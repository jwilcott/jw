#Assign new Redshift shader to selected objects. Name shader "Obj_Name + _MTL"

import maya.cmds as cmds # type: ignore

def assign_redshift_material():
    selected = cmds.ls(selection=True)
    if not selected:
        cmds.warning("No object selected.")
        return
    
    for obj in selected:
        material_name = obj + "_MTL"
        shading_group = material_name + "SG"
        
        # Check if material already exists
        if not cmds.objExists(material_name):
            material = cmds.shadingNode("RedshiftMaterial", asShader=True, name=material_name)
            shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group)
            cmds.connectAttr(material + ".outColor", shading_group + ".surfaceShader", force=True)
            if cmds.objExists(material + ".reflRoughness"):
                cmds.setAttr(material + ".reflRoughness", 0.5)  # Set roughness to 0.5
        else:
            material = material_name
            shading_group = shading_group
        
        # Assign material to the object
        cmds.sets(obj, edit=True, forceElement=shading_group)
    
    print("Assigned materials to selected objects.")

assign_redshift_material()
