# Build Redshift metalness/roughness/normal hookups from selected shaders.
# Expects the diffuse texture filename to share a base name with *_nmap and *_spec.

import os

import maya.cmds as cmds


SHADER_TYPES = {"RedshiftMaterial"}
TEXTURE_EXTENSIONS = [".png", ".tif", ".tiff", ".exr", ".jpg", ".jpeg", ".tga"]

DIFFUSE_TOKENS = [
    "_diffuse",
    "_diff",
    "_albedo",
    "_basecolor",
    "_base_color",
    "_color",
    "_col",
]
NORMAL_TOKENS = ["_nmap", "_normal", "_norm", "_nrm"]
SPEC_TOKENS = ["_spec", "_specular"]

FRESNEL_ATTRS = ["refl_fresnel_mode", "refl_fresnel_type", "fresnel_mode", "fresnelType"]
DIFFUSE_ATTRS = ["diffuse_color", "diffuseColor", "base_color", "baseColor", "color"]
METALNESS_ATTRS = ["refl_metalness", "metalness"]
ROUGHNESS_ATTRS = ["refl_roughness", "roughness"]
EMISSION_WEIGHT_ATTRS = ["emission_weight", "emissionWeight"]
BUMP_ATTRS = ["bump_input", "bumpInput", "normalCamera"]

BUMP_INPUT_ATTRS = ["input", "inputTexture", "tex0"]
BUMP_OUTPUT_ATTRS = ["out", "outColor", "outValue"]
BUMP_TYPE_ATTRS = ["inputType", "input_type", "bumpInputType", "mapType"]
BUMP_SCALE_ATTRS = ["scale", "heightScale", "height_scale", "bumpScale"]


def _unique_in_order(items):
    return list(dict.fromkeys(items))


def _short_name(node):
    return node.split("|")[-1].split(":")[-1]


def _safe_name(name):
    return _short_name(name).replace(":", "_")


def _make_unique_name(base_name):
    if not cmds.objExists(base_name):
        return base_name

    index = 1
    while cmds.objExists("{}_{}".format(base_name, index)):
        index += 1
    return "{}_{}".format(base_name, index)


def _has_attr(node, attr):
    return cmds.attributeQuery(attr, node=node, exists=True)


def _first_existing_attr(node, attrs):
    for attr in attrs:
        if _has_attr(node, attr):
            return attr
    return None


def _connect(source_attr, destination_attr):
    try:
        if not cmds.isConnected(source_attr, destination_attr):
            cmds.connectAttr(source_attr, destination_attr, force=True)
        return True
    except Exception as exc:
        print("Failed to connect {} to {}: {}".format(source_attr, destination_attr, exc))
        return False


def _set_enum_by_label(node, attr, labels, fallback_values=None):
    if not _has_attr(node, attr):
        return False

    enum_data = cmds.attributeQuery(attr, node=node, listEnum=True) or []
    enum_names = enum_data[0].split(":") if enum_data else []
    wanted = {_normalize_label(label) for label in labels}

    for index, enum_name in enumerate(enum_names):
        if _normalize_label(enum_name) in wanted:
            cmds.setAttr("{}.{}".format(node, attr), index)
            return True

    for value in fallback_values or []:
        try:
            cmds.setAttr("{}.{}".format(node, attr), value)
            return True
        except Exception:
            pass

    return False


def _normalize_label(label):
    return "".join(char.lower() for char in label if char.isalnum())


def _selected_shaders():
    selection = cmds.ls(selection=True, flatten=True) or []
    shaders = []

    for item in selection:
        if "." in item:
            continue

        try:
            node_type = cmds.nodeType(item)
        except Exception:
            continue

        if node_type in SHADER_TYPES:
            shaders.append(item)
        elif node_type == "shadingEngine":
            connected = cmds.listConnections(item + ".surfaceShader", source=True, destination=False) or []
            shaders.extend([node for node in connected if cmds.nodeType(node) in SHADER_TYPES])

    return _unique_in_order(shaders)


def _set_fresnel_to_metalness(shader):
    for attr in FRESNEL_ATTRS:
        if _set_enum_by_label(shader, attr, ["Metalness", "Metalness/Roughness"], fallback_values=[2, 1]):
            print("Set {}.{} to Metalness".format(shader, attr))
            return True

    print("Could not find a Fresnel type attr on {}".format(shader))
    return False


