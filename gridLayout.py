# layout selected objects in a grid along XY axis
import maya.cmds as cmds
import math

def layout_grid():
    sel = cmds.ls(selection=True)
    if not sel:
        cmds.warning("No objects selected.")
        return

    count = len(sel)
    cols = int(math.ceil(math.sqrt(count)))
    rows = int(math.ceil(float(count) / cols))

    # Duplicate objects and group them
    dup_objs = cmds.duplicate(sel, rr=True)
    layout_grp = cmds.group(dup_objs, name="layout")

    # Get bounding boxes for all duplicated objects
    bboxes = [cmds.exactWorldBoundingBox(obj) for obj in dup_objs]
    widths = [bbox[3] - bbox[0] for bbox in bboxes]
    heights = [bbox[4] - bbox[1] for bbox in bboxes]

    # Find max width and height for spacing
    max_width = max(widths)
    max_height = max(heights)

    # Calculate grid positions
    positions = []
    for idx, obj in enumerate(dup_objs):
        row = idx // cols
        col = idx % cols
        x = col * max_width
        y = row * max_height
        positions.append((x, y, 0))

    # Center the grid at world 0,0,0
    min_x = min(pos[0] for pos in positions)
    max_x = max(pos[0] for pos in positions)
    min_y = min(pos[1] for pos in positions)
    max_y = max(pos[1] for pos in positions)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    for obj, pos in zip(dup_objs, positions):
        cmds.xform(obj, ws=True, t=(pos[0] - center_x, pos[1] - center_y, 0))

    # Move the group to world 0,0,0
    cmds.xform(layout_grp, ws=True, t=(0, 0, 0))

layout_grid()


