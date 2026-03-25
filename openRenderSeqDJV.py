# Open rendered sequence in DJV

import os
import re
import subprocess

import maya.cmds as cmds


def show_viewport_message(message):
    try:
        cmds.inViewMessage(
            statusMessage=message,
            pos="midCenterTop",
            fade=True,
            alpha=0.9,
        )
    except Exception:
        print(message)


def replace_token_ci(text, token, replacement):
    return re.sub(re.escape(token), replacement, text, flags=re.IGNORECASE)


def normalize_prefix(prefix):
    if not prefix:
        return ""
    return prefix.replace("\\", "/").strip("/")


def resolve_render_tokens(path_value):
    if not path_value:
        return ""

    resolved_value = path_value
    scene_name = os.path.splitext(os.path.basename(cmds.file(q=True, sn=True)))[0]
    if "<scene>" in resolved_value.lower():
        resolved_value = replace_token_ci(resolved_value, "<scene>", scene_name)

    try:
        current_layer = cmds.editRenderLayerGlobals(q=True, currentRenderLayer=True)
    except Exception:
        current_layer = "defaultRenderLayer"

    layer_name = current_layer.split("|")[-1] if current_layer else "defaultRenderLayer"
    if "<renderlayer>" in resolved_value.lower():
        resolved_value = replace_token_ci(resolved_value, "<renderlayer>", layer_name)

    return resolved_value


def get_image_extension(image_format):
    extensions = {
        0: "iff",
        1: "cin",
        2: "tga",
        3: "tif",
        4: "sgi",
        5: "als",
        6: "iff",
        7: "jpg",
        8: "jpeg",
        9: "eps",
        10: "iff",
        11: "iff",
        12: "iff",
        13: "bmp",
        19: "png",
        20: "qt",
        21: "avi",
        22: "mov",
        23: "exr",
        24: "dpx",
        32: "exr",
    }
    return extensions.get(image_format, "png")


def get_sequence_search_root(render_dir, raw_prefix, resolved_prefix):
    raw_prefix_dir = os.path.dirname(raw_prefix or "")
    resolved_prefix_dir = os.path.dirname(resolved_prefix or "")

    raw_parts = [part for part in raw_prefix_dir.split("/") if part]
    resolved_parts = [part for part in resolved_prefix_dir.split("/") if part]

    stable_parts = []
    for index, raw_part in enumerate(raw_parts):
        if "<" in raw_part and ">" in raw_part:
            break
        if index >= len(resolved_parts):
            break
        stable_parts.append(resolved_parts[index])

    if stable_parts:
        return os.path.normpath(os.path.join(render_dir, *stable_parts))
    if resolved_prefix_dir:
        return os.path.normpath(os.path.join(render_dir, resolved_prefix_dir))
    return os.path.normpath(render_dir)


def find_sequence_frame():
    workspace_dir = cmds.workspace(q=True, rd=True)
    images_dir = cmds.workspace(fileRuleEntry="images")
    render_dir = os.path.normpath(os.path.join(workspace_dir, images_dir))

    raw_prefix = normalize_prefix(cmds.getAttr("defaultRenderGlobals.imageFilePrefix"))
    resolved_prefix = normalize_prefix(resolve_render_tokens(raw_prefix))
    frame_padding = int(cmds.getAttr("defaultRenderGlobals.extensionPadding"))
    image_format = int(cmds.getAttr("defaultRenderGlobals.imageFormat"))
    extension = get_image_extension(image_format)

    prefix_dir = os.path.dirname(resolved_prefix)
    expected_dir = os.path.normpath(os.path.join(render_dir, prefix_dir))
    expected_base_name = os.path.basename(resolved_prefix)
    if "<" in expected_base_name and ">" in expected_base_name:
        expected_base_name = ""
    search_root = get_sequence_search_root(render_dir, raw_prefix, resolved_prefix)

    frame_regex = re.compile(
        rf"^(?P<base>.+)\.(?P<frame>\d{{{frame_padding}}})\.{re.escape(extension)}$",
        flags=re.IGNORECASE,
    )

    matches = []
    for dirpath, _, filenames in os.walk(search_root):
        for filename in filenames:
            match = frame_regex.match(filename)
            if not match:
                continue

            base_name = match.group("base")
            if expected_base_name and os.path.normcase(base_name) != os.path.normcase(expected_base_name):
                continue

            frame_number = int(match.group("frame"))
            full_path = os.path.join(dirpath, filename)
            matches.append(
                {
                    "dirpath": os.path.normpath(dirpath),
                    "base_name": base_name,
                    "frame_number": frame_number,
                    "full_path": full_path,
                }
            )

    if not matches:
        return None

    normalized_expected_dir = os.path.normcase(expected_dir)
    normalized_expected_base_name = os.path.normcase(expected_base_name)

    matches.sort(
        key=lambda item: (
            0
            if os.path.normcase(item["dirpath"]) == normalized_expected_dir
            and os.path.normcase(item["base_name"]) == normalized_expected_base_name
            else 1,
            os.path.normcase(item["dirpath"]),
            os.path.normcase(item["base_name"]),
            item["frame_number"],
        )
    )

    return matches[0]["full_path"]


def open_with_djv(image_path, djv_path="C:\\Program Files\\DJV2\\bin\\djv.exe"):
    if not os.path.exists(djv_path):
        raise FileNotFoundError(f"DJV executable not found at {djv_path}")

    subprocess.run([djv_path, image_path], check=True)


def main():
    render_path = find_sequence_frame()
    print(f"Resolved render frame: {render_path}")

    if not render_path:
        show_viewport_message("No render sequence found. DJV will not be opened.")
        return

    try:
        open_with_djv(render_path)
        show_viewport_message("Render sequence opened in DJV.")
    except Exception as exc:
        show_viewport_message("Failed to open render sequence in DJV.")
        print(f"Failed to open image with DJV: {exc}")


if __name__ == "__main__":
    main()