def _file_node_from_shader(shader):
    diffuse_attr = _first_existing_attr(shader, DIFFUSE_ATTRS)
    if not diffuse_attr:
        return None, None

    connections = cmds.listConnections(
        "{}.{}".format(shader, diffuse_attr),
        source=True,
        destination=False,
        plugs=False,
    ) or []

    for node in connections:
        if cmds.nodeType(node) == "file":
            return node, diffuse_attr

    history = cmds.listHistory(connections, pruneDagObjects=True) or []
    for node in history:
        if cmds.nodeType(node) == "file":
            return node, diffuse_attr

    return None, diffuse_attr


def _texture_path(file_node):
    if not file_node or not _has_attr(file_node, "fileTextureName"):
        return None

    path = cmds.getAttr(file_node + ".fileTextureName")
    return path or None


def _path_exists(path):
    expanded_path = os.path.expandvars(os.path.expanduser(path))
    if os.path.exists(expanded_path):
        return True

    try:
        workspace_path = cmds.workspace(expandName=path)
    except Exception:
        workspace_path = None

    return bool(workspace_path and os.path.exists(os.path.expandvars(workspace_path)))


def _candidate_texture_paths(diffuse_path, target_tokens):
    folder, filename = os.path.split(diffuse_path)
    stem, extension = os.path.splitext(filename)
    extensions = _unique_in_order([extension] + TEXTURE_EXTENSIONS)
    stems = []

    lower_stem = stem.lower()
    for diffuse_token in DIFFUSE_TOKENS:
        if diffuse_token in lower_stem:
            start = lower_stem.rfind(diffuse_token)
            for target_token in target_tokens:
                stems.append(stem[:start] + target_token + stem[start + len(diffuse_token):])

    for target_token in target_tokens:
        stems.append(stem + target_token)

    candidates = []
    for candidate_stem in _unique_in_order(stems):
        for candidate_extension in extensions:
            candidates.append(os.path.join(folder, candidate_stem + candidate_extension))

    return candidates


def _find_existing_texture(diffuse_path, target_tokens):
    for path in _candidate_texture_paths(diffuse_path, target_tokens):
        if _path_exists(path):
            return path

    candidates = _candidate_texture_paths(diffuse_path, target_tokens)
    return candidates[0] if candidates else None


def _copy_place2d(source_file, target_file):
    source_place = _upstream_place2d(source_file)
    if not source_place:
        return

    for source_attr, target_attr in [
        ("outUV", "uvCoord"),
        ("outUvFilterSize", "uvFilterSize"),
        ("coverage", "coverage"),
        ("translateFrame", "translateFrame"),
        ("rotateFrame", "rotateFrame"),
        ("mirrorU", "mirrorU"),
        ("mirrorV", "mirrorV"),
        ("stagger", "stagger"),
        ("wrapU", "wrapU"),
        ("wrapV", "wrapV"),
        ("repeatUV", "repeatUV"),
        ("offset", "offset"),
        ("rotateUV", "rotateUV"),
        ("noiseUV", "noiseUV"),
        ("vertexUvOne", "vertexUvOne"),
        ("vertexUvTwo", "vertexUvTwo"),
        ("vertexUvThree", "vertexUvThree"),
        ("vertexCameraOne", "vertexCameraOne"),
    ]:
        source_plug = "{}.{}".format(source_place, source_attr)
        target_plug = "{}.{}".format(target_file, target_attr)
        if _has_attr(source_place, source_attr) and _has_attr(target_file, target_attr):
            _connect(source_plug, target_plug)


def _upstream_place2d(file_node):
    connections = cmds.listConnections(file_node, source=True, destination=False) or []
    for node in connections:
        if cmds.nodeType(node) == "place2dTexture":
            return node
    return None


def _create_file_node(path, base_name, source_file=None, color_space="Raw"):
    file_node = cmds.shadingNode("file", asTexture=True, name=_make_unique_name(base_name))
    cmds.setAttr(file_node + ".fileTextureName", path, type="string")

    if _has_attr(file_node, "colorSpace"):
        try:
            cmds.setAttr(file_node + ".colorSpace", color_space, type="string")
        except Exception:
            pass

    if source_file:
        _copy_place2d(source_file, file_node)

    return file_node


