"""Skip Maya's save confirmation for unnamed scenes with only default nodes.

Default camera movement and render-setting changes alone count as blank.
Named scenes, custom nodes, references and animation retain the normal prompt.
"""
from pathlib import Path
import re

from maya import cmds, mel


def is_blank_scene():
    """Fail closed: uncertainty must retain Maya's normal save dialog."""
    try:
        if cmds.file(query=True, sceneName=True):
            return False
        if cmds.file(query=True, reference=True):
            return False
        allowed = set(cmds.ls(defaultNodes=True, long=True) or [])
        # Maya omits these standard scene infrastructure nodes from defaultNodes.
        infrastructure = {
            'defaultLayer': 'displayLayer',
            'defaultRenderLayer': 'renderLayer',
            'layerManager': 'displayLayerManager',
            'renderLayerManager': 'renderLayerManager',
            'lightLinker1': 'lightLinker',
            'shapeEditorManager': 'shapeEditorManager',
            'poseInterpolatorManager': 'poseInterpolatorManager',
            'hikSolver': 'hikSolver',
            'ikRPsolver': 'ikRPsolver',
            'ikSCsolver': 'ikSCsolver',
            'ikSplineSolver': 'ikSplineSolver',
        }
        for node, node_type in infrastructure.items():
            if cmds.objExists(node) and cmds.nodeType(node) == node_type:
                allowed.update(cmds.ls(node, long=True) or [])
        for name in ('persp', 'top', 'front', 'side'):
            transform = '|' + name
            shape = transform + '|' + name + 'Shape'
            if (cmds.objExists(shape)
                    and cmds.nodeType(shape) == 'camera'
                    and cmds.camera(shape, query=True, startupCamera=True)):
                allowed.update((transform, shape))
        return not (set(cmds.ls(dependencyNodes=True, long=True) or []) - allowed)
    except Exception:
        return False


def install():
    """Wrap this Maya version's stock routine without modifying Autodesk files."""
    if cmds.about(batch=True):
        return
    if not mel.eval('exists "jwOriginalSaveChanges"'):
        location = mel.eval('whatIs "saveChanges"')
        prefix = 'Mel procedure found in: '
        if not location.startswith(prefix):
            raise RuntimeError('Cannot locate Maya saveChanges.mel: ' + location)
        source = Path(location[len(prefix):]).read_text(encoding='utf-8')
        source, count = re.subn(
            r'global\s+proc\s+int\s+saveChanges\s*\(',
            'global proc int jwOriginalSaveChanges (', source, count=1)
        if count != 1:
            raise RuntimeError('Unexpected Maya saveChanges procedure signature')
        mel.eval(source)
    mel.eval('''
global proc int saveChanges(string $action) {
    if (`python("__import__('jw.blankSceneSaveGuard', fromlist=['is_blank_scene']).is_blank_scene()")`) {
        if ($action != "") evalEcho($action);
        return 1;
    }
    return jwOriginalSaveChanges($action);
}
''')
