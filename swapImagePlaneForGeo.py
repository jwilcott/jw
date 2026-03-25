import maya.cmds as cmds  # type: ignore


MM_PER_INCH = 25.4
FIT_FILL = 0
FIT_BEST = 1
FIT_HORIZONTAL = 2
FIT_VERTICAL = 3
FIT_TO_SIZE = 4


def _short_name(node_name):
    return node_name.split("|")[-1].split(":")[-1]


def _make_unique_name(base_name):
    if not cmds.objExists(base_name):
        return base_name

    index = 1
    while cmds.objExists("{}_{}".format(base_name, index)):
        index += 1
    return "{}_{}".format(base_name, index)


def _ensure_redshift():
    for plugin_name in ("redshift4maya", "redshift4maya.mll"):
        try:
            if not cmds.pluginInfo(plugin_name, query=True, loaded=True):
                cmds.loadPlugin(plugin_name)
            return True
        except Exception:
            continue

    cmds.warning("Could not load Redshift for Maya.")
    return False


def _list_selected_image_plane_shapes():
    selection = cmds.ls(selection=True, long=True) or []
    image_plane_shapes = []

    for node in selection:
        node_type = cmds.nodeType(node)

        if node_type == "imagePlane":
            image_plane_shapes.append(node)
            continue

        if node_type == "transform":
            shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.nodeType(shape) == "imagePlane":
                    image_plane_shapes.append(shape)

    ordered = []
    seen = set()
    for shape in image_plane_shapes:
        if shape not in seen:
            ordered.append(shape)
            seen.add(shape)
    return ordered


def _get_attached_camera(image_plane_shape):
    image_plane_transform = cmds.listRelatives(image_plane_shape, parent=True, fullPath=True) or []
    if not image_plane_transform:
        raise RuntimeError("Could not find transform for image plane {}.".format(image_plane_shape))

    camera_shape = cmds.listRelatives(image_plane_transform[0], parent=True, fullPath=True) or []
    if not camera_shape or cmds.nodeType(camera_shape[0]) != "camera":
        raise RuntimeError(
            "Image plane {} is not attached to a camera shape.".format(_short_name(image_plane_shape))
        )

    camera_transform = cmds.listRelatives(camera_shape[0], parent=True, fullPath=True) or []
    if not camera_transform:
        raise RuntimeError("Could not find camera transform for {}.".format(camera_shape[0]))

    return image_plane_transform[0], camera_shape[0], camera_transform[0]


def _get_attr(node, attr_name, default_value=None):
    if not cmds.attributeQuery(attr_name, node=node, exists=True):
        return default_value
    return cmds.getAttr("{}.{}".format(node, attr_name))


def _safe_image_size(image_plane_shape):
    try:
        image_size = cmds.imagePlane(image_plane_shape, query=True, imageSize=True)
        if image_size and len(image_size) == 2 and image_size[0] > 0 and image_size[1] > 0:
            return float(image_size[0]), float(image_size[1])
    except Exception:
        pass
    return None


def _aperture_to_world(depth_value, aperture_inches, focal_length_mm):
    if abs(focal_length_mm) < 0.000001:
        raise RuntimeError("Camera focal length is zero, cannot compute image plane size.")
    return depth_value * ((aperture_inches * MM_PER_INCH) / focal_length_mm)


