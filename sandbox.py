import maya.cmds as cmds

def select_lowest_center_edge_loop():
    # Check if an edge is already selected
    selected_edges = cmds.filterExpand(selectionMask=32)
    if selected_edges:
        cmds.polySelectSp(loop=True)
        cmds.inViewMessage(amg="<hl>Using the selected edge loop for joint placement.</hl>", pos="topCenter", fade=True)
        place_joint_chain_on_edge_loop("Selected Edge Loop")
        return

    # Get the selected objects
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.warning("No objects selected. Please select one or more objects.")
        return

    for obj in selection:
        # Get the bounding box of the object
        bbox = cmds.exactWorldBoundingBox(obj)
        min_x, min_y, min_z, max_x, max_y, max_z = bbox

        # Calculate the center of the bounding box in the X and Z axes
        center_x = (min_x + max_x) / 2
        center_z = (min_z + max_z) / 2

        # Find the lowest Y value (min_y) and use it to locate the edges near this area
        # Convert the bounding box center to a point near the lowest part
        lowest_point = [center_x, min_y, center_z]

        # Select the object in component mode (edges)
        cmds.select(obj + ".e[*]", replace=True)

        # Find the closest edge loop to the lowest point
        edges = cmds.filterExpand(selectionMask=32)  # Get all edges
        closest_edge = None
        closest_distance = float("inf")

        for edge in edges:
            # Get the vertices of the edge
            verts = cmds.polyListComponentConversion(edge, toVertex=True)
            verts = cmds.filterExpand(verts, selectionMask=31)

            # Calculate the average position of the edge
            edge_center = [0, 0, 0]
            for vert in verts:
                pos = cmds.pointPosition(vert, world=True)
                edge_center[0] += pos[0]
                edge_center[1] += pos[1]
                edge_center[2] += pos[2]
            edge_center = [coord / len(verts) for coord in edge_center]

            # Calculate the distance to the lowest point
            distance = ((edge_center[0] - lowest_point[0]) ** 2 +
                        (edge_center[1] - lowest_point[1]) ** 2 +
                        (edge_center[2] - lowest_point[2]) ** 2) ** 0.5

            # Update the closest edge if this one is closer
            if distance < closest_distance:
                closest_distance = distance
                closest_edge = edge

        # Select the closest edge loop
        if closest_edge:
            cmds.select(closest_edge, replace=True)
            cmds.polySelectSp(loop=True)
            cmds.inViewMessage(amg=f"<hl>Center edge loop selected for {obj} near the lowest part of the bounding box.</hl>", pos="topCenter", fade=True)
            place_joint_chain_on_edge_loop(obj)
        else:
            cmds.warning(f"No edge loop found near the lowest part of the bounding box for {obj}.")

def place_joint_chain_on_edge_loop(obj_name):
    # Get the selected edge loop
    edge_loop = cmds.ls(selection=True, flatten=True)
    if not edge_loop:
        cmds.warning(f"No edge loop selected for {obj_name}. Please select an edge loop.")
        return

    # Convert the edge loop to vertices
    verts = cmds.polyListComponentConversion(edge_loop, toVertex=True)
    verts = cmds.filterExpand(verts, selectionMask=31)

    if not verts:
        cmds.warning(f"No vertices found in the edge loop for {obj_name}.")
        return

    # Get the positions of all vertices
    vert_positions = []
    for vert in verts:
        pos = cmds.pointPosition(vert, world=True)
        vert_positions.append((vert, pos))

    # Sort vertices by their Y position (ascending)
    vert_positions.sort(key=lambda v: v[1][1])

    # Place joints on every other vertex
    for i, (vert, pos) in enumerate(vert_positions):
        if i % 2 == 0:  # Every other vertex
            joint_name = cmds.joint(position=pos)
            cmds.inViewMessage(amg=f"<hl>Joint created: {joint_name} for {obj_name}</hl>", pos="topCenter", fade=True)

# Run the function
select_lowest_center_edge_loop()