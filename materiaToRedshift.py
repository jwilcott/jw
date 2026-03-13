# Converts supported Maya shaders on the current selection to Redshift materials.
# Connected color and bump/normal inputs are preserved where possible.

import maya.cmds as cmds


SUPPORTED_SHADER_TYPES = {"phong", "blinn", "standardSurface"}
BUMP_NODE_TYPES = {"bump2d", "bump3d"}


def _short_name(node_name):
    return node_name.split("|")[-1].split(":")[-1]


def _make_unique_name(base_name):
    if not cmds.objExists(base_name):
        return base_name

    index = 1
    while cmds.objExists("{}_{}".format(base_name, index)):
        index += 1
    return "{}_{}".format(base_name, index)


def _ensure_redshift_material(base_name):
    material_name = "{}_RS".format(_short_name(base_name))

    if cmds.objExists(material_name):
        if cmds.nodeType(material_name) == "RedshiftMaterial":
            return material_name
        material_name = _make_unique_name(material_name)

    shader = cmds.shadingNode("RedshiftMaterial", asShader=True, name=material_name)
    if cmds.attributeQuery("refl_roughness", node=shader, exists=True):
        cmds.setAttr(shader + ".refl_roughness", 0.5)
    return shader


def _ensure_shading_group(shader):
    shading_group_name = "{}SG".format(_short_name(shader))

    if cmds.objExists(shading_group_name):
        if cmds.nodeType(shading_group_name) == "shadingEngine":
            if not cmds.isConnected(shader + ".outColor", shading_group_name + ".surfaceShader"):
                cmds.connectAttr(shader + ".outColor", shading_group_name + ".surfaceShader", force=True)
            return shading_group_name
        shading_group_name = _make_unique_name(shading_group_name)

    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group_name)
    cmds.connectAttr(shader + ".outColor", shading_group + ".surfaceShader", force=True)
    return shading_group


def _copy_attr_or_connection(source_attr, destination_attr):
    incoming = cmds.listConnections(source_attr, source=True, destination=False, plugs=True) or []
    if incoming:
        try:
            if not cmds.isConnected(incoming[0], destination_attr):
                cmds.connectAttr(incoming[0], destination_attr, force=True)
            return
        except Exception as exc:
            print("Failed to connect {} to {}: {}".format(incoming[0], destination_attr, exc))

    try:
        value = cmds.getAttr(source_attr)
        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        if isinstance(value, tuple):
            cmds.setAttr(destination_attr, *value, type="double3")
        else:
            cmds.setAttr(destination_attr, value)
    except Exception as exc:
        print("Failed to copy value from {} to {}: {}".format(source_attr, destination_attr, exc))


def _copy_bump_or_normal(source_shader, target_shader):
    source_attr = source_shader + ".normalCamera"
    incoming = cmds.listConnections(source_attr, source=True, destination=False, plugs=True) or []
    if not incoming:
        print("No bump/normal input connected to {}".format(source_attr))
        return

    source_plug = incoming[0]
    source_node = source_plug.split(".", 1)[0]

    try:
        if not cmds.isConnected(source_plug, target_shader + ".bump_input"):
            cmds.connectAttr(source_plug, target_shader + ".bump_input", force=True)
        print("Connected {} to {}.bump_input".format(source_plug, target_shader))
    except Exception as exc:
        print("Failed to connect bump/normal {}: {}".format(source_plug, exc))
        return

    if cmds.nodeType(source_node) in BUMP_NODE_TYPES and cmds.attributeQuery("bumpDepth", node=source_node, exists=True):
        try:
            cmds.setAttr(source_node + ".bumpDepth", 0.1)
            print("Set {}.bumpDepth to 0.1".format(source_node))
        except Exception as exc:
            print("Failed to set bump depth on {}: {}".format(source_node, exc))


def _get_surface_shader(shading_group):
    shaders = cmds.listConnections(shading_group + ".surfaceShader", source=True, destination=False) or []
    if not shaders:
        return None
    return shaders[0]


def _shading_groups_for_target(target):
    if "." in target:
        object_name = target.split(".", 1)[0]
        shapes = cmds.ls(object_name, long=True) or [object_name]
    else:
        target_path = (cmds.ls(target, long=True) or [target])[0]
        target_type = cmds.nodeType(target_path)
        if target_type == "transform":
            shapes = cmds.listRelatives(target_path, shapes=True, fullPath=True) or []
        else:
            shapes = [target_path]

    shading_groups = []
    for shape in shapes:
        shape_sets = cmds.listConnections(shape, type="shadingEngine") or []
        shading_groups.extend(shape_sets)

    return list(dict.fromkeys(shading_groups))


def _members_for_target(shading_group, target):
    members = cmds.sets(shading_group, q=True) or []
    member_paths = cmds.ls(members, long=True, flatten=True) or []
    target_path = (cmds.ls(target, long=True) or [target])[0]
    target_type = cmds.nodeType(target)

    if "." in target_path:
        return [member for member in member_paths if member == target_path]

    matched = []
    for member in member_paths:
        if member == target_path or member.startswith(target_path + "|") or member.startswith(target_path + "."):
            matched.append(member)
        elif target_type == "transform":
            shapes = cmds.listRelatives(target_path, shapes=True, fullPath=True) or []
            if any(member == shape or member.startswith(shape + ".") for shape in shapes):
                matched.append(member)
    return list(dict.fromkeys(matched))


def _selected_targets():
    selection = cmds.ls(selection=True, long=True, flatten=True) or []
    if not selection:
        return []

    targets = []
    for item in selection:
        if "." in item:
            targets.append(item)
            continue

        node_type = cmds.nodeType(item)
        if node_type in {"transform", "mesh", "nurbsSurface", "subdiv"}:
            targets.append(item)

    return list(dict.fromkeys(targets))


def assign_redshift_shader():
    targets = _selected_targets()
    if not targets:
        cmds.warning("No supported object or component selected.")
        return

    converted_pairs = set()

    for target in targets:
        print("Processing target: {}".format(target))
        shading_groups = _shading_groups_for_target(target)
        if not shading_groups:
            print("No shading group found for {}".format(target))
            continue

        for shading_group in shading_groups:
            source_shader = _get_surface_shader(shading_group)
            if not source_shader:
                print("No shader connected to {}".format(shading_group))
                continue

            source_type = cmds.nodeType(source_shader)
            if source_type not in SUPPORTED_SHADER_TYPES:
                print("Skipping {} because {} is type {}".format(shading_group, source_shader, source_type))
                continue

            target_members = _members_for_target(shading_group, target)
            if not target_members:
                print("No members from {} matched target {}".format(shading_group, target))
                continue

            redshift_shader = _ensure_redshift_material(source_shader)
            redshift_sg = _ensure_shading_group(redshift_shader)

            if (source_shader, redshift_shader) not in converted_pairs:
                color_attr = ".baseColor" if source_type == "standardSurface" else ".color"
                _copy_attr_or_connection(source_shader + color_attr, redshift_shader + ".diffuse_color")
                _copy_bump_or_normal(source_shader, redshift_shader)
                converted_pairs.add((source_shader, redshift_shader))
                print("Converted {} -> {}".format(source_shader, redshift_shader))

            try:
                cmds.sets(target_members, edit=True, forceElement=redshift_sg)
                print("Assigned {} to {}".format(redshift_shader, target_members))
            except Exception as exc:
                print("Failed to assign {} to {}: {}".format(redshift_shader, target_members, exc))


assign_redshift_shader()