def _compute_visible_plane(image_plane_shape, camera_shape):
    depth_value = float(_get_attr(image_plane_shape, "depth", 100.0))
    offset_x = float(_get_attr(image_plane_shape, "offsetX", 0.0))
    offset_y = float(_get_attr(image_plane_shape, "offsetY", 0.0))
    rotate_value = float(_get_attr(image_plane_shape, "rotate", 0.0))
    size_x = float(_get_attr(image_plane_shape, "sizeX", 1.0))
    size_y = float(_get_attr(image_plane_shape, "sizeY", 1.0))
    fit_value = int(_get_attr(image_plane_shape, "fit", FIT_BEST))
    maintain_ratio = bool(_get_attr(image_plane_shape, "maintainRatio", True))
    squeeze_correction = float(_get_attr(image_plane_shape, "squeezeCorrection", 1.0) or 1.0)
    focal_length_mm = float(cmds.getAttr(camera_shape + ".focalLength"))

    base_width = _aperture_to_world(depth_value, size_x, focal_length_mm)
    base_height = _aperture_to_world(depth_value, size_y, focal_length_mm)
    center_x = _aperture_to_world(depth_value, offset_x, focal_length_mm)
    center_y = _aperture_to_world(depth_value, offset_y, focal_length_mm)

    image_size = _safe_image_size(image_plane_shape)
    if not image_size or not maintain_ratio:
        return {
            "center_x": center_x,
            "center_y": center_y,
            "depth": depth_value,
            "rotate": rotate_value,
            "width": base_width,
            "height": base_height,
            "crop_u": 1.0,
            "crop_v": 1.0,
            "image_width": None,
            "image_height": None,
        }

    image_width, image_height = image_size
    effective_aspect = (image_width / image_height) / squeeze_correction if squeeze_correction else (image_width / image_height)

    if effective_aspect <= 0.0:
        effective_aspect = base_width / base_height

    if fit_value == FIT_TO_SIZE:
        scaled_width = base_width
        scaled_height = base_height
    elif fit_value == FIT_FILL:
        scale_value = max(base_width / effective_aspect, base_height)
        scaled_width = effective_aspect * scale_value
        scaled_height = scale_value
    elif fit_value == FIT_HORIZONTAL:
        scaled_width = base_width
        scaled_height = base_width / effective_aspect
    elif fit_value == FIT_VERTICAL:
        scaled_width = effective_aspect * base_height
        scaled_height = base_height
    else:
        scale_value = min(base_width / effective_aspect, base_height)
        scaled_width = effective_aspect * scale_value
        scaled_height = scale_value

    visible_width = min(scaled_width, base_width)
    visible_height = min(scaled_height, base_height)
    crop_u = visible_width / scaled_width if scaled_width > 0.0 else 1.0
    crop_v = visible_height / scaled_height if scaled_height > 0.0 else 1.0

    return {
        "center_x": center_x,
        "center_y": center_y,
        "depth": depth_value,
        "rotate": rotate_value,
        "width": visible_width,
        "height": visible_height,
        "crop_u": crop_u,
        "crop_v": crop_v,
        "image_width": image_width,
        "image_height": image_height,
    }


def _compute_place2d_settings(image_plane_shape, visible_plane):
    coverage_u = 1.0
    coverage_v = 1.0
    translate_u = 0.0
    translate_v = 0.0
    image_width = visible_plane["image_width"]
    image_height = visible_plane["image_height"]

    if image_width and image_width > 0.0:
        coverage_x = int(_get_attr(image_plane_shape, "coverageX", 0))
        origin_x = int(_get_attr(image_plane_shape, "coverageOriginX", 0))
        if coverage_x > 0:
            coverage_u = min(max(float(coverage_x) / image_width, 0.0), 1.0)
            translate_u = min(max(float(origin_x) / image_width, 0.0), 1.0)

    if image_height and image_height > 0.0:
        coverage_y = int(_get_attr(image_plane_shape, "coverageY", 0))
        origin_y = int(_get_attr(image_plane_shape, "coverageOriginY", 0))
        if coverage_y > 0:
            coverage_v = min(max(float(coverage_y) / image_height, 0.0), 1.0)
            translate_v = min(max(float(origin_y) / image_height, 0.0), 1.0)

    final_coverage_u = coverage_u * visible_plane["crop_u"]
    final_coverage_v = coverage_v * visible_plane["crop_v"]
    final_translate_u = translate_u + (coverage_u * (1.0 - visible_plane["crop_u"]) * 0.5)
    final_translate_v = translate_v + (coverage_v * (1.0 - visible_plane["crop_v"]) * 0.5)

    return {
        "coverage_u": final_coverage_u,
        "coverage_v": final_coverage_v,
        "translate_u": final_translate_u,
        "translate_v": final_translate_v,
        "repeat_u": float(_get_attr(image_plane_shape, "squeezeCorrection", 1.0) or 1.0),
    }


