#Round-trip selected geometry through OBJ export and import to clean it up.

import os
import tempfile

import maya.cmds as cmds


EXPORT_OPTIONS = "groups=1;ptgroups=1;materials=0;smoothing=1;normals=1"
IMPORT_OPTIONS = "mo=1"


def ensure_obj_plugin_loaded():
    if cmds.pluginInfo("objExport", query=True, loaded=True):
        return
    cmds.loadPlugin("objExport")


def unique_in_order(items):
    seen = set()
    ordered = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def selected_mesh_transforms():
    selection = cmds.ls(selection=True, long=True, objectsOnly=True) or []
    mesh_transforms = []

    for node in selection:
        if cmds.nodeType(node) == "mesh":
            parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
            mesh_transforms.extend(parents)
            continue

        if cmds.nodeType(node) != "transform":
            continue

        shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True, fullPath=True) or []
        if any(cmds.nodeType(shape) == "mesh" for shape in shapes):
            mesh_transforms.append(node)

    return unique_in_order(mesh_transforms)


def imported_mesh_transforms(new_nodes):
    mesh_transforms = []

    for node in new_nodes:
        if not cmds.objExists(node):
            continue

        node_type = cmds.nodeType(node)
        if node_type == "mesh":
            parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
            mesh_transforms.extend(parents)
        elif node_type == "transform":
            shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True, fullPath=True) or []
            if any(cmds.nodeType(shape) == "mesh" for shape in shapes):
                mesh_transforms.append(node)

    return unique_in_order(mesh_transforms)


def clean_selected_geo_via_obj():
    mesh_transforms = selected_mesh_transforms()
    if not mesh_transforms:
        cmds.warning("Select one or more mesh objects.")
        return

    ensure_obj_plugin_loaded()

    temp_dir = tempfile.mkdtemp(prefix="maya_obj_clean_")
    export_path = os.path.join(temp_dir, "cleaned_selection.obj")

    cmds.select(mesh_transforms, replace=True)
    cmds.file(
        export_path,
        force=True,
        options=EXPORT_OPTIONS,
        type="OBJexport",
        preserveReferences=False,
        exportSelected=True,
    )

    cmds.delete(mesh_transforms)

    new_nodes = cmds.file(
        export_path,
        i=True,
        ignoreVersion=True,
        ra=True,
        mergeNamespacesOnClash=False,
        namespace=":",
        options=IMPORT_OPTIONS,
        preserveReferences=False,
        returnNewNodes=True,
    )

    imported_transforms = imported_mesh_transforms(new_nodes)
    if imported_transforms:
        cmds.select(imported_transforms, replace=True)
    else:
        cmds.select(clear=True)

    print("Clean OBJ round-trip complete: {}".format(export_path))


def main():
    cmds.undoInfo(openChunk=True)
    try:
        clean_selected_geo_via_obj()
    finally:
        cmds.undoInfo(closeChunk=True)


main()
