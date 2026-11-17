import maya.cmds as cmds

def move_bbox_center_to_origin():
    sel = cmds.ls(selection=True, long=True)
    if not sel:
        cmds.warning("No objects selected.")
        return
    
    for obj in sel:
        # Get bounding box of the object
        bbox = cmds.exactWorldBoundingBox(obj)
        center = [
            (bbox[0] + bbox[3]) / 2.0,  # x center
            (bbox[1] + bbox[4]) / 2.0,  # y center
            (bbox[2] + bbox[5]) / 2.0   # z center
        ]
        
        # Calculate offset to bring bbox center to 0,0,0
        offset = [-center[0], -center[1], -center[2]]
        
        # Move object by that offset
        cmds.move(offset[0], offset[1], offset[2], obj, relative=True, worldSpace=True)
        
        # Center the pivot
        cmds.xform(obj, centerPivots=True)
        
        # Freeze transforms (translation, rotation, scale)
        cmds.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True, normal=False)
    
    print("Moved to origin, centered pivot, and froze transforms.")

# Run it
move_bbox_center_to_origin()