def _create_render_plane(base_name, visible_plane, camera_transform):
    group_name = _make_unique_name("{}_render_GRP".format(base_name))
    plane_name = _make_unique_name("{}_render_GEO".format(base_name))

    group = cmds.createNode("transform", name=group_name)
    cmds.delete(cmds.parentConstraint(camera_transform, group, maintainOffset=False))
    constraint = cmds.parentConstraint(
        camera_transform,
        group,
        maintainOffset=False,
        name=_make_unique_name("{}_parentConstraint".format(group_name)),
    )[0]

    plane_transform, _ = cmds.polyPlane(
        width=visible_plane["width"],
        height=visible_plane["height"],
        subdivisionsX=1,
        subdivisionsY=1,
        axis=(0, 0, 1),
        name=plane_name,
    )
    cmds.parent(plane_transform, group)
    plane_shape = (cmds.listRelatives(plane_transform, shapes=True, fullPath=True) or [None])[0]

    cmds.setAttr(plane_transform + ".translateX", visible_plane["center_x"])
    cmds.setAttr(plane_transform + ".translateY", visible_plane["center_y"])
    cmds.setAttr(plane_transform + ".translateZ", -visible_plane["depth"])
    cmds.setAttr(plane_transform + ".rotateZ", -visible_plane["rotate"])

    for axis in ("X", "Y", "Z"):
        source_attr = "{}.scale{}".format(camera_transform, axis)
        target_attr = "{}.scale{}".format(group, axis)
        if not cmds.isConnected(source_attr, target_attr):
            cmds.connectAttr(source_attr, target_attr, force=True)

    return {
        "group": group,
        "constraint": constraint,
        "transform": plane_transform,
        "shape": plane_shape,
    }


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
        source_plug = "{}.{}".format(place2d_node, source_attr)
        target_plug = "{}.{}".format(file_node, target_attr)
        if not cmds.isConnected(source_plug, target_plug):
            cmds.connectAttr(source_plug, target_plug, force=True)


def _copy_value_or_connection(source_plug, target_plug):
    incoming = cmds.listConnections(source_plug, source=True, destination=False, plugs=True) or []
    if incoming:
        if not cmds.isConnected(incoming[0], target_plug):
            cmds.connectAttr(incoming[0], target_plug, force=True)
        return

    value = cmds.getAttr(source_plug)
    if isinstance(value, list) and len(value) == 1:
        value = value[0]

    if isinstance(value, tuple):
        cmds.setAttr(target_plug, *value, type="double3")
    else:
        cmds.setAttr(target_plug, value)


def _build_redshift_network(base_name, image_plane_shape, visible_plane):
    material_name = _make_unique_name("{}_RS_MTL".format(base_name))
    shading_group_name = _make_unique_name("{}SG".format(material_name))
    file_name = _make_unique_name("{}_plate_file".format(base_name))
    place2d_name = _make_unique_name("{}_plate_place2d".format(base_name))

    material = cmds.shadingNode("RedshiftMaterial", asShader=True, name=material_name)
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group_name)
    file_node = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name=file_name)
    place2d = cmds.shadingNode("place2dTexture", asUtility=True, name=place2d_name)

    _connect_place2d_to_file(place2d, file_node)

    settings = _compute_place2d_settings(image_plane_shape, visible_plane)
    cmds.setAttr(place2d + ".coverageU", settings["coverage_u"])
    cmds.setAttr(place2d + ".coverageV", settings["coverage_v"])
    cmds.setAttr(place2d + ".translateFrameU", settings["translate_u"])
    cmds.setAttr(place2d + ".translateFrameV", settings["translate_v"])
    cmds.setAttr(place2d + ".repeatU", settings["repeat_u"])
    cmds.setAttr(place2d + ".repeatV", 1.0)

    image_name = _get_attr(image_plane_shape, "imageName", "")
    if image_name:
        cmds.setAttr(file_node + ".fileTextureName", image_name, type="string")

    if cmds.attributeQuery("colorSpace", node=image_plane_shape, exists=True):
        color_space = cmds.getAttr(image_plane_shape + ".colorSpace")
        if color_space and cmds.attributeQuery("colorSpace", node=file_node, exists=True):
            cmds.setAttr(file_node + ".colorSpace", color_space, type="string")

    if cmds.attributeQuery("useFrameExtension", node=image_plane_shape, exists=True):
        cmds.setAttr(file_node + ".useFrameExtension", cmds.getAttr(image_plane_shape + ".useFrameExtension"))

    if cmds.attributeQuery("frameOffset", node=image_plane_shape, exists=True):
        _copy_value_or_connection(image_plane_shape + ".frameOffset", file_node + ".frameOffset")

    if cmds.attributeQuery("frameExtension", node=image_plane_shape, exists=True):
        _copy_value_or_connection(image_plane_shape + ".frameExtension", file_node + ".frameExtension")

    if cmds.attributeQuery("frameCache", node=image_plane_shape, exists=True) and cmds.attributeQuery("useCache", node=file_node, exists=True):
        frame_cache = int(cmds.getAttr(image_plane_shape + ".frameCache"))
        cmds.setAttr(file_node + ".useCache", frame_cache > 0)
        if not cmds.attributeQuery("sourceImagePlaneFrameCache", node=file_node, exists=True):
            cmds.addAttr(
                file_node,
                longName="sourceImagePlaneFrameCache",
                attributeType="long",
                keyable=True,
            )
        cmds.setAttr(file_node + ".sourceImagePlaneFrameCache", frame_cache)

    cmds.connectAttr(file_node + ".outColor", material + ".diffuse_color", force=True)
    cmds.connectAttr(file_node + ".outColor", material + ".emission_color", force=True)
    cmds.connectAttr(material + ".outColor", shading_group + ".surfaceShader", force=True)

    if cmds.attributeQuery("emission_weight", node=material, exists=True):
        cmds.setAttr(material + ".emission_weight", 1.0)
    if cmds.attributeQuery("refl_weight", node=material, exists=True):
        cmds.setAttr(material + ".refl_weight", 0.0)
    if cmds.attributeQuery("refl_color", node=material, exists=True):
        cmds.setAttr(material + ".refl_color", 0.0, 0.0, 0.0, type="double3")

    return {
        "material": material,
        "shading_group": shading_group,
        "file": file_node,
        "place2d": place2d,
    }


def _assign_shader(shape_node, shading_group):
    cmds.sets(shape_node, edit=True, forceElement=shading_group)


def swap_image_plane_for_geo():
    if not _ensure_redshift():
        return

    image_plane_shapes = _list_selected_image_plane_shapes()
    if not image_plane_shapes:
        cmds.warning("Select one or more imagePlane nodes or their transforms.")
        return

    created_geo = []

    for image_plane_shape in image_plane_shapes:
        try:
            image_plane_transform, camera_shape, camera_transform = _get_attached_camera(image_plane_shape)
            base_name = _short_name(image_plane_transform)
            visible_plane = _compute_visible_plane(image_plane_shape, camera_shape)
            render_plane = _create_render_plane(base_name, visible_plane, camera_transform)
            network = _build_redshift_network(base_name, image_plane_shape, visible_plane)
            _assign_shader(render_plane["shape"], network["shading_group"])
            created_geo.append(render_plane["transform"])
            print(
                "Created {} from {} and constrained it to {}.".format(
                    render_plane["transform"],
                    image_plane_shape,
                    camera_transform,
                )
            )
        except Exception as exc:
            cmds.warning("Failed to convert {}: {}".format(image_plane_shape, exc))

    if created_geo:
        cmds.select(created_geo, replace=True)


swap_image_plane_for_geo()
