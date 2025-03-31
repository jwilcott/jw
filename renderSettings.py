#Set my favorite render settings for Redshift in Maya

import maya.cmds as cmds

# Render Settings
cmds.setAttr("redshiftOptions.imageFormat", 2)  # PNG
cmds.setAttr("defaultRenderGlobals.animation", 1)  # Enable Animation
cmds.setAttr("redshiftOptions.interactiveRenderingMode", 2)  # Buckets
cmds.setAttr("redshiftOptions.denoisingEnabled", 1)  # Denoise
cmds.setAttr("redshiftOptions.denoiseEngine", 3)  # OptiX
cmds.setAttr("redshiftOptions.secondaryGIEngine", 4)  # Brute Force GI
cmds.setAttr("redshiftOptions.bucketSize", 256)  # Big Buckets
cmds.setAttr("redshiftOptions.unifiedAdaptiveErrorThreshold", 1.0)  # Low Res
cmds.setAttr("defaultResolution.width", 1920)  # HD
cmds.setAttr("defaultResolution.height", 1080)  # HD

# Check if Camera exists and create if it doesn't
if not cmds.objExists("Camera"):
    cam = cmds.camera(
        name="Camera", 
        position=(0, 0, 10), 
        rotation=(0, 0, 0), 
        focalLength=35, 
        nearClipPlane=0.1, 
        farClipPlane=10000
    )[0]

print("Render settings applied successfully.")