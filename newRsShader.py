#Assign new Redshift shader to selected objects or faces. Name shader "Obj_Name[_Selection]_MTL"

import maya.cmds as cmds # type: ignore

def assign_redshift_material():
    selected = cmds.ls(selection=True, flatten=True)
    if not selected:
        cmds.warning("No object or component selected.")
        return

    # Determine if faces/components are selected
    face_selection = [s for s in selected if '.f[' in s]
    if face_selection:
        # Faces/components are selected
        # Get the first object's name (before .f[)
        first_obj_name = face_selection[0].split('.')[0]
        material_name = first_obj_name + "_Face_MTL"
    else:
        # Whole objects are selected
        first_obj_name = selected[0]
        material_name = first_obj_name + "_MTL"

    shading_group_name = material_name + "SG"

    # Check if material already exists, create if not
    if not cmds.objExists(material_name):
        material = cmds.shadingNode("RedshiftMaterial", asShader=True, name=material_name)
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group_name)
        cmds.connectAttr(material + ".outColor", shading_group + ".surfaceShader", force=True)
        if cmds.attributeQuery("refl_roughness", node=material, exists=True):
            cmds.setAttr(material + ".refl_roughness", 0.5)
    else:
        if not cmds.objExists(shading_group_name):
            cmds.warning(f"Material '{material_name}' exists, but shading group '{shading_group_name}' not found. Cannot assign.")
            return
        print(f"Material '{material_name}' already exists. Assigning.")

    # Assign material to selection
    try:
        if face_selection:
            cmds.sets(face_selection, edit=True, forceElement=shading_group_name)
            print(f"Assigned material '{material_name}' to selected faces.")
        else:
            for obj in selected:
                cmds.sets(obj, edit=True, forceElement=shading_group_name)
            print(f"Assigned material '{material_name}' to selected objects.")
    except Exception as e:
        cmds.warning(f"Could not assign material: {e}")

assign_redshift_material()
