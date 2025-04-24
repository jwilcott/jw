#Reveal Shader in Attribute Editor for selected object

import maya.cmds as cmds

def select_shader_from_selection():
    """Selects the shader(s) attached to the currently selected object(s)."""
    # Use long=True to get unique path names
    selected_objects = cmds.ls(selection=True, long=True, type='transform')

    if not selected_objects:
        cmds.warning("Please select an object.")
        return

    shaders_to_select = []
    for obj in selected_objects:
        # Get full paths for shapes to ensure uniqueness
        shapes = cmds.listRelatives(obj, shapes=True, type='shape', fullPath=True)
        if shapes:
            for shape in shapes: # 'shape' now holds the full path
                # Use the full path of the shape for connection queries
                shading_groups = cmds.listConnections(shape, type='shadingEngine')
                if shading_groups:
                    # Shading group names are usually unique, but check connections from them
                    for sg in shading_groups:
                        # Ensure we query the specific surfaceShader attribute
                        shaders = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False)
                        if shaders:
                            # Use list() to ensure we get unique shader names, though listConnections usually handles this
                            shaders_to_select.extend(list(set(shaders))) # Use set to ensure uniqueness

    if shaders_to_select:
        # Ensure the final list is unique before selecting
        cmds.select(list(set(shaders_to_select)), replace=True)
    else:
        cmds.warning("No shaders found attached to the selected object(s).")

select_shader_from_selection()