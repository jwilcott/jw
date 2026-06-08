# Create a Redshift FX card from a selected PNG sequence.

import os
import re

import maya.cmds as cmds  # type: ignore


PNG_SEQUENCE_PATTERN = re.compile(r"^(.*?)(\d+)(\.png)$", re.IGNORECASE)

DIFFUSE_ATTRS = ["base_color", "baseColor", "diffuse_color", "diffuseColor", "color"]
EMISSION_COLOR_ATTRS = ["emission_color", "emissionColor"]
EMISSION_WEIGHT_ATTRS = ["emission_weight", "emissionWeight"]
OPACITY_ATTRS = ["opacity_color", "opacityColor", "opacity", "transparency"]


def _safe_name(name):
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    cleaned = cleaned.strip("_") or "fx_card"
    if cleaned[0].isdigit():
        cleaned = "_" + cleaned
    return cleaned


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
        cmds.connectAttr(source_attr, destination_attr, force=True)
        return True
    except Exception as exc:
        print("Could not connect {} to {}: {}".format(source_attr, destination_attr, exc))
        return False


def _connect_alpha_to_attr(file_node, material, attr):
    destination = "{}.{}".format(material, attr)
    children = cmds.attributeQuery(attr, node=material, listChildren=True) or []

    if children:
        connected = False
        for child in children:
            connected = _connect(file_node + ".outAlpha", "{}.{}".format(material, child)) or connected
        return connected

    return _connect(file_node + ".outAlpha", destination)


def _connect_place2d_to_file(place2d_node, file_node):
    connections = (
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
        ("outUV", "uvCoord"),
        ("outUvFilterSize", "uvFilterSize"),
    )

    for source_attr, target_attr in connections:
        if _has_attr(place2d_node, source_attr) and _has_attr(file_node, target_attr):
            _connect(
                "{}.{}".format(place2d_node, source_attr),
                "{}.{}".format(file_node, target_attr),
            )


def _set_attr_if_exists(node, attr, value):
    if not _has_attr(node, attr):
        return False

    cmds.setAttr("{}.{}".format(node, attr), value)
    return True


def _choose_png_sequence_file():
    paths = cmds.fileDialog2(
        caption="Choose PNG Sequence Frame",
        fileFilter="PNG files (*.png)",
        fileMode=1,
        dialogStyle=2,
    )
    if not paths:
        return None
    return paths[0]


def _sequence_info(path):
    folder, filename = os.path.split(path)
    match = PNG_SEQUENCE_PATTERN.match(filename)
    if not match:
        cmds.error("Choose a PNG with trailing frame digits, like fx_name.0001.png.")
        return None

    prefix, frame_text, extension = match.groups()
    padding = len(frame_text)
    base_name = _safe_name(prefix.rstrip("._- ") or os.path.splitext(filename)[0])

    frame_pattern = re.compile(
        r"^{}(\d{{{}}}){}$".format(
            re.escape(prefix),
            padding,
            re.escape(extension),
        ),
        re.IGNORECASE,
    )

    frames = []
    for entry in os.listdir(folder):
        entry_match = frame_pattern.match(entry)
        if entry_match:
            frames.append(int(entry_match.group(1)))

    frames = sorted(set(frames))
    if not frames:
        frames = [int(frame_text)]

    return {
        "folder": folder,
        "path": path,
        "base_name": base_name,
        "first_frame": frames[0],
        "last_frame": frames[-1],
        "sequence_length": len(frames),
        "padding": padding,
        "has_gaps": len(frames) != (frames[-1] - frames[0] + 1),
    }


def _create_redshift_material(base_name):
    material_name = _make_unique_name(base_name + "_MTL")
    viewport_material_name = _make_unique_name(base_name + "_Viewport_MTL")
    shading_group_name = _make_unique_name(material_name + "SG")

    material = cmds.shadingNode("RedshiftMaterial", asShader=True, name=material_name)
    viewport_material = cmds.shadingNode("lambert", asShader=True, name=viewport_material_name)
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group_name)
    _connect(viewport_material + ".outColor", shading_group + ".surfaceShader")

    if _has_attr(shading_group, "rsSurfaceShader"):
        _connect(material + ".outColor", shading_group + ".rsSurfaceShader")
    else:
        cmds.warning(
            "{} has no rsSurfaceShader attr. Redshift may render the viewport Lambert instead.".format(
                shading_group
            )
        )

    emission_weight_attr = _first_existing_attr(material, EMISSION_WEIGHT_ATTRS)
    if emission_weight_attr:
        cmds.setAttr("{}.{}".format(material, emission_weight_attr), 1.0)

    if _has_attr(material, "refl_weight"):
        cmds.setAttr(material + ".refl_weight", 0.0)

    return material, viewport_material, shading_group


def _configure_interactive_sequence_cache(file_node, sequence_info):
    start_frame = int(sequence_info["first_frame"])
    end_frame = int(sequence_info["last_frame"])

    _set_attr_if_exists(file_node, "useHardwareTextureCycling", 1)
    _set_attr_if_exists(file_node, "startCycleExtension", start_frame)
    _set_attr_if_exists(file_node, "endCycleExtension", end_frame)
    _set_attr_if_exists(file_node, "byCycleIncrement", 1)


def _create_loop_expression(file_node, sequence_info):
    expr_name = _make_unique_name(sequence_info["base_name"] + "_frameLoop_EXP")
    scene_start_frame = int(cmds.playbackOptions(query=True, minTime=True))
    start_frame = int(sequence_info["first_frame"])
    sequence_length = int(sequence_info["sequence_length"])

    expression = "{file_node}.frameExtension = ((frame - {scene_start}) % {length}) + {start};".format(
        file_node=file_node,
        scene_start=scene_start_frame,
        start=start_frame,
        length=sequence_length,
    )

    return cmds.expression(
        name=expr_name,
        string=expression,
        object=file_node,
        alwaysEvaluate=True,
        unitConversion="all",
    )


def make_fx_card():
    selected_path = _choose_png_sequence_file()
    if not selected_path:
        return

    sequence = _sequence_info(selected_path)
    if not sequence:
        return

    base_name = sequence["base_name"]
    plane_name = _make_unique_name(base_name + "_geo")
    file_name = _make_unique_name(base_name + "_FILE")
    place2d_name = _make_unique_name(base_name + "_place2d")

    plane_transform, plane_shape = cmds.polyPlane(
        width=1,
        height=1,
        subdivisionsX=1,
        subdivisionsY=1,
        name=plane_name,
    )
    cmds.setAttr(plane_transform + ".scaleX", 20)
    cmds.setAttr(plane_transform + ".scaleY", 20)
    cmds.setAttr(plane_transform + ".scaleZ", 20)
    cmds.setAttr(plane_transform + ".rotateX", 90)
    cmds.makeIdentity(plane_transform, apply=True, translate=False, rotate=True, scale=True)

    material, viewport_material, shading_group = _create_redshift_material(base_name)
    file_node = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name=file_name)
    place2d = cmds.shadingNode("place2dTexture", asUtility=True, name=place2d_name)

    _connect_place2d_to_file(place2d, file_node)

    cmds.setAttr(file_node + ".fileTextureName", sequence["path"], type="string")
    if _has_attr(file_node, "useFrameExtension"):
        cmds.setAttr(file_node + ".useFrameExtension", 1)
    _configure_interactive_sequence_cache(file_node, sequence)

    if _has_attr(file_node, "colorSpace"):
        try:
            cmds.setAttr(file_node + ".colorSpace", "sRGB", type="string")
        except Exception:
            pass

    diffuse_attr = _first_existing_attr(material, DIFFUSE_ATTRS)
    emission_color_attr = _first_existing_attr(material, EMISSION_COLOR_ATTRS)
    opacity_attr = _first_existing_attr(material, OPACITY_ATTRS)

    if diffuse_attr:
        _connect(file_node + ".outColor", "{}.{}".format(material, diffuse_attr))
    else:
        cmds.warning("Could not find a diffuse/base color attr on {}.".format(material))

    _connect(file_node + ".outColor", viewport_material + ".color")

    if emission_color_attr:
        _connect(file_node + ".outColor", "{}.{}".format(material, emission_color_attr))
    else:
        cmds.warning("Could not find an emission color attr on {}.".format(material))

    if opacity_attr:
        _connect_alpha_to_attr(file_node, material, opacity_attr)
    else:
        cmds.warning("Could not find an opacity attr on {}.".format(material))

    if _has_attr(file_node, "outTransparency") and _has_attr(viewport_material, "transparency"):
        _connect(file_node + ".outTransparency", viewport_material + ".transparency")
    else:
        cmds.warning("Could not connect viewport alpha on {}.".format(viewport_material))

    cmds.sets(plane_transform, edit=True, forceElement=shading_group)
    expression = _create_loop_expression(file_node, sequence)

    cmds.select(plane_transform, replace=True)

    if sequence["has_gaps"]:
        cmds.warning(
            "Sequence has missing frame numbers. The modulo loop uses the detected length, "
            "so missing files may show as blank frames."
        )

    print(
        "Created FX card: {}, {}, {}, {} frames, loop expression {}".format(
            plane_transform,
            material,
            file_node,
            sequence["sequence_length"],
            expression,
        )
    )


make_fx_card()
