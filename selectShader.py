#Reveal Shader in Attribute Editor for selected object
#if redshift shader is plugged into shading group, it will be selected in the attribute editor

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
            for shape in shapes:
                # Use the full path of the shape for connection queries
                sg_raw = cmds.listConnections(shape, type='shadingEngine')
                shading_groups = cmds.ls(sg_raw, long=True) if sg_raw else []
                if shading_groups:
                    for sg in shading_groups:
                        rs_shaders = (
                            cmds.listConnections(sg + ".rsSurfaceShader", source=True, destination=False)
                            if cmds.attributeQuery("rsSurfaceShader", node=sg, exists=True)
                            else None
                        )
                        if rs_shaders:
                            shaders_to_select.extend(list(set(rs_shaders)))
                        else:
                            shaders = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False)
                            if shaders:
                                shaders_to_select.extend(list(set(shaders)))

    if shaders_to_select:
        # Ensure the final list is unique before selecting
        cmds.select(list(set(shaders_to_select)), replace=True)
    else:
        cmds.warning("No shaders found attached to the selected object(s).")

select_shader_from_selection()