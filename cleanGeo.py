#Round-trip selected geometry through OBJ export and import to clean it up.

import os
import re
import tempfile

import maya.cmds as cmds


EXPORT_OPTIONS = "groups=1;ptgroups=1;materials=0;smoothing=1;normals=1"
IMPORT_OPTIONS = "mo=1"
FACE_COMPONENT_RE = re.compile(r"\.f\[(\d+)(?::(\d+))?\]$")


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


def short_name(node):
    return node.split("|")[-1]


def first_long_name(node):
    matches = cmds.ls(node, long=True) or []
    return matches[0] if matches else node


def mesh_shapes(transform):
    shapes = cmds.listRelatives(transform, shapes=True, noIntermediate=True, fullPath=True) or []
    return [shape for shape in shapes if cmds.nodeType(shape) == "mesh"]


def normalized_set_members(shading_engine, flatten=False):
    members = cmds.sets(shading_engine, query=True) or []
    if not members:
        return []

    normalized = cmds.ls(members, long=True, flatten=flatten) or []
    return normalized or members


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


def selected_mesh_records(mesh_transforms):
    records = []

    for transform in mesh_transforms:
        shapes = mesh_shapes(transform)
        parent = cmds.listRelatives(transform, parent=True, fullPath=True) or []
        records.append(
            {
                "transform": transform,
                "name": short_name(transform),
                "parent": parent[0] if parent else None,
                "bbox": cmds.exactWorldBoundingBox(transform),
                "shape_names": [short_name(shape) for shape in shapes],
                "shader_assignments": shader_assignments(transform, shapes),
            }
        )

    return records


def shader_assignments(transform, shapes):
    assignments = []

    for shape in shapes:
        shading_engines = (
            cmds.listConnections(shape, type="shadingEngine", source=False, destination=True)
            or []
        )
        shape_assignments = []

        for shading_engine in unique_in_order(shading_engines):
            shape_assignments.append(
                {
                    "shading_engine": shading_engine,
                    "object": is_object_assigned(transform, shape, shading_engine),
                    "faces": face_indices_for_assignment(transform, shape, shading_engine),
                }
            )

        assignments.append(shape_assignments)

    return assignments


def is_object_assigned(transform, shape, shading_engine):
    if has_whole_shape_shading_connection(shape, shading_engine):
        return True

    transform_names = set(cmds.ls(transform, long=True) or [transform])
    shape_names = set(cmds.ls(shape, long=True) or [shape])

    for member in normalized_set_members(shading_engine):
        if ".f[" in member:
            continue

        member_names = set(cmds.ls(member, long=True) or [member])
        if member_names & transform_names or member_names & shape_names:
            return True

    return False


def has_whole_shape_shading_connection(shape, shading_engine):
    source_plugs = (
        cmds.listConnections(
            "{}.dagSetMembers".format(shading_engine),
            source=True,
            destination=False,
            plugs=True,
        )
        or []
    )
    shape_names = set(cmds.ls(shape, long=True) or [shape])

    for plug in source_plugs:
        node = plug.split(".", 1)[0]
        node_names = set(cmds.ls(node, long=True) or [node])
        if not node_names & shape_names:
            continue

        if ".objectGroups[" not in plug:
            return True

    return False


def face_indices_for_assignment(transform, shape, shading_engine):
    members = normalized_set_members(shading_engine, flatten=True)
    faces = cmds.filterExpand(members, selectionMask=34, expand=True, fullPath=True) or []
    indices = []

    for face in faces:
        if not component_belongs_to_mesh(face, transform, shape):
            continue

        indices.extend(face_indices_from_component(face))

    return sorted(set(indices))


def component_belongs_to_mesh(component, transform, shape):
    owners = cmds.ls(component, objectsOnly=True, long=True) or []
    names = set(cmds.ls([transform, shape], long=True) or [transform, shape])

    for owner in owners:
        owner_names = set(cmds.ls(owner, long=True) or [owner])
        if owner_names & names:
            return True

    return False


def face_indices_from_component(component):
    match = FACE_COMPONENT_RE.search(component)
    if not match:
        return []

    start = int(match.group(1))
    end = int(match.group(2) or start)
    if end < start:
        start, end = end, start

    return list(range(start, end + 1))


def compact_face_components(transform, face_indices):
    if not face_indices:
        return []

    components = []
    start = previous = face_indices[0]

    for face_index in face_indices[1:]:
        if face_index == previous + 1:
            previous = face_index
            continue

        components.append(face_component(transform, start, previous))
        start = previous = face_index

    components.append(face_component(transform, start, previous))
    return components


def face_component(transform, start, end):
    if start == end:
        return "{}.f[{}]".format(transform, start)
    return "{}.f[{}:{}]".format(transform, start, end)


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


def pair_records_to_imports(records, imported_transforms):
    remaining_imports = list(imported_transforms)
    pairs = []

    for record in records:
        match = best_import_match(record, remaining_imports)
        if match is None:
            cmds.warning("No imported mesh found for {}.".format(record["transform"]))
            continue

        remaining_imports.remove(match)
        pairs.append((record, match))

    return pairs


def best_import_match(record, imported_transforms):
    if not imported_transforms:
        return None

    name_matches = [
        imported_transform
        for imported_transform in imported_transforms
        if short_name(imported_transform) == record["name"]
    ]
    candidates = name_matches or imported_transforms

    return min(candidates, key=lambda item: bbox_difference(record["bbox"], item))


def bbox_difference(source_bbox, transform):
    try:
        target_bbox = cmds.exactWorldBoundingBox(transform)
    except RuntimeError:
        return float("inf")

    return sum(abs(source - target) for source, target in zip(source_bbox, target_bbox))


def restore_imported_mesh(record, imported_transform):
    imported_transform = first_long_name(imported_transform)

    if record["parent"] and cmds.objExists(record["parent"]):
        imported_transform = cmds.parent(imported_transform, record["parent"])[0]
        imported_transform = first_long_name(imported_transform)

    imported_transform = cmds.rename(imported_transform, record["name"])
    imported_transform = first_long_name(imported_transform)

    imported_shapes = mesh_shapes(imported_transform)
    for imported_shape, original_shape_name in zip(imported_shapes, record["shape_names"]):
        cmds.rename(imported_shape, original_shape_name)

    apply_shader_assignments(imported_transform, record["shader_assignments"])
    return first_long_name(imported_transform)


def apply_shader_assignments(transform, shader_assignments_by_shape):
    shapes = mesh_shapes(transform)

    for shape_index, imported_shape in enumerate(shapes):
        if shape_index >= len(shader_assignments_by_shape):
            continue

        face_count = cmds.polyEvaluate(imported_shape, face=True) or 0
        shape_assignments = shader_assignments_by_shape[shape_index]
        for assignment in shape_assignments:
            shading_engine = assignment["shading_engine"]
            if not cmds.objExists(shading_engine):
                continue

            if assignment["object"]:
                assign_to_shading_engine(imported_shape, shading_engine)

        for assignment in shape_assignments:
            shading_engine = assignment["shading_engine"]
            if not cmds.objExists(shading_engine) or not assignment["faces"]:
                continue

            valid_faces = [
                face_index
                for face_index in assignment["faces"]
                if 0 <= face_index < face_count
            ]
            face_components = compact_face_components(transform, valid_faces)
            if face_components:
                assign_to_shading_engine(face_components, shading_engine)


def assign_to_shading_engine(members, shading_engine):
    try:
        cmds.sets(members, edit=True, forceElement=shading_engine)
    except RuntimeError as exc:
        cmds.warning(
            "Could not assign {} to {}: {}".format(members, shading_engine, exc)
        )


def show_viewport_message(message):
    cmds.inViewMessage(
        amg=message,
        pos="midCenter",
        fade=True,
        fadeStayTime=1000,
    )


def clean_selected_geo_via_obj():
    mesh_transforms = selected_mesh_transforms()
    if not mesh_transforms:
        cmds.warning("Select one or more mesh objects.")
        return

    records = selected_mesh_records(mesh_transforms)

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
    restored_transforms = [
        restore_imported_mesh(record, imported_transform)
        for record, imported_transform in pair_records_to_imports(records, imported_transforms)
    ]

    if restored_transforms:
        cmds.select(restored_transforms, replace=True)
    else:
        cmds.select(clear=True)

    show_viewport_message("Cleaned")
    print("Clean OBJ round-trip complete: {}".format(export_path))


def main():
    cmds.undoInfo(openChunk=True)
    try:
        clean_selected_geo_via_obj()
    finally:
        cmds.undoInfo(closeChunk=True)


main()
