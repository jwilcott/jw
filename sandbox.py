"""
Maya mesh liquid-volume calculator.

Select one or more closed polygon meshes and run this file in Maya's Script
Editor, or import it and call calculate_selected_mesh_volumes().

The math uses each mesh triangle as the base of a tetrahedron to the world
origin. For best results the mesh should be closed, manifold, and have
consistent face normals.
"""

from __future__ import print_function

from maya import cmds
from maya.api import OpenMaya as om


UNIT_TO_METERS = {
    "mm": 0.001,
    "millimeter": 0.001,
    "cm": 0.01,
    "centimeter": 0.01,
    "m": 1.0,
    "meter": 1.0,
    "km": 1000.0,
    "kilometer": 1000.0,
    "in": 0.0254,
    "inch": 0.0254,
    "ft": 0.3048,
    "foot": 0.3048,
    "yd": 0.9144,
    "yard": 0.9144,
    "mi": 1609.344,
    "mile": 1609.344,
}

LITERS_PER_CUBIC_METER = 1000.0
US_GALLONS_PER_LITER = 0.2641720524


def _mesh_shapes_from_selection():
    """Return selected non-intermediate mesh shape paths."""
    meshes = []
    selected = cmds.ls(selection=True, long=True) or []

    for item in selected:
        if cmds.nodeType(item) == "mesh":
            shapes = [item]
        else:
            shapes = cmds.listRelatives(
                item,
                shapes=True,
                noIntermediate=True,
                fullPath=True,
                type="mesh",
            ) or []

        for shape in shapes:
            if shape not in meshes:
                meshes.append(shape)

    return meshes


def _dag_path(node):
    selection = om.MSelectionList()
    selection.add(node)
    return selection.getDagPath(0)


def _scene_unit_to_meters():
    unit = cmds.currentUnit(query=True, linear=True)
    try:
        return UNIT_TO_METERS[unit]
    except KeyError:
        raise RuntimeError("Unsupported Maya linear unit: {0}".format(unit))


def mesh_volume_cubic_scene_units(mesh_shape):
    """
    Calculate the signed-then-absolute volume of a mesh in cubic Maya scene units.

    Args:
        mesh_shape (str): Mesh shape or transform name.

    Returns:
        float: Mesh volume in cubic current scene units.
    """
    dag = _dag_path(mesh_shape)

    if dag.apiType() == om.MFn.kTransform:
        dag.extendToShape()

    mesh_fn = om.MFnMesh(dag)
    points = mesh_fn.getPoints(om.MSpace.kWorld)
    triangle_counts, triangle_vertices = mesh_fn.getTriangles()

    signed_volume = 0.0
    cursor = 0

    for triangle_count in triangle_counts:
        for _ in range(triangle_count):
            p0 = points[triangle_vertices[cursor]]
            p1 = points[triangle_vertices[cursor + 1]]
            p2 = points[triangle_vertices[cursor + 2]]
            cursor += 3

            v0 = om.MVector(p0.x, p0.y, p0.z)
            v1 = om.MVector(p1.x, p1.y, p1.z)
            v2 = om.MVector(p2.x, p2.y, p2.z)

            signed_volume += v0 * (v1 ^ v2) / 6.0

    return abs(signed_volume)


def convert_cubic_scene_units_to_liquid(volume_cubic_scene_units):
    """
    Convert cubic Maya scene units to common liquid volume units.

    Returns:
        dict: cubic_scene_units, cubic_meters, liters, milliliters, us_gallons.
    """
    meters_per_unit = _scene_unit_to_meters()
    cubic_meters = volume_cubic_scene_units * (meters_per_unit ** 3)
    liters = cubic_meters * LITERS_PER_CUBIC_METER

    return {
        "cubic_scene_units": volume_cubic_scene_units,
        "cubic_meters": cubic_meters,
        "liters": liters,
        "milliliters": liters * 1000.0,
        "us_gallons": liters * US_GALLONS_PER_LITER,
    }


def mesh_liquid_volume(mesh_shape):
    """Return volume information for one mesh shape or transform."""
    volume = mesh_volume_cubic_scene_units(mesh_shape)
    result = convert_cubic_scene_units_to_liquid(volume)
    result["mesh"] = mesh_shape
    result["linear_unit"] = cmds.currentUnit(query=True, linear=True)
    return result


def calculate_selected_mesh_volumes(print_results=True):
    """
    Calculate liquid volume for every selected mesh.

    Args:
        print_results (bool): Print a formatted report to the Script Editor.

    Returns:
        list[dict]: One volume report per selected mesh.
    """
    meshes = _mesh_shapes_from_selection()
    if not meshes:
        cmds.warning("Select one or more polygon meshes.")
        return []

    results = [mesh_liquid_volume(mesh) for mesh in meshes]

    if print_results:
        unit = cmds.currentUnit(query=True, linear=True)
        print("\nMesh liquid volume ({0} scene units):".format(unit))

        for result in results:
            print(
                "{mesh}: {cubic_scene_units:.6f} {unit}^3 | "
                "{liters:.6f} L | {us_gallons:.6f} US gal".format(
                    unit=unit,
                    **result
                )
            )

        if len(results) > 1:
            total_cubic_units = sum(r["cubic_scene_units"] for r in results)
            total = convert_cubic_scene_units_to_liquid(total_cubic_units)
            print(
                "TOTAL: {cubic_scene_units:.6f} {unit}^3 | "
                "{liters:.6f} L | {us_gallons:.6f} US gal".format(
                    unit=unit,
                    **total
                )
            )

    return results


# Auto-run for the way these Maya utility scripts are usually launched:
# exec(open(r"c:\Users\jwilc\Documents\maya\scripts\jw\sandbox.py").read())
calculate_selected_mesh_volumes()
