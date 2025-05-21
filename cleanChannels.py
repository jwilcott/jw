import maya.cmds as cmds

selected = cmds.ls(selection=True)
if selected:
    animCurves = cmds.listConnections(selected, type="animCurve", connections=False) or []
    for curve in animCurves:
        values = cmds.keyframe(curve, query=True, valueChange=True)
        if values and all(v == values[0] for v in values):
            cmds.delete(curve)
else:
    cmds.warning("Nothing is selected.")
