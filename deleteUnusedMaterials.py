import maya.cmds as cmds
import maya.mel as mel


DEFAULT_MATERIALS = {"lambert1", "particleCloud1", "shaderGlow1"}


def _material_is_assigned(material):
    shading_groups = cmds.listConnections(material, type="shadingEngine") or []
    for shading_group in shading_groups:
        members = cmds.sets(shading_group, q=True) or []
        if members:
            return True
    return False


def _manual_delete_unused_materials():
    deleted = []
    materials = cmds.ls(materials=True) or []

    for material in materials:
        if material in DEFAULT_MATERIALS:
            continue
        if _material_is_assigned(material):
            continue

        try:
            cmds.delete(material)
            deleted.append(material)
        except Exception as exc:
            print("Failed to delete {}: {}".format(material, exc))

    return deleted


def delete_unused_materials():
    materials_before = set(cmds.ls(materials=True) or [])

    try:
        # Use Maya's built-in cleanup first; it is more reliable than hand-checking SG usage.
        result = mel.eval("MLdeleteUnused;")
        materials_after = set(cmds.ls(materials=True) or [])
        deleted = sorted(materials_before - materials_after)
        print("Deleted unused materials: {}".format(deleted))
        if result is not None:
            print("Maya cleanup result: {}".format(result))
        return deleted
    except Exception as exc:
        print("Built-in cleanup failed, falling back to manual delete: {}".format(exc))
        deleted = _manual_delete_unused_materials()
        print("Deleted unused materials: {}".format(deleted))
        return deleted


delete_unused_materials()