def _create_bump_node(shader):
    return cmds.shadingNode(
        "RedshiftBumpMap",
        asUtility=True,
        name=_make_unique_name("{}_rsBumpMap".format(_safe_name(shader))),
    )


def _set_bump_to_tangent_space(bump_node):
    for attr in BUMP_TYPE_ATTRS:
        if _set_enum_by_label(
            bump_node,
            attr,
            ["Tangent Space", "Tangent Space Normal", "Tangent-Space Normal", "Normal Map"],
            fallback_values=[1],
        ):
            print("Set {}.{} to tangent space".format(bump_node, attr))
            return True

    print("Could not find tangent-space type attr on {}".format(bump_node))
    return False


def _set_bump_scale(bump_node, value=1.0):
    scale_attr = _first_existing_attr(bump_node, BUMP_SCALE_ATTRS)
    if not scale_attr:
        print("Could not find scale attr on {}".format(bump_node))
        return False

    cmds.setAttr("{}.{}".format(bump_node, scale_attr), value)
    print("Set {}.{} to {}".format(bump_node, scale_attr, value))
    return True


def _connect_normal_map(shader, diffuse_file, normal_path):
    normal_file = _create_file_node(
        normal_path,
        "{}_nmap_FILE".format(_safe_name(shader)),
        source_file=diffuse_file,
        color_space="Raw",
    )
    bump_node = _create_bump_node(shader)

    bump_input_attr = _first_existing_attr(bump_node, BUMP_INPUT_ATTRS)
    bump_output_attr = _first_existing_attr(bump_node, BUMP_OUTPUT_ATTRS)
    shader_bump_attr = _first_existing_attr(shader, BUMP_ATTRS)

    if not bump_input_attr or not bump_output_attr or not shader_bump_attr:
        print("Could not find normal-map attrs for {}".format(shader))
        return

    _set_bump_to_tangent_space(bump_node)
    _set_bump_scale(bump_node, 1.0)
    _connect(normal_file + ".outColor", bump_node + "." + bump_input_attr)
    _connect(bump_node + "." + bump_output_attr, shader + "." + shader_bump_attr)
    print("Connected normal map {} to {}".format(normal_path, shader))


def _connect_spec_map(shader, diffuse_file, spec_path):
    spec_file = _create_file_node(
        spec_path,
        "{}_spec_FILE".format(_safe_name(shader)),
        source_file=diffuse_file,
        color_space="Raw",
    )

    metalness_attr = _first_existing_attr(shader, METALNESS_ATTRS)
    roughness_attr = _first_existing_attr(shader, ROUGHNESS_ATTRS)
    emission_weight_attr = _first_existing_attr(shader, EMISSION_WEIGHT_ATTRS)

    if metalness_attr:
        _connect(spec_file + ".outColorR", shader + "." + metalness_attr)
    else:
        print("Could not find metalness attr on {}".format(shader))

    if roughness_attr:
        _connect(spec_file + ".outColorG", shader + "." + roughness_attr)
    else:
        print("Could not find roughness attr on {}".format(shader))

    if emission_weight_attr:
        _connect(spec_file + ".outColorB", shader + "." + emission_weight_attr)
    else:
        print("Could not find emission weight attr on {}".format(shader))

    print("Connected spec map {} to {}".format(spec_path, shader))


def setup_selected_redshift_shaders():
    shaders = _selected_shaders()
    if not shaders:
        cmds.warning("Select one or more RedshiftMaterial shaders.")
        return

    for shader in shaders:
        print("Processing {}".format(shader))
        _set_fresnel_to_metalness(shader)

        diffuse_file, diffuse_attr = _file_node_from_shader(shader)
        diffuse_path = _texture_path(diffuse_file)
        if not diffuse_path:
            print("No diffuse file found on {}{}".format(shader, "." + diffuse_attr if diffuse_attr else ""))
            continue

        normal_path = _find_existing_texture(diffuse_path, NORMAL_TOKENS)
        spec_path = _find_existing_texture(diffuse_path, SPEC_TOKENS)

        if normal_path:
            _connect_normal_map(shader, diffuse_file, normal_path)
        else:
            print("Could not build a normal-map path from {}".format(diffuse_path))

        if spec_path:
            _connect_spec_map(shader, diffuse_file, spec_path)
        else:
            print("Could not build a spec-map path from {}".format(diffuse_path))


setup_selected_redshift_shaders()
