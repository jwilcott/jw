#Open rendered sequence in DJV

import os
import re
import subprocess
import maya.cmds as cmds

def construct_render_path():
    """
    Construct the full render path based on Maya's render settings.

    :return: Full path to the rendered image.
    """
    # Retrieve the render output directory
    workspace_dir = cmds.workspace(q=True, rd=True)
    images_dir = cmds.workspace(fileRuleEntry="images")
    render_directory = os.path.join(workspace_dir, images_dir)

    # Retrieve the file name prefix, frame padding, and image format
    prefix = cmds.getAttr("defaultRenderGlobals.imageFilePrefix")
    frame_padding = cmds.getAttr("defaultRenderGlobals.extensionPadding")
    image_format = cmds.getAttr("defaultRenderGlobals.imageFormat")

    # Map image format codes to extensions
    extensions = {0: "iff", 1: "cin", 2: "tga", 3: "tif", 4: "sgi", 5: "als", 6: "iff", 7: "jpg", 8: "jpeg", 9: "eps", 10: "iff", 11: "iff", 12: "iff", 13: "bmp", 19: "png", 20: "qt", 21: "avi", 22: "mov", 23: "exr", 24: "dpx"}
    extension = extensions.get(image_format, "png")  # Default to "png" if format is unknown

    # Replace <scene> token with the current scene name
    scene_name = os.path.splitext(os.path.basename(cmds.file(q=True, sn=True)))[0]
    if "<scene>" in prefix:
        prefix = prefix.replace("<scene>", scene_name)

    # Helper for case-insensitive token replacement
    def _replace_token_ci(text, token, replacement):
        return re.sub(re.escape(token), replacement, text, flags=re.IGNORECASE)

    # Current render layer name (fallback to defaultRenderLayer if query fails)
    try:
        current_layer = cmds.editRenderLayerGlobals(q=True, currentRenderLayer=True)
    except Exception:
        current_layer = 'defaultRenderLayer'
    layer_name = current_layer.split('|')[-1] if current_layer else 'defaultRenderLayer'

    # Replace all <renderlayer> tokens (case-insensitive) in prefix
    if '<renderlayer>' in prefix.lower():
        prefix = _replace_token_ci(prefix, '<renderlayer>', layer_name)

    # Construct the full path
    frame_number = "0" * frame_padding  # Default frame number (e.g., "0000")
    full_path = os.path.join(render_directory, f"{prefix}.{frame_number}.{extension}")

    # Defensive: also replace <renderlayer> if it appears in constructed path
    if '<renderlayer>' in full_path.lower():
        full_path = _replace_token_ci(full_path, '<renderlayer>', layer_name)

    return full_path

def open_with_djv(image_path, djv_path="C:\\Program Files\\DJV2\\bin\\djv.exe"):
    """
    Open the specified image with DJV.

    :param image_path: Path to the image file.
    :param djv_path: Path to the DJV executable.
    """
    if not os.path.exists(djv_path):
        raise FileNotFoundError(f"DJV executable not found at {djv_path}")

    # Open the image with DJV
    subprocess.run([djv_path, image_path], check=True)

def main():
    # Construct the render path
    render_path = construct_render_path()
    print(f"Constructed render path: {render_path}")

    # Open the render path with DJV
    try:
        open_with_djv(render_path)
        print("Image opened successfully in DJV.")
    except Exception as e:
        print(f"Failed to open image with DJV: {e}")

if __name__ == "__main__":
    main()
