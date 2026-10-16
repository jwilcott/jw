"""Run in Maya to exclusively light-link the selected lights and geometry."""

import maya.cmds as cmds


def link_selected_exclusively():
    """Isolate selected lights/objects, including light and shadow links.

    Selecting a transform or group includes its descendant shapes. Links
    between unselected lights and unselected objects are left untouched.
    """
    selection = cmds.ls(selection=True, long=True, objectsOnly=True) or []
    selected_shapes = set()
    for node in selection:
        selected_shapes.add(node)
        selected_shapes.update(
            cmds.listRelatives(node, allDescendents=True, fullPath=True) or []
        )

    # Classification also includes renderer plug-in light types.
    all_lights = set(cmds.ls(lights=True, long=True) or [])
    for light_type in cmds.listNodeTypes("light") or []:
        all_lights.update(cmds.ls(type=light_type, long=True) or [])
    all_objects = set(cmds.ls(geometry=True, long=True, noIntermediate=True) or [])
    all_objects.difference_update(all_lights)
    lights = sorted(selected_shapes & all_lights)
    objects = sorted(selected_shapes & all_objects)

    if not lights or not objects:
        cmds.warning("Select at least one light and one geometry object. No links changed.")
        return

    other_lights = sorted(all_lights - set(lights))
    other_objects = sorted(all_objects - set(objects))
    cmds.undoInfo(openChunk=True, chunkName="Exclusive Light Links")
    try:
        for shadow in (False, True):
            if other_objects:
                cmds.lightlink(b=True, light=lights, object=other_objects, shadow=shadow)
            if other_lights:
                cmds.lightlink(b=True, light=other_lights, object=objects, shadow=shadow)
            cmds.lightlink(make=True, light=lights, object=objects, shadow=shadow)
    finally:
        cmds.undoInfo(closeChunk=True)

    print("Exclusively linked {} light(s) to {} object(s).".format(len(lights), len(objects)))


if __name__ == "__main__":
    link_selected_exclusively()
