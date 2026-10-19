#Be sure to first click on Bokeh checkbox to properly connect it to the camera.
#This script renames a selected locator to "DOF", creates a CamLocator parented to the Camera, and links their distance to all RedshiftBokeh nodes and rsCameraEffects1.dofFocusDistance.

import maya.cmds as cmds

def locator_shape(node):
    """Resolve a locator shape using its full DAG path."""
    if cmds.nodeType(node) == "locator":
        return node
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True, type="locator") or []
    return shapes[0] if shapes else None

# Function to rename the selected locator to DOF
def rename_selected_locator():
    # Get the selected objects
    selected = cmds.ls(selection=True, long=True)
    
    if not selected or len(selected) != 1:
        cmds.warning("Please select one locator.")
        return

    locator = selected[0]

    # Check if the selected object has a shape node of type 'locator'
    if not locator_shape(locator):
        cmds.warning("Selected object is not a locator.")
        return

    if cmds.nodeType(locator) == "locator":
        locator = cmds.listRelatives(locator, parent=True, fullPath=True)[0]

    # Rename the locator to DOF
    new_name = cmds.rename(locator, "DOF")
    print(f"Renamed locator to {new_name}")
    return new_name

# Function to create a CamLocator and parent it to the Camera
def create_cam_locator():
    # Ensure the camera named "Camera" exists
    if not cmds.objExists("Camera"):
        cmds.warning("Camera named 'Camera' does not exist in the scene.")
        return None

    # Create a CamLocator if it doesn't already exist
    if not cmds.objExists("CamLocator"):
        cam_locator = cmds.spaceLocator(name="CamLocator")[0]
        cam_locator = cmds.parent(cam_locator, "Camera")[0]
        cmds.xform(cam_locator, translation=(0, 0, 0), worldSpace=False)
        print("Created and parented CamLocator under Camera.")
    else:
        cam_locator = "CamLocator"

    return cam_locator

# Function to connect DOF locator to the CamLocator with a distanceBetween node and link to all RedshiftBokeh nodes' dofFocusDistance
def connect_dof_to_cam_locator(dof_locator="DOF"):
    # Ensure DOF locator exists
    if not cmds.objExists(dof_locator):
        cmds.warning("DOF locator does not exist. Please rename a locator to DOF first.")
        return

    # Create CamLocator
    cam_locator = create_cam_locator()
    if not cam_locator:
        return

    # Resolve shapes after renaming/parenting, which can change their DAG paths.
    dof_shape = locator_shape(dof_locator)
    cam_shape = locator_shape(cam_locator)
    if not dof_shape or not cam_shape:
        cmds.warning("DOF and CamLocator must both contain locator shapes.")
        return

    # Create a distanceBetween node
    distance_node = cmds.createNode("distanceBetween", name="DOF_distanceBetween")

    # Connect DOF locator to the distanceBetween node
    cmds.connectAttr(f"{dof_shape}.worldPosition[0]", f"{distance_node}.point1")

    # Connect the CamLocator to the distanceBetween node
    cmds.connectAttr(f"{cam_shape}.worldPosition[0]", f"{distance_node}.point2")

    # Find all RedshiftBokeh nodes in the scene
    bokeh_nodes = cmds.ls(type="RedshiftBokeh")

    # Connect the distance output to each RedshiftBokeh node's dofFocusDistance
    for bokeh_node in bokeh_nodes:
        cmds.setAttr(f"{bokeh_node}.dofDeriveFocusDistanceFromCamera", 0)
        cmds.connectAttr(f"{distance_node}.distance", f"{bokeh_node}.dofFocusDistance", force=True)
        print(f"Connected distance to {bokeh_node}.dofFocusDistance.")

    # Also support the Redshift camera effects focus distance, independently of Bokeh nodes.
    camera_effects_focus = "rsCameraEffects1.dofFocusDistance"
    if cmds.objExists(camera_effects_focus):
        cmds.connectAttr(f"{distance_node}.distance", camera_effects_focus, force=True)
        print(f"Connected distance to {camera_effects_focus}.")
    else:
        cmds.warning(f"{camera_effects_focus} does not exist in the scene.")

    print("Connected DOF locator and linked focus distance.")

# Run the functions
locator_name = rename_selected_locator()
if locator_name:
    connect_dof_to_cam_locator(locator_name)
