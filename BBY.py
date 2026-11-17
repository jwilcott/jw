import maya.cmds as cmds

def pivot_to_bottom():
    selection = cmds.ls(selection=True, transforms=True)
    if not selection:
        cmds.warning("No objects selected.")
        return

    for obj in selection:
        bbox = cmds.exactWorldBoundingBox(obj)
        center_x = (bbox[0] + bbox[3]) / 2.0
        center_z = (bbox[2] + bbox[5]) / 2.0
        bottom_y = bbox[1]

        cmds.xform(obj + ".scalePivot", ws=True, absolute=True, t=(center_x, bottom_y, center_z))
        cmds.xform(obj + ".rotatePivot", ws=True, absolute=True, t=(center_x, bottom_y, center_z))

pivot_to_bottom()
