# Converts supported Maya shaders on the current selection to Redshift materials.
# Connected color and bump/normal inputs are preserved where possible.

import maya.cmds as cmds


SUPPORTED_SHADER_TYPES = {"phong", "blinn", "standardSurface"}
BUMP_NODE_TYPES = {"bump2d", "bump3d"}


def _short_name(node_name):
    return node_name.split("|")[-1].split(":")[-1]


def _safe_node_name(node_name):
    return node_name.split("|")[-1].replace(":", "_")


def _unique_in_order(items):
    return list(dict.fromkeys(items))


def _make_unique_name(base_name):
    if not cmds.objExists(base_name):
        return base_name

    index = 1
    while cmds.objExists("{}_{}".format(base_name, index)):
        index += 1
    return "{}_{}".format(base_name, index)


def _ensure_redshift_material(base_name):
    material_name = "{}_RS".format(_safe_node_name(base_name))

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


def _long_name(item):
    matches = cmds.ls(item, long=True, flatten=True) or []
    return matches[0] if matches else item


def _node_from_component(item):
    return item.split(".", 1)[0]


def _shapes_for_node(node):
    node_path = _long_name(node)
    try:
        node_type = cmds.nodeType(node_path)
    except Exception:
        return []

    if node_type == "transform":
        return cmds.listRelatives(node_path, shapes=True, noIntermediate=True, fullPath=True) or []

    if node_type in {"mesh", "nurbsSurface", "subdiv"}:
        return [node_path]

    return []


def _shading_groups_for_target(target):
    if "." in target:
        shapes = _shapes_for_node(_node_from_component(target))
    else:
        shapes = _shapes_for_node(target)

    shading_groups = []
    for shape in shapes:
        shape_sets = cmds.listConnections(
            shape,
            type="shadingEngine",
            source=False,
            destination=True,
        ) or []
        shading_groups.extend(shape_sets)

    return _unique_in_order(shading_groups)


def _is_member(item, shading_group):
    try:
        return bool(cmds.sets(item, isMember=shading_group))
    except Exception:
        return False


def _normalized_set_members(shading_group, flatten=False):
    members = cmds.sets(shading_group, q=True) or []
    if not members:
        return []

    return cmds.ls(members, long=True, flatten=flatten) or members


def _component_belongs_to_shapes(component, shapes):
    owners = cmds.ls(component, objectsOnly=True, long=True) or []
    shape_names = set(cmds.ls(shapes, long=True) or shapes)

    for owner in owners:
        owner_names = set(cmds.ls(owner, long=True) or [owner])
        if owner_names & shape_names:
            return True

    return False


def _component_members_for_target(shading_group, target):
    components = cmds.ls(target, long=True, flatten=True) or [target]
    return [component for component in components if _is_member(component, shading_group)]


def _object_members_for_target(shading_group, target):
    target_path = _long_name(target)
    shapes = _shapes_for_node(target_path)
    candidates = []

    if _is_member(target_path, shading_group):
        candidates.append(target_path)

    for shape in shapes:
        if _is_member(shape, shading_group):
            candidates.append(shape)

    for member in _normalized_set_members(shading_group, flatten=True):
        if "." not in member:
            continue
        if _component_belongs_to_shapes(member, shapes):
            candidates.append(member)

    return _unique_in_order(candidates)


def _members_for_target(shading_group, target):
    if "." in target:
        return _component_members_for_target(shading_group, target)

    return _object_members_for_target(shading_group, target)


def _split_object_and_component_members(members):
    object_members = []
    component_members = []

    for member in members:
        if "." in member:
            component_members.append(member)
        else:
            object_members.append(member)

    return object_members, component_members


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

    converted_shaders = {}
    copied_shaders = set()

    for target in targets:
        print("Processing target: {}".format(target))
        shading_groups = _shading_groups_for_target(target)
        if not shading_groups:
            print("No shading group found for {}".format(target))
            continue

        pending_assignments = []

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
            object_members, component_members = _split_object_and_component_members(target_members)

            redshift_shader = converted_shaders.get(source_shader)
            if not redshift_shader:
                redshift_shader = _ensure_redshift_material(source_shader)
                converted_shaders[source_shader] = redshift_shader
            redshift_sg = _ensure_shading_group(redshift_shader)

            if source_shader not in copied_shaders:
                color_attr = ".baseColor" if source_type == "standardSurface" else ".color"
                _copy_attr_or_connection(source_shader + color_attr, redshift_shader + ".diffuse_color")
                _copy_bump_or_normal(source_shader, redshift_shader)
                copied_shaders.add(source_shader)
                print("Converted {} -> {}".format(source_shader, redshift_shader))

            pending_assignments.append(
                {
                    "shader": redshift_shader,
                    "shading_group": redshift_sg,
                    "object_members": object_members,
                    "component_members": component_members,
                }
            )

        for assignment_type in ("object_members", "component_members"):
            for assignment in pending_assignments:
                members = assignment[assignment_type]
                if not members:
                    continue

                try:
                    cmds.sets(members, edit=True, forceElement=assignment["shading_group"])
                    print("Assigned {} to {}".format(assignment["shader"], members))
                except Exception as exc:
                    print(
                        "Failed to assign {} to {}: {}".format(
                            assignment["shader"],
                            members,
                            exc,
                        )
                    )


assign_redshift_shader()
