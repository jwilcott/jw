#RobloxClean
#Mat-RS
#Combine Parts (legs, arms)
#Face Separate (eyes, tongue, teeth, brows)
#Make Skin MTL
#Open Mouth
#Send For Remesh

import maya.cmds as cmds

def process_scene():
    # Group all top-level mesh transforms in the outliner
    mesh_transforms = []
    for obj in cmds.ls(assemblies=True, long=False):
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True) or []
        if shapes:
            mesh_transforms.append(obj)
    if not mesh_transforms:
        cmds.warning("No mesh objects found to group.")
        return
    group_name = "geo"
    group = cmds.group(mesh_transforms, name=group_name)

    # Center pivot at bottom of bounding box
    bbox = cmds.exactWorldBoundingBox(group)
    pivot = [(bbox[0]+bbox[3])/2, bbox[1], (bbox[2]+bbox[5])/2]
    cmds.xform(group, piv=pivot, ws=True)

    # Move group so bottom of bounding box is at 0,0,0
    cmds.xform(group, ws=True, t=[0,0,0])  # Reset translation first (optional, for consistency)
    bbox = cmds.exactWorldBoundingBox(group)
    offset = [-((bbox[0]+bbox[3])/2), -bbox[1], -((bbox[2]+bbox[5])/2)]
    cmds.xform(group, r=True, t=offset)

    # Rotate group 180 in Y
    cmds.xform(group, ws=True, rotation=[0,180,0])

    # Scale group up by 6
    cmds.xform(group, ws=True, scale=[6,6,6])

    # PolyMergeVert .001 for each object in group
    children = cmds.listRelatives(group, children=True, type='transform', fullPath=True) or []
    for obj in children:
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True) or []
        if shapes:
            cmds.select(obj)
            try:
                cmds.polyMergeVertex(d=0.001)
            except Exception:
                cmds.warning(f"Could not merge vertices for {obj}")

    # Quadulate each object, uncheck keep hard edges
    for obj in children:
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True) or []
        if shapes:
            cmds.select(obj, r=True)
            try:
                cmds.polyQuad(obj, khe=0)
            except Exception as e:
                cmds.warning(f"Could not polyQuad {obj}: {e}")

    # Center the pivot for each object in the group
    for obj in children:
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True) or []
        if shapes:
            try:
                cmds.xform(obj, centerPivots=True)
            except Exception as e:
                cmds.warning(f"Could not center pivot for {obj}: {e}")

    # Re-query children after namespaces have been removed
    children = cmds.listRelatives(group, children=True, type='transform', fullPath=True) or []

    # Set all file node color spaces to 'sRGB'
    file_nodes = cmds.ls(type='file')
    for node in file_nodes:
        try:
            if cmds.attributeQuery('colorSpace', node=node, exists=True):
                cmds.setAttr(f"{node}.colorSpace", 'sRGB', type='string')
        except Exception as e:
            cmds.warning(f"Could not set colorSpace for {node}: {e}")

    # Delete history for each object in the group
    for obj in children:
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

    cmds.select(clear=True)

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