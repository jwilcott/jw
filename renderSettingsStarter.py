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
cmds.setAttr("defaultResolution.width", 1920)  # HD
cmds.setAttr("defaultResolution.height", 1080)  # HD

# Check if Camera exists and create if it doesn't
if not cmds.objExists("Camera"):
    cam = cmds.camera(
        name="Camera", 
        position=(0, 4, 16), 
        rotation=(0, 0, 0), 
        focalLength=35, 
        nearClipPlane=0.1, 
        farClipPlane=10000,
        displayResolution=True, 
        displayGateMask=True,
        overscan=1.3
    )[0]

    # Rename camera shape node to Camera
    cmds.rename(cam, "Camera")

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