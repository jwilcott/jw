# Adjust displacement attributes on the displacement node
#
# Usage: select one or more geometry transforms and run this script.
# The script finds any shadingEngine(s) attached to the shapes, then
# queries the displacement shader plugged into the shadingEngine's
# displacementShader attribute. If a displacement node is found it will
# adjust the following attributes:
#
#   newRangeMin -> -0.05
#   newRangeMax -> 0.5
#   scale        -> 0.1
#
# (If the attributes exist on the node.)

import maya.cmds as cmds


def adjust_displacement_on_selection():
    """Finds displacement nodes for the current selection and updates
    their range/scale attributes."""

    transforms = cmds.ls(selection=True, long=True, type='transform')
    if not transforms:
        cmds.warning("Please select at least one geometry transform.")
        return

    updated_nodes = []

    for tr in transforms:
        shapes = cmds.listRelatives(tr, shapes=True, fullPath=True) or []
        for shape in shapes:
            # shading engines connected to the shape
            sgs = cmds.listConnections(shape, type='shadingEngine') or []
            for sg in sgs:
                # look for a displacement shader plugged into the shadingEngine
                disp_nodes = cmds.listConnections(sg + ".displacementShader",
                                                  source=True, destination=False) or []
                for disp in disp_nodes:
                    # set attributes if they exist
                    if cmds.objExists(disp + ".newrange_min"):
                        cmds.setAttr(disp + ".newrange_min", -0.5)
                    if cmds.objExists(disp + ".newrange_max"):
                        cmds.setAttr(disp + ".newrange_max", 0.5)
                    if cmds.objExists(disp + ".scale"):
                        cmds.setAttr(disp + ".scale", 0.1)

                    updated_nodes.append(disp)

    if updated_nodes:
        cmds.inViewMessage(amg="<hl>Updated displacement node(s): %s</hl>" %
                           ", ".join(updated_nodes), pos='topCenter', fade=True)
        # select the displacement nodes in Maya
        try:
            cmds.select(updated_nodes, replace=True)
        except Exception:
            # if for some reason selection fails, ignore
            pass
    else:
        cmds.warning("No displacement nodes found on the selected geometry.")


# run when script is executed directly
if __name__ == '__main__':
    adjust_displacement_on_selection()
