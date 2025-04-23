import maya.cmds as cmds

def delete_unused_materials():
    deleted = []
    materials = cmds.ls(materials=True)

    # Skip default materials
    default_materials = ['lambert1', 'particleCloud1', 'shaderGlow1']
    
    for mat in materials:
        if mat in default_materials:
            continue

        # Get the shading groups connected to the material
        sg = cmds.listConnections(mat, type='shadingEngine') or []
        is_used = False

        for sg_node in sg:
            # Check if that shading group is assigned to any geometry
            geo = cmds.sets(sg_node, q=True)
            if geo:
                is_used = True
                break

        if not is_used:
            try:
                cmds.delete(mat)
                deleted.append(mat)
            except Exception as e:
                print(f"Failed to delete {mat}: {e}")

    print("Deleted unused materials:", deleted)

delete_unused_materials()
