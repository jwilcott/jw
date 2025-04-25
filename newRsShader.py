#Assign new Redshift shader to selected objects. Name shader "Obj_Name + _MTL"

import maya.cmds as cmds # type: ignore

def assign_redshift_material():
    selected = cmds.ls(selection=True)
    if not selected:
        cmds.warning("No object selected.")
        return

    # Use the first selected object's name for the material
    first_obj_name = selected[0]
    # Basic sanitization for node names (replace potential invalid characters if needed)
    # For simplicity, assuming standard object names work. More robust sanitization could be added.
    material_name = first_obj_name + "_MTL"
    shading_group_name = material_name + "SG" # Renamed variable for clarity

    # Check if material already exists, create if not
    if not cmds.objExists(material_name):
        material = cmds.shadingNode("RedshiftMaterial", asShader=True, name=material_name)
        # Use the determined shading_group_name when creating the set
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group_name)
        cmds.connectAttr(material + ".outColor", shading_group + ".surfaceShader", force=True)
        # Check for roughness attribute on the newly created material
        if cmds.attributeQuery("refl_roughness", node=material, exists=True):
             cmds.setAttr(material + ".refl_roughness", 0.5)  # Set roughness to 0.5
    else:
        # If material exists, assume the SG also exists with the derived name
        # No need to reassign material variable here, just ensure shading_group_name is correct
        if not cmds.objExists(shading_group_name):
            # Handle case where material exists but SG doesn't (unlikely but possible)
            cmds.warning(f"Material '{material_name}' exists, but shading group '{shading_group_name}' not found. Cannot assign.")
            return
        print(f"Material '{material_name}' already exists. Assigning.")


    # Assign the single material to all selected objects
    for obj in selected:
        try:
            # Use the consistent shading_group_name for assignment
            cmds.sets(obj, edit=True, forceElement=shading_group_name)
        except Exception as e:
            cmds.warning(f"Could not assign material to {obj}: {e}")

    print(f"Assigned material '{material_name}' to selected objects.")

assign_redshift_material()
