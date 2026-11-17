import math
import maya.cmds as cmds
import maya.mel as mel

def bake_walk_legs():
    if mel.eval('whatIs "asSwitchFKIK"') == 'Unknown':
        cmds.warning('Open the AdvancedSkeleton biped Selector, then click this button again.')
        return
    pairs = []
    for left in cmds.ls('FKIKLeg_L', '*:FKIKLeg_L', recursive=True, type='transform') or []:
        prefix = left[:-len('FKIKLeg_L')]
        if cmds.objExists(prefix + 'FKIKLeg_R'):
            pairs.append(prefix)
    pairs = sorted(set(pairs))
    selected = cmds.ls(sl=True, objectsOnly=True) or []
    matching = [p for p in pairs if any((n.rsplit('|', 1)[-1].rpartition(':')[0] + ':') == (p or ':') for n in selected)]
    if len(matching) == 1:
        prefix = matching[0]
    elif len(pairs) == 1:
        prefix = pairs[0]
    else:
        cmds.warning('Select a control on the AdvancedSkeleton biped you want to bake.')
        return

    slider = mel.eval('$tmp = $gPlayBackSlider')
    start, stop = cmds.timeControl(slider, q=True, rangeArray=True)
    if stop - start <= 1:
        start = math.ceil(cmds.playbackOptions(q=True, min=True))
        end = math.floor(cmds.playbackOptions(q=True, max=True))
    else:
        start, end = math.ceil(start), math.ceil(stop) - 1
    if end <= start:
        cmds.warning('Choose a range containing at least two frames.')
        return

    sides = []
    for side in ('_L', '_R'):
        plug = prefix + 'FKIKLeg' + side + '.FKIKBlend'
        values = {cmds.getAttr(plug, time=f) for f in range(start, end + 1)}
        if values == {0.0}:
            sides.append(side)
        elif values != {10.0}:
            cmds.warning('A leg mixes FK and IK in this range. Choose a range where its blend stays in FK.')
            return
    if not sides:
        cmds.warning('Both legs are already in IK throughout this range.')
        return

    time = cmds.currentTime(q=True)
    auto_key = cmds.autoKeyframe(q=True, state=True)
    prior_namespace = mel.eval('global string $gAsPanelNamespace; $gAsPanelNamespace;')
    def set_panel_namespace(value):
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        mel.eval('global string $gAsPanelNamespace; $gAsPanelNamespace = "' + escaped + '";')

    cmds.undoInfo(openChunk=True, chunkName='Bake walk legs to IK')
    try:
        set_panel_namespace(prefix)
        for side in sides:
            cmds.playbackOptions(selectionStartTime=start, selectionEndTime=end, selectionVisible=True)
            if cmds.timeControl(slider, q=True, rangeArray=True) != [start, end + 1]:
                raise RuntimeError('Maya did not apply the requested Time Slider range.')
            mel.eval('asSwitchFKIK "asPanel" "Leg" "' + side + '" "FK2IK";')
    finally:
        set_panel_namespace(prior_namespace)
        cmds.autoKeyframe(state=auto_key)
        cmds.currentTime(time)
        cmds.undoInfo(closeChunk=True)
    print('Baked leg IK on frames {}–{}.'.format(start, end))

bake_walk_legs()
