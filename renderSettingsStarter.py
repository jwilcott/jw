#Set my favorite render settings for Redshift in Maya

import maya.cmds as cmds # type: ignore

# Set Maya's renderer to Redshift
cmds.setAttr("defaultRenderGlobals.currentRenderer", "redshift", type="string")

# Render Settings
cmds.setAttr("redshiftOptions.imageFormat", 2)  # PNG
cmds.setAttr("defaultRenderGlobals.animation", 1)  # Enable Animation
cmds.setAttr("defaultRenderGlobals.imageFilePrefix", "<scene>/<scene>", type="string")  # Add scene name prefix
cmds.setAttr("redshiftOptions.interactiveRenderingMode", 2)  # Buckets
cmds.setAttr("redshiftOptions.denoisingEnabled", 1)  # Denoise
cmds.setAttr("redshiftOptions.denoiseEngine", 3)  # OptiX
cmds.setAttr("redshiftOptions.GIEnabled", 1)  # Enable Global Illumination
cmds.setAttr("redshiftOptions.secondaryGIEngine", 4)  # Brute Force GI
cmds.setAttr("redshiftOptions.bucketSize", 256)  # Big Buckets
cmds.setAttr("redshiftOptions.unifiedAdaptiveErrorThreshold", 1.0)  # Low Res
cmds.setAttr("defaultResolution.width", 1920)  # Square
cmds.setAttr("defaultResolution.height", 1920)  # Square

# Uncheck any CPU device for Redshift (disable CPU rendering)
try:
    cmds.setAttr("redshiftOptions.enableCPURendering", 0)
except Exception:
    pass  # Attribute may not exist in all Redshift versions

# Check if Camera exists and create/import if it doesn't
if not cmds.objExists("Camera"):
    # Import the camera from the specified path
    camera_path = r"H:/Shared drives/Roblox Post Production/01 Assets/3D/Ref/Camera.ma"
    try:
        cmds.file(camera_path, i=True, ignoreVersion=True, mergeNamespacesOnClash=False, namespace=":")
        print(f"Imported camera from '{camera_path}'.")
    except Exception as e:
        cmds.warning(f"Failed to import camera from '{camera_path}': {e}")
    # Optionally, you can add logic here to set the imported camera as renderable, etc.
    # For example, disable persp camera renderable and set viewport to look through "Camera":
    if cmds.objExists("Camera"):
        camera_shape = cmds.listRelatives("Camera", shapes=True)[0]
        persp_camera_shape = cmds.listRelatives("persp", shapes=True)[0]
        cmds.setAttr(camera_shape + ".renderable", 1)
        cmds.setAttr(persp_camera_shape + ".renderable", 0)
        current_panel = cmds.getPanel(withFocus=True)
        if cmds.getPanel(typeOf=current_panel) == "modelPanel":
            cmds.lookThru(current_panel, "Camera")
            print(f"Set panel '{current_panel}' to look through 'Camera'.")
        else:
            model_panels = cmds.getPanel(type="modelPanel")
            visible_model_panels = [p for p in model_panels if cmds.modelEditor(p, query=True, visible=True)]
            if visible_model_panels:
                cmds.lookThru(visible_model_panels[0], "Camera")
                print(f"Set first visible model panel '{visible_model_panels[0]}' to look through 'Camera'.")
            else:
                cmds.warning("Could not find an active or visible model panel to set camera.")
else:
    # Get the shape node of the camera
    camera_shape = cmds.listRelatives("Camera", shapes=True)[0]
    persp_camera_shape = cmds.listRelatives("persp", shapes=True)[0]

    # Set the camera as renderable
    cmds.setAttr(camera_shape + ".renderable", 1)
    cmds.setAttr(persp_camera_shape + ".renderable", 0) # Disable persp camera

    # Set active viewport to look through the new camera
    current_panel = cmds.getPanel(withFocus=True)
    if cmds.getPanel(typeOf=current_panel) == "modelPanel":
        cmds.lookThru(current_panel, "Camera")
        print(f"Set panel '{current_panel}' to look through 'Camera'.")
    else:
        # Fallback if focus isn't on a model panel (e.g., script editor)
        # Try to find the first visible model panel
        model_panels = cmds.getPanel(type="modelPanel")
        visible_model_panels = [p for p in model_panels if cmds.modelEditor(p, query=True, visible=True)]
        if visible_model_panels:
            cmds.lookThru(visible_model_panels[0], "Camera")
            print(f"Set first visible model panel '{visible_model_panels[0]}' to look through 'Camera'.")
        else:
             cmds.warning("Could not find an active or visible model panel to set camera.")


print("Render settings applied successfully.")