#This script renames a selected locator to "DOF", creates a CamLocator parented to the Camera, and connects the DOF locator to the CamLocator with a distanceBetween node, linking the distance to rsBokeh1.dofFocusDistance.

import maya.cmds as cmds

# Function to rename the selected locator to DOF
def rename_selected_locator():
    # Get the selected objects
    selected = cmds.ls(selection=True)
    
    if not selected or len(selected) != 1:
        cmds.warning("Please select one locator.")
        return

    locator = selected[0]

    # Check if the selected object has a shape node of type 'locator'
    shapes = cmds.listRelatives(locator, shapes=True)
    if not shapes or not cmds.objectType(shapes[0], isType="locator"):
        cmds.warning("Selected object is not a locator.")
        return

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
        cmds.parent(cam_locator, "Camera")
        cmds.xform(cam_locator, translation=(0, 0, 0), worldSpace=False)
        print("Created and parented CamLocator under Camera.")
    else:
        cam_locator = "CamLocator"

    return cam_locator

# Function to connect DOF locator to the CamLocator with a distanceBetween node and link to rsBokeh1.dofFocusDistance
def connect_dof_to_cam_locator():
    # Ensure DOF locator exists
    if not cmds.objExists("DOF"):
        cmds.warning("DOF locator does not exist. Please rename a locator to DOF first.")
        return

    # Create CamLocator
    cam_locator = create_cam_locator()
    if not cam_locator:
        return

    # Create a distanceBetween node
    distance_node = cmds.createNode("distanceBetween", name="DOF_distanceBetween")

    # Connect DOF locator to the distanceBetween node
    cmds.connectAttr("DOF.worldPosition[0]", f"{distance_node}.point1")

    # Connect the CamLocator to the distanceBetween node
    cmds.connectAttr(f"{cam_locator}.worldPosition[0]", f"{distance_node}.point2")

    # Connect the distance output to rsBokeh1.dofFocusDistance
    if not cmds.objExists("rsBokeh1"):
        rsBokeh1 = cmds.createNode("RedshiftBokeh", name="rsBokeh1")
        cmds.setAttr("rsBokeh1.dofDeriveFocusDistanceFromCamera", 0)
        # Get the camera shape node
        cameraShape = cmds.listRelatives("Camera", shapes=True)[0]
        # Connect rsBokeh1 to camera's lens shader
        cmds.connectAttr("rsBokeh1.message", f"{cameraShape}.rsLensShader", force=True)
        print("Created rsBokeh1 node and connected to camera lens shader.")
    else:
        rsBokeh1 = "rsBokeh1"

    cmds.connectAttr(f"{distance_node}.distance", f"{rsBokeh1}.dofFocusDistance", force=True)
    print(f"Connected DOF locator and linked distance to {rsBokeh1}.dofFocusDistance.")

# Run the functions
locator_name = rename_selected_locator()
if locator_name == "DOF":
    connect_dof_to_cam_locator()
