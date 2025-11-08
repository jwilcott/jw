#Open the file explorer to the directory containing the rendered image based on Maya's render settings.

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

    # Helper to replace tokens case-insensitively and everywhere
    def _replace_token_ci(text, token, replacement):
        return re.sub(re.escape(token), replacement, text, flags=re.IGNORECASE)

    # Compute current render layer name once
    current_layer = cmds.editRenderLayerGlobals(q=True, currentRenderLayer=True)
    layer_name = current_layer.split('|')[-1] if current_layer else "defaultRenderLayer"

    # Replace <renderlayer> in the prefix (all instances, case-insensitive)
    if "<renderlayer>".lower() in prefix.lower():
        prefix = _replace_token_ci(prefix, "<renderlayer>", layer_name)


    # Construct the full path
    frame_number = "0" * frame_padding  # Default frame number (e.g., "0000")
    full_path = os.path.join(render_directory, f"{prefix}.{frame_number}.{extension}")

    # Also replace <renderlayer> anywhere in the final file path (defensive, handles directory-level tokens)
    if "<renderlayer>".lower() in full_path.lower():
        full_path = _replace_token_ci(full_path, "<renderlayer>", layer_name)

    return full_path

def open_file_explorer_to_file(file_path):
    """
    Open a file explorer window at the directory containing the specified file.

    :param file_path: Full path to the file.
    """
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    subprocess.run(["explorer", os.path.normpath(directory)])

def main():
    # Construct the full render path
    render_path = construct_render_path()
    print(f"Constructed render path: {render_path}")

    # Open the file explorer window to the render path
    try:
        open_file_explorer_to_file(render_path)
        print("File explorer opened successfully to the render directory.")
    except Exception as e:
        print(f"Failed to open file explorer: {e}")

if __name__ == "__main__":
    main()
