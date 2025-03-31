#Reveal Shader in Attribute Editor for selected object

import maya.cmds as cmds

def select_shader_from_selection():
    """Selects the shader(s) attached to the currently selected object(s)."""
    selected_objects = cmds.ls(selection=True, type='transform')

    if not selected_objects:
        cmds.warning("Please select an object.")
        return

    shaders_to_select = []
    for obj in selected_objects:
        shapes = cmds.listRelatives(obj, shapes=True, type='shape')
        if shapes:
            for shape in shapes:
                shading_groups = cmds.listConnections(shape, type='shadingEngine')
                if shading_groups:
                    for sg in shading_groups:
                        shaders = cmds.listConnections(sg + ".surfaceShader")
                        if shaders:
                            shaders_to_select.extend(shaders)

    if shaders_to_select:
        cmds.select(shaders_to_select, replace=True)
    else:
        cmds.warning("No shaders found attached to the selected object(s).")

select_shader_from_selection()