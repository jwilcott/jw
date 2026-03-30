#RobloxClean
#Mat-RS
#Combine Parts (legs, arms)
#Face Separate (eyes, tongue, teeth, brows)
#Make Skin MTL
#Open Mouth
#Send For Remesh

import maya.cmds as cmds

TARGET_HEIGHT = 20.0

def bottom_pivot_from_bbox(bbox):
    return [(bbox[0] + bbox[3]) / 2, bbox[1], (bbox[2] + bbox[5]) / 2]

def get_active_model_panel():
    current_panel = cmds.getPanel(withFocus=True)
    if current_panel and cmds.getPanel(typeOf=current_panel) == "modelPanel":
        return current_panel

    for panel in cmds.getPanel(type="modelPanel") or []:
        try:
            if cmds.modelPanel(panel, query=True, visible=True):
                return panel
        except Exception:
            pass

    return None

def enable_viewport_options():
    panel = get_active_model_panel()
    if not panel:
        cmds.warning("Could not find an active or visible model panel to update viewport settings.")
        return

    try:
        cmds.modelEditor(
            panel,
            edit=True,
            displayAppearance="smoothShaded",
            displayTextures=True,
            joints=True,
            jointXray=True,
        )
    except Exception as e:
        cmds.warning(f"Could not update viewport display options for {panel}: {e}")

    for attr in ("multiSampleEnable", "ssaoEnable"):
        try:
            if cmds.attributeQuery(attr, node="hardwareRenderingGlobals", exists=True):
                cmds.setAttr(f"hardwareRenderingGlobals.{attr}", 1)
        except Exception as e:
            cmds.warning(f"Could not enable {attr} on hardwareRenderingGlobals: {e}")

def process_scene():
    # Collect all top-level mesh transforms in the outliner
    mesh_transforms = []
    for obj in cmds.ls(assemblies=True, long=False):
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True) or []
        if shapes:
            mesh_transforms.append(obj)
    if not mesh_transforms:
        cmds.warning("No mesh objects found to process.")
        return

    # Use the combined bounding box of all top-level meshes
    bbox = cmds.exactWorldBoundingBox(*mesh_transforms)
    pivot = bottom_pivot_from_bbox(bbox)
    for obj in mesh_transforms:
        cmds.xform(obj, ws=True, piv=pivot)

    # Move the combined meshes so the bottom of the bounding box is at 0,0,0
    offset = [-pivot[0], -pivot[1], -pivot[2]]
    for obj in mesh_transforms:
        cmds.xform(obj, r=True, t=offset)

    # Rotate the combined meshes 180 in Y around the shared bottom pivot
    for obj in mesh_transforms:
        cmds.xform(obj, relative=True, rotation=[0, 180, 0])

    # Scale the combined meshes uniformly so the bounding box is TARGET_HEIGHT units tall
    bbox = cmds.exactWorldBoundingBox(*mesh_transforms)
    current_height = bbox[4] - bbox[1]
    if current_height <= 0:
        cmds.warning("Could not scale meshes: bounding box height is zero.")
    else:
        scale_factor = TARGET_HEIGHT / current_height
        for obj in mesh_transforms:
            cmds.xform(obj, relative=True, scale=[scale_factor, scale_factor, scale_factor])

    # PolyMergeVert .001 for each mesh transform
    for obj in mesh_transforms:
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True) or []
        if shapes:
            cmds.select(obj)
            try:
                cmds.polyMergeVertex(d=0.001)
            except Exception:
                cmds.warning(f"Could not merge vertices for {obj}")

    # Quadulate each object, uncheck keep hard edges
    for obj in mesh_transforms:
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True) or []
        if shapes:
            cmds.select(obj, r=True)
            try:
                cmds.polyQuad(obj, khe=0)
            except Exception as e:
                cmds.warning(f"Could not polyQuad {obj}: {e}")

    # Set each object pivot to the bottom of its own bounding box
    for obj in mesh_transforms:
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True) or []
        if shapes:
            try:
                obj_bbox = cmds.exactWorldBoundingBox(obj)
                cmds.xform(obj, ws=True, piv=bottom_pivot_from_bbox(obj_bbox))
            except Exception as e:
                cmds.warning(f"Could not set bottom pivot for {obj}: {e}")

    # Set all file node color spaces to 'sRGB'
    file_nodes = cmds.ls(type='file')
    for node in file_nodes:
        try:
            if cmds.attributeQuery('colorSpace', node=node, exists=True):
                cmds.setAttr(f"{node}.colorSpace", 'sRGB', type='string')
        except Exception as e:
            cmds.warning(f"Could not set colorSpace for {node}: {e}")

    # Delete history for each object
    for obj in mesh_transforms:
        # Double-check object exists before operating, to avoid errors from missing nodes
        if not cmds.objExists(obj):
            cmds.warning(f"Object {obj} does not exist, skipping history delete.")
            continue
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True) or []
        if shapes:
            try:
                cmds.delete(obj, constructionHistory=True)
            except Exception as e:
                cmds.warning(f"Could not delete history for {obj}: {e}")

    # Freeze transforms at the end and keep pivots at the bottom of each mesh
    for obj in mesh_transforms:
        if not cmds.objExists(obj):
            continue
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True) or []
        if shapes:
            try:
                cmds.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True)
                obj_bbox = cmds.exactWorldBoundingBox(obj)
                cmds.xform(obj, ws=True, piv=bottom_pivot_from_bbox(obj_bbox))
            except Exception as e:
                cmds.warning(f"Could not freeze transforms for {obj}: {e}")

    cmds.select(clear=True)
    enable_viewport_options()

    print("""Scene processing complete! Next Steps:
    Mat-RS
    Combine Parts (legs, arms)
    Face Separate (eyes, tongue, teeth, brows)
    Make Skin MTL
    Open Mouth
    Send For Remesh""")



# Wrap the whole process in a single undo chunk
def main():
    cmds.undoInfo(openChunk=True)
    try:
        process_scene()
    finally:
        cmds.undoInfo(closeChunk=True)

main()
