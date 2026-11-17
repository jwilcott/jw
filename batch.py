import maya.cmds as cmds

cmds.BatchRender()

width = 960 // 2
height = 540 // 2
window_name = "renderViewWindow"

if cmds.window(window_name, exists=True):
    cmds.window(window_name, edit=True, widthHeight=(width, height))
    print("Render View size set to {}x{}.".format(width, height))

for panel in cmds.getPanel(scriptType="renderWindowPanel") or []:
    if cmds.renderWindowEditor(panel, exists=True):
        cmds.renderWindowEditor(panel, edit=True, refresh=True)
