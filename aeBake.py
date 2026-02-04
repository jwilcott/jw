# Bakes "Camera" and all locators with "AE" in the name
# Best to use built in maya Rivit command for locators on verticies
# Also sets "Camera" as non-renderable
# adds "_null" to locators and exports the group as .ma file to the render directory
# REMEMBER to check if focal length is correct in in AE after importing

import maya.cmds as cmds
import os

def bake_object(obj_name):
    # Determine name based on object type
    if obj_name == 'Camera':
        new_name = f'Baked_{obj_name}'
    else:
        new_name = f'{obj_name}_null'
        
    # Duplicate and unparent
    baked_obj = cmds.duplicate(obj_name, name=new_name)[0]
    cmds.parent(baked_obj, world=True)
    
    # Create parent constraint
    constraint = cmds.parentConstraint(obj_name, baked_obj, maintainOffset=False)[0]
    
    # Bake animation
    start_time = cmds.playbackOptions(query=True, minTime=True)
    end_time = cmds.playbackOptions(query=True, maxTime=True)
    cmds.bakeResults(baked_obj, 
                    simulation=False,
                    time=(start_time, end_time),
                    sampleBy=1,
                    disableImplicitControl=True,
                    preserveOutsideKeys=True,
                    sparseAnimCurveBake=False,
                    removeBakedAttributeFromLayer=False,
                    removeBakedAnimFromLayer=False,
                    bakeOnOverrideLayer=False,
                    minimizeRotation=True,
                    controlPoints=False)
    
    # Delete constraint
    cmds.delete(constraint)
    
    # Set camera as non-renderable if it's the baked camera
    if obj_name == 'Camera':
        cmds.setAttr(f"{baked_obj}.renderable", 0)
    
    return baked_obj

# Get all locators with "AE" in the name
locators = cmds.ls("*AE*", type="locator")
locator_transforms = [cmds.listRelatives(loc, parent=True)[0] for loc in locators]

# List of objects to process
objects_to_bake = ['Camera'] + locator_transforms

# Process all objects
baked_objects = [bake_object(obj) for obj in objects_to_bake]

# Create group and parent all baked objects
export_group = cmds.group(empty=True, name='AE Export')
for obj in baked_objects:
    cmds.parent(obj, export_group)

def construct_render_path():
    workspace_dir = cmds.workspace(q=True, rd=True)
    images_dir = cmds.workspace(fileRuleEntry="images")
    render_directory = os.path.join(workspace_dir, images_dir)
    prefix = cmds.getAttr("defaultRenderGlobals.imageFilePrefix")
    scene_name = os.path.splitext(os.path.basename(cmds.file(q=True, sn=True)))[0]
    if "<scene>" in prefix:
        prefix = prefix.replace("<scene>", scene_name)
    return os.path.dirname(os.path.join(render_directory, prefix))

# Get render directory using the construct_render_path function
directory = construct_render_path()
try:
    if not os.path.exists(directory):
        os.makedirs(directory)
except (OSError, PermissionError) as e:
    cmds.warning(f"Unable to create directory: {directory}")
    directory = cmds.workspace(q=True, rd=True)
    cmds.warning(f"Falling back to project directory: {directory}")

# Export the group as .ma file
export_file = os.path.join(directory, 'AE_Export.ma')
try:
    cmds.select(export_group)
    cmds.file(export_file, 
             force=True, 
             options='v=0', 
             type='mayaAscii', 
             exportSelected=True)
    cmds.warning(f"Successfully exported to: {export_file}")
except Exception as e:
    cmds.warning(f"Failed to export: {str(e)}")
