import maya.cmds as cmds
import os

def connect_base_color():
    """
    Prompts the user for a texture file and connects it to the
    'color' attribute of the selected shader node.
    """
    selection = cmds.ls(selection=True, type='shadingDependNode')

    if not selection:
        cmds.warning("Please select a shader node.")
        return

    if len(selection) > 1:
        cmds.warning("Please select only one shader node.")
        return

    shader_node = selection[0]

    # Check if the selected node has a 'color' attribute (common for diffuse)
    if not cmds.attributeQuery('color', node=shader_node, exists=True):
         # Arnold aiStandardSurface uses 'baseColor'
        if cmds.attributeQuery('baseColor', node=shader_node, exists=True):
             target_attr = 'baseColor'
        else:
            cmds.warning(f"Selected node '{shader_node}' does not have a standard 'color' or 'baseColor' attribute.")
            return
    else:
        target_attr = 'color'


    # Prompt for file selection
    file_filter = "Image Files (*.png *.jpg *.jpeg *.tif *.tiff *.exr *.tga);;All Files (*.*)"
    file_path_list = cmds.fileDialog2(fileFilter=file_filter, dialogStyle=2, fileMode=1, caption="Select Base Color Texture")

    if not file_path_list:
        print("No file selected.")
        return

    file_path = file_path_list[0]

    # Create file texture node
    file_node = cmds.shadingNode('file', asTexture=True, isColorManaged=True, name=f"{os.path.basename(file_path).split('.')[0]}_file")
    place_util = cmds.shadingNode('place2dTexture', asUtility=True, name=f"{file_node}_place2dTexture")

    # Connect place2dTexture to file node
    attrs_to_connect = [
        'coverage', 'translateFrame', 'rotateFrame', 'mirrorU', 'mirrorV',
        'stagger', 'wrapU', 'wrapV', 'repeatUV', 'offset',
        'rotateUV', 'noiseUV', 'vertexUvOne', 'vertexUvTwo',
        'vertexUvThree', 'vertexCameraOne'
    ]
    for attr in attrs_to_connect:
        cmds.connectAttr(f'{place_util}.{attr}', f'{file_node}.{attr}', force=True)
    cmds.connectAttr(f'{place_util}.outUV', f'{file_node}.uvCoord', force=True)
    cmds.connectAttr(f'{place_util}.outUvFilterSize', f'{file_node}.uvFilterSize', force=True)


    # Set file path
    cmds.setAttr(file_node + '.fileTextureName', file_path, type='string')

    # Connect file node to shader
    try:
        cmds.connectAttr(f'{file_node}.outColor', f'{shader_node}.{target_attr}', force=True)
        print(f"Connected '{file_path}' to '{shader_node}.{target_attr}'.")
    except Exception as e:
        cmds.warning(f"Could not connect {file_node}.outColor to {shader_node}.{target_attr}: {e}")
        # Clean up created nodes if connection fails
        cmds.delete(file_node)
        cmds.delete(place_util)


# Run the function
connect_base_color()
