#exec(open(r"c:\Users\jwilc\Documents\maya\scripts\jw\renderSettings.py").read()); renderSettings("high")
# Example usage:
# renderSettings("high")  # Full resolution
# renderSettings("low")   # Half resolution

import maya.cmds as cmds

def renderSettings(quality="high"):
    # Determine the scale factor and threshold based on the quality
    if quality == "high":
        scale_factor = 2  # Full resolution
        threshold = 0.1  # Set threshold to 0.1 for high quality
        message = "High quality render settings applied."
    elif quality == "low":
        scale_factor = 0.5  # Half resolution
        threshold = 1  # Set threshold to 1 for low quality
        message = "Low quality render settings applied."
    else:
        raise ValueError("Invalid quality setting. Please use 'high' or 'low'.")

    # Get current render width and height
    render_width = cmds.getAttr("defaultResolution.width")
    render_height = cmds.getAttr("defaultResolution.height")

    # Adjust width and height based on the scale factor
    new_width = render_width * scale_factor
    new_height = render_height * scale_factor

    # Set render settings to the new size
    cmds.setAttr("defaultResolution.width", new_width)
    cmds.setAttr("defaultResolution.height", new_height)

    # Set sampling threshold
    cmds.setAttr("redshiftOptions.unifiedAdaptiveErrorThreshold", threshold)

    # Print message to the viewport
    cmds.inViewMessage(amg=f"<hl>{message}</hl>", pos="topCenter", fade=True)

