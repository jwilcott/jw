#This script is designed to convert any Phong, Blinn, or Arnold Standard Surface material to a Redshift material in Autodesk Maya
#Select one or multiple objects and run the script to convert Phong to Redshift Material
#The script will create a new Redshift material if it doesn't exist and connect the color texture to the diffuse color input
#The script will also set the Reflection Roughness to 0.5 for the Redshift material

import pymel.core as pm

def assign_redshift_shader():
    # Get the selected objects
    selection = pm.selected()
    if not selection:
        pm.warning("No object selected. Please select an object.")
        return

    for obj in selection:
        print(f"Processing object: {obj}")
        # Generate shader and shading group names based on object name
        shader_name = f"{obj}_MTL"
        shading_group_name = f"{shader_name}SG"

        # Create a new Redshift material if it doesn't exist, otherwise use the existing one
        if pm.objExists(shader_name):
            shader = pm.PyNode(shader_name)
            print(f"Using existing Redshift shader: {shader}")
        else:
            shader = pm.shadingNode("RedshiftMaterial", asShader=True, name=shader_name)
            shader.refl_roughness.set(0.5)
            print(f"Created new Redshift shader: {shader}")

        # Get the shape node (shading is applied to shapes, not transforms)
        shapes = obj.getShapes()
        if not shapes:
            print(f"No shape node found for {obj}")
            continue

        print(f"Shape node found: {shapes}")

        # Find the shading group assigned to the shape
        shading_groups = pm.listConnections(shapes, type='shadingEngine')
        if not shading_groups:
            print(f"No shading group found for {obj}")
            continue

        shading_group = shading_groups[0]
        print(f"Shading group found: {shading_group}")

        # Get the Phong, Blinn, or Arnold Standard Surface shader from the shading group's surfaceShader connection
        surface_shaders = pm.listConnections(shading_group.surfaceShader, source=True, destination=False)
        if not surface_shaders:
            print(f"No shader found in {shading_group}")
            continue

        surface_shader = surface_shaders[0]
        shader_type = surface_shader.nodeType()
        if shader_type not in ["phong", "blinn", "standardSurface"]:
            print(f"No Phong, Blinn, or Arnold Standard Surface shader found in {shading_group} (found {shader_type})")
            continue

        print(f"{shader_type.capitalize()} shader detected: {surface_shader}")

        # Determine color and bump attributes based on shader type
        if shader_type == "standardSurface":
            color_attr = "baseColor"
            bump_attr = "normalCamera"
        else:
            color_attr = "color"
            bump_attr = "normalCamera"

        # Find texture connected to the shader's color
        file_texture = pm.listConnections(surface_shader.attr(color_attr), source=True, destination=False, plugs=True) or []
        print(f"File texture connections: {file_texture}")

        if file_texture:
            texture_node = pm.PyNode(file_texture[0].split('.')[0])
            print(f"Texture node identified: {texture_node}")

            # Ensure it is a file texture before connecting
            if texture_node.nodeType() == "file":
                pm.connectAttr(texture_node.outColor, shader.diffuse_color, force=True) # type: ignore
                print(f"Connected {texture_node}.outColor to {shader}.diffuse_color")
            else:
                print(f"Texture node {texture_node} is not a file node.")
        else:
            # If no texture is connected, get and transfer the color value from the shader
            shader_color = surface_shader.attr(color_attr).get()
            shader.diffuse_color.set(shader_color)
            print(f"Transferred color value {shader_color} from {surface_shader} to {shader}.diffuse_color")

        # Find bump node connected to the shader's bump/normal attribute
        bump_node = pm.listConnections(surface_shader.attr(bump_attr), source=True, destination=False, plugs=True) or []
        print(f"Bump node connections: {bump_node}")

        if bump_node:
            bump_node_name = pm.PyNode(bump_node[0].split('.')[0])
            print(f"Bump node identified: {bump_node_name}")

            # Ensure it is a bump node before connecting
            if bump_node_name.nodeType() == "bump2d":
                pm.connectAttr(bump_node_name.outNormal, shader.bump_input, force=True)
                print(f"Connected {bump_node_name}.outNormal to {shader}.bump_input")
            else:
                print(f"Bump node {bump_node_name} is not a bump2d node.")
        else:
            print(f"No bump node connected to {surface_shader}.{bump_attr}")

        # Create a shading group if it doesn't exist
        if not pm.objExists(shading_group_name):
            shading_group = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group_name)
            print(f"Created new shading group: {shading_group}")
        else:
            shading_group = pm.PyNode(shading_group_name)
            print(f"Using existing shading group: {shading_group}")

        # Connect shader to shading group
        pm.connectAttr(shader.outColor, shading_group.surfaceShader, force=True)
        print(f"Connected {shader}.outColor to {shading_group}.surfaceShader")

        # Assign shader to the selected object
        pm.sets(shading_group, edit=True, forceElement=obj)
        print(f"Assigned {shader_name} to {obj} with Reflection Roughness set to 0.5")

assign_redshift_shader()
