import maya.cmds as cmds
import ngSkinTools2.api as ng_api

def flood_smooth_skin_weights():
    # Get the selected objects
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.warning("No objects selected. Please select one or more skinned objects.")
        return

    for obj in selection:
        try:
            # Get the NG Skin Tools layer data for the object
            layer_data = ng_api.LayerDataManager.getInstance().getLayerData(obj)
            if not layer_data:
                cmds.warning(f"No NG Skin Tools layer data found for {obj}. Skipping.")
                continue

            # Flood smooth weights
            ng_api.SmoothWeightsCommand(layer_data).execute()
            cmds.inViewMessage(amg=f"<hl>Smooth weights flooded for {obj}.</hl>", pos="topCenter", fade=True)
        except Exception as e:
            cmds.warning(f"Failed to smooth weights for {obj}: {e}")

