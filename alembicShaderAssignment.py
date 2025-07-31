# Select original source group, then alembic cache group. 

import maya.cmds as cmds
import maya.mel as mel

def get_all_shapes(node):
    """Recursively get all mesh shapes under a node."""
    shapes = []
    children = cmds.listRelatives(node, children=True, fullPath=True) or []
    for child in children:
        if cmds.objectType(child, isType='transform'):
            shapes.extend(get_all_shapes(child))
        elif cmds.objectType(child, isType='mesh'):
            shapes.append(child)
    return shapes

def get_shader_assignments(group_name):
    """Collect shader assignments including component-level assignments from the source group."""
    shader_dict = {}
    all_shapes = get_all_shapes(group_name)
    
    print(f"Scanning source group '{group_name}' for shapes...")
    if not all_shapes:
        print(f"No shapes found in source group '{group_name}'")
        return shader_dict
    
    for shape in all_shapes:
        print(f"Checking shape: {shape}")
        shader_engines = cmds.listConnections(shape, type='shadingEngine', destination=True) or []
        if not shader_engines:
            print(f"No shader engines connected to {shape}")
            continue
            
        for se in shader_engines:
            if cmds.sets(shape, isMember=se):
                shader_dict[shape] = {'type': 'object', 'shader': se}
                print(f"Found object-level shader {se} for {shape}")
            
            # Check for component-level assignments
            component_assignments = cmds.listConnections(f"{se}.dagSetMembers", source=True, destination=False) or []
            if component_assignments:
                face_groups = mel.eval(f'polyListComponentConversion -fromFace -toFace "{shape}"')
                if face_groups:
                    shader_dict[shape] = {'type': 'component', 'shader': se, 'faces': face_groups}
                    print(f"Found component-level shader {se} for {shape} with faces: {face_groups}")
    
    if not shader_dict:
        print("No shader assignments found in source group")
    return shader_dict

def apply_shaders_to_alembic(source_group, alembic_group):
    """Apply shaders from source group to matching alembic cache objects."""
    shader_assignments = get_shader_assignments(source_group)
    alembic_shapes = get_all_shapes(alembic_group)
    
    print(f"\nScanning alembic group '{alembic_group}' for shapes...")
    if not alembic_shapes:
        print(f"No shapes found in alembic group '{alembic_group}'")
        return
    
    for alembic_shape in alembic_shapes:
        print(f"Checking alembic shape: {alembic_shape}")
        if not cmds.objectType(alembic_shape, isType='mesh'):
            print(f"Skipping non-mesh shape: {alembic_shape}")
            continue
            
        alembic_base_name = alembic_shape.split('|')[-1].split(':')[-1]
        matching_source = None
        
        for source_shape in shader_assignments.keys():
            source_base_name = source_shape.split('|')[-1].split(':')[-1]
            if source_base_name == alembic_base_name:
                matching_source = source_shape
                print(f"Exact match found: {alembic_shape} -> {source_shape}")
                break
            elif source_base_name in alembic_base_name or alembic_base_name in source_base_name:
                matching_source = source_shape
                print(f"Partial match found: {alembic_shape} -> {source_shape}")
                break
        
        if not matching_source:
            print(f"No matching source shape found for {alembic_shape}")
            continue
        
        if shader_assignments.get(matching_source):
            assignment = shader_assignments[matching_source]
            shader_engine = assignment['shader']
            
            if assignment['type'] == 'object':
                try:
                    cmds.sets(alembic_shape, forceElement=shader_engine)
                    print(f"Successfully applied shader {shader_engine} to {alembic_shape}")
                except Exception as e:
                    print(f"Failed to apply shader {shader_engine} to {alembic_shape}: {str(e)}")
                
            elif assignment['type'] == 'component':
                face_indices = assignment['faces']
                if face_indices:
                    alembic_faces = []
                    for face in face_indices:
                        face_index = face.split('[')[-1].split(']')[0]
                        alembic_faces.append(f"{alembic_shape}.f[{face_index}]")
                    
                    if alembic_faces:
                        try:
                            cmds.sets(alembic_faces, forceElement=shader_engine)
                            print(f"Successfully applied component shader {shader_engine} to {alembic_shape} faces")
                        except Exception as e:
                            print(f"Failed to apply component shader {shader_engine} to {alembic_shape}: {str(e)}")
                    else:
                        print(f"No valid faces found for component shading on {alembic_shape}")
        else:
            print(f"No shader assignment data for matched source {matching_source}")

def main():
    """Main function to process selected groups."""
    selection = cmds.ls(selection=True, type='transform')
    
    if len(selection) != 2:
        cmds.warning("Please select exactly two groups: source group and alembic group")
        print("Selection error: Please select exactly two groups")
        return
    
    source_group, alembic_group = selection
    print(f"Source group: {source_group}")
    print(f"Alembic group: {alembic_group}")
    
    if not cmds.objExists(source_group) or not cmds.objExists(alembic_group):
        cmds.error("One or both selected groups do not exist")
        print("Group existence error")
        return
    
    apply_shaders_to_alembic(source_group, alembic_group)
    print("Shader assignment process completed!")

if __name__ == "__main__":
    main()