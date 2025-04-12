#Phong to Redshift Material with preserving color texture input
#Select one or multiple objects and run the script to convert Phong to Redshift Material
#The script will create a new Redshift material if it doesn't exist and connect the color texture to the diffuse color input
#The script will also set the Reflection Roughness to 0.5 for the Redshift material

import maya.cmds as cmds

def assign_redshift_shader():
    # Get the selected objects
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.warning("No object selected. Please select an object.")
        return

    for obj in selection:
        print(f"Processing object: {obj}")
        # Generate shader and shading group names based on object name
        shader_name = f"{obj}_MTL"
        shading_group_name = f"{shader_name}SG"

        # Create a new Redshift material if it doesn't exist
        if not cmds.objExists(shader_name):
            shader = cmds.shadingNode("RedshiftMaterial", asShader=True, name=shader_name)
            cmds.setAttr(f"{shader}.refl_roughness", 0.5)
            print(f"Created new Redshift shader: {shader}")
        else:
            shader = shader_name
            print(f"Using existing Redshift shader: {shader}")

        # Get the shape node (shading is applied to shapes, not transforms)
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
        if not shapes:
            print(f"No shape node found for {obj}")
            continue

        print(f"Shape node found: {shapes}")

        # Find the shading group assigned to the shape
        shading_groups = cmds.listConnections(shapes, type='shadingEngine') or []
        if not shading_groups:
            print(f"No shading group found for {obj}")
            continue

        shading_group = shading_groups[0]
        print(f"Shading group found: {shading_group}")

        # Get the Phong shader from the shading group's surfaceShader connection
        phong_shader = cmds.listConnections(f"{shading_group}.surfaceShader", source=True, destination=False)
        if not phong_shader or cmds.nodeType(phong_shader[0]) != "phong":
            print(f"No Phong shader found in {shading_group}")
            continue

        phong_shader = phong_shader[0]
        print(f"Phong shader detected: {phong_shader}")

        # Find texture connected to the Phong shader's color
        file_texture = cmds.listConnections(f"{phong_shader}.color", source=True, destination=False, plugs=True) or []
        print(f"File texture connections: {file_texture}")

        if file_texture:
            texture_node = file_texture[0].split('.')[0]  # Get just the node name
            print(f"Texture node identified: {texture_node}")

            # Ensure it is a file texture before connecting
            if cmds.nodeType(texture_node) == "file":
                cmds.connectAttr(f"{texture_node}.outColor", f"{shader}.diffuse_color", force=True)
                print(f"Connected {texture_node}.outColor to {shader}.diffuse_color")
            else:
                print(f"Texture node {texture_node} is not a file node.")
        else:
            # If no texture is connected, get and transfer the color value from the Phong shader
            phong_color = cmds.getAttr(f"{phong_shader}.color")[0]
            cmds.setAttr(f"{shader}.diffuse_color", *phong_color, type="double3")
            print(f"Transferred color value {phong_color} from {phong_shader} to {shader}.diffuse_color")

        # Find bump node connected to the Phong shader's normalCamera attribute
        bump_node = cmds.listConnections(f"{phong_shader}.normalCamera", source=True, destination=False, plugs=True) or []
        print(f"Bump node connections: {bump_node}")

        if bump_node:
            bump_node_name = bump_node[0].split('.')[0]  # Get just the node name
            print(f"Bump node identified: {bump_node_name}")

            # Ensure it is a bump node before connecting
            if cmds.nodeType(bump_node_name) == "bump2d":
                cmds.connectAttr(f"{bump_node_name}.outNormal", f"{shader}.bump_input", force=True)
                print(f"Connected {bump_node_name}.outNormal to {shader}.bump_input")
            else:
                print(f"Bump node {bump_node_name} is not a bump2d node.")
        else:
            print(f"No bump node connected to {phong_shader}.normalCamera")

        # Create a shading group if it doesn't exist
        if not cmds.objExists(shading_group_name):
            shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group_name)
            print(f"Created new shading group: {shading_group}")
        else:
            shading_group = shading_group_name
            print(f"Using existing shading group: {shading_group}")

        # Connect shader to shading group
        cmds.connectAttr(f"{shader}.outColor", f"{shading_group}.surfaceShader", force=True)
        print(f"Connected {shader}.outColor to {shading_group}.surfaceShader")

        # Assign shader to the selected object
        cmds.sets(obj, edit=True, forceElement=shading_group)
        print(f"Assigned {shader_name} to {obj} with Reflection Roughness set to 0.5")

assign_redshift_shader()
