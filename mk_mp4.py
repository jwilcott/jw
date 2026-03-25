#Make Mp4 from image sequence using render settings from Maya
#Open File explorer after conversion and select the new mp4 file

import os
import argparse
import subprocess
import maya.cmds as cmds
import re

FFMPEG_BIN_DIR = "C:/ffmpeg/ffmpeg-master-latest-win64-gpl/bin"

def resolve_render_tokens(path_value):
    """
    Resolve supported Maya render tokens in a path-like string.
    """
    if not path_value:
        return path_value

    resolved_value = path_value

    if "<scene>" in resolved_value:
        scene_name = os.path.splitext(os.path.basename(cmds.file(q=True, sceneName=True)))[0]
        resolved_value = resolved_value.replace("<scene>", scene_name)

    if "<renderLayer>" in resolved_value:
        render_layer = cmds.editRenderLayerGlobals(query=True, currentRenderLayer=True)
        resolved_value = resolved_value.replace("<renderLayer>", render_layer)

    return resolved_value

def normalize_prefix(prefix):
    if not prefix:
        return prefix
    prefix = prefix.replace('\\', '/').strip('/')
    return prefix


def get_image_extension(image_format):
    if image_format == 8:
        return ".jpg"
    if image_format == 32:
        return ".exr"
    if image_format == 0:
        return ".iff"
    return ".png"


def get_sequence_search_root(render_dir, raw_prefix, resolved_prefix):
    raw_prefix_dir = os.path.dirname(raw_prefix or "")
    resolved_prefix_dir = os.path.dirname(resolved_prefix or "")

    raw_parts = [part for part in raw_prefix_dir.split('/') if part]
    resolved_parts = [part for part in resolved_prefix_dir.split('/') if part]

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


def find_sequence_specs(search_root, extension, frame_padding):
    frame_regex = re.compile(rf"^(?P<base>.+)\.(?P<frame>\d{{{frame_padding}}}){re.escape(extension)}$")
    grouped_sequences = {}

    for dirpath, _, filenames in os.walk(search_root):
        for filename in filenames:
            match = frame_regex.match(filename)
            if not match:
                continue

            base_name = match.group("base")
            frame_number = int(match.group("frame"))
            input_dir = os.path.normpath(dirpath)
            sequence_key = (input_dir, base_name)

            if sequence_key not in grouped_sequences:
                grouped_sequences[sequence_key] = {
                    "input_dir": input_dir,
                    "base_name": base_name,
                    "frame_numbers": []
                }

            grouped_sequences[sequence_key]["frame_numbers"].append(frame_number)

    sequence_specs = []
    for sequence_spec in grouped_sequences.values():
        sequence_spec["frame_numbers"].sort()
        sequence_spec["frame_pattern"] = f"{sequence_spec['base_name']}.%0{frame_padding}d{extension}"
        sequence_spec["output_file"] = os.path.join(sequence_spec["input_dir"], f"{sequence_spec['base_name']}.mp4")
        sequence_specs.append(sequence_spec)

    return sequence_specs


def sort_sequence_specs(sequence_specs, primary_input_dir, primary_base_name):
    normalized_primary_dir = os.path.normcase(os.path.normpath(primary_input_dir))
    normalized_primary_base = os.path.normcase(primary_base_name)

    def sort_key(sequence_spec):
        is_primary = (
            os.path.normcase(os.path.normpath(sequence_spec["input_dir"])) == normalized_primary_dir and
            os.path.normcase(sequence_spec["base_name"]) == normalized_primary_base
        )
        return (
            0 if is_primary else 1,
            os.path.normcase(os.path.normpath(sequence_spec["input_dir"])),
            os.path.normcase(sequence_spec["base_name"])
        )

    return sorted(sequence_specs, key=sort_key)


def find_image_sequence_from_maya_settings():
    """
    Find the image sequence based on Maya's render settings.
    """
    # Get render settings from Maya
    render_dir = os.path.normpath(cmds.workspace(q=True, rd=True) + cmds.workspace(fileRuleEntry="images"))
    raw_file_prefix = normalize_prefix(cmds.getAttr("defaultRenderGlobals.imageFilePrefix"))
    file_prefix = normalize_prefix(resolve_render_tokens(raw_file_prefix))

    frame_padding = int(cmds.getAttr("defaultRenderGlobals.extensionPadding"))
    image_format = int(cmds.getAttr("defaultRenderGlobals.imageFormat"))

    # Map Maya time units to FPS values
    fps_mapping = {
        "film": 24,
        "pal": 25,
        "29.97": 29.97,
        "ntsc": 30,
        "show": 48,
        "palf": 50,
        "ntscf": 60
    }
    fps = fps_mapping.get(cmds.currentUnit(q=True, time=True), 24)

    start_frame = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
    end_frame = int(cmds.getAttr("defaultRenderGlobals.endFrame"))

    extension = get_image_extension(image_format)

    prefix_dir = os.path.dirname(file_prefix)
    base_name = os.path.basename(file_prefix)
    input_dir = os.path.normpath(os.path.join(render_dir, prefix_dir))
    search_root = get_sequence_search_root(render_dir, raw_file_prefix, file_prefix)

    return {
        "input_dir": input_dir,
        "extension": extension,
        "fps": fps,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "base_name": base_name,
        "frame_padding": frame_padding,
        "search_root": search_root
    }


def convert_to_mp4(sequence_spec, fps, start_frame, end_frame):
    """
    Convert an image sequence into an H.264 MP4 video.
    """
    input_dir = sequence_spec["input_dir"]
    base_name = sequence_spec["base_name"]
    frame_numbers = sequence_spec["frame_numbers"]
    frame_pattern = sequence_spec["frame_pattern"]
    output_file = sequence_spec["output_file"]

    if not frame_numbers:
        raise FileNotFoundError(f"No images found for {base_name} in {input_dir}")

    actual_start = frame_numbers[0]
    actual_end = frame_numbers[-1]

    if start_frame < actual_start or end_frame > actual_end:
        print(f"Warning: requested frame range {start_frame}-{end_frame} is outside detected sequence {actual_start}-{actual_end}.")
        start_frame = max(start_frame, actual_start)
        end_frame = min(end_frame, actual_end)

    if start_frame > end_frame:
        raise ValueError(f"Invalid frame range after clamping: {start_frame}-{end_frame}")

    frame_count = end_frame - start_frame + 1

    # Ensure proper quoting of paths with spaces
    input_path = os.path.join(input_dir, frame_pattern).replace("\\", "/")
    output_file = output_file.replace("\\", "/")

    # Debug: Print paths
    print(f"Sequence: {base_name}")
    print(f"Input path: {input_path}")
    print(f"Output file: {output_file}")
    print(f"Requested frame range: {start_frame}-{end_frame} ({frame_count} frames)")

    # Add overwrite flag if the file already exists
    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists. It will be overwritten.")

    # ffmpeg command to convert image sequence to MP4
    command = [
        "ffmpeg",
        "-y",  # Automatically overwrite existing files
        "-framerate", str(fps),
        "-start_number", str(start_frame),  # Explicitly set start frame
        "-i", input_path,
        "-frames:v", str(frame_count),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_file
    ]

    # Ensure ffmpeg is in PATH
    env = os.environ.copy()
    env["PATH"] += os.pathsep + FFMPEG_BIN_DIR

    print("Running command:", " ".join(command))
    result = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("FFmpeg Output:\n", result.stdout)
    print("FFmpeg Errors:\n", result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed with exit code {result.returncode}")

    return output_file


def open_in_explorer(output_file):
    directory = os.path.abspath(os.path.dirname(output_file))
    if not os.path.exists(directory):
        print(f"Directory does not exist: {directory}")
        return

    print(f"Opening directory and selecting file: {output_file}")
    try:
        subprocess.run(["explorer", "/select,", os.path.normpath(output_file)], check=True)
    except Exception as exc:
        print(f"Error while opening directory in Explorer: {exc}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert an image sequence to an H.264 MP4 video based on Maya render settings.")

    args = parser.parse_args()

    try:
        settings = find_image_sequence_from_maya_settings()
        sequence_specs = find_sequence_specs(
            settings["search_root"],
            settings["extension"],
            settings["frame_padding"]
        )
        sequence_specs = sort_sequence_specs(
            sequence_specs,
            settings["input_dir"],
            settings["base_name"]
        )

        if not sequence_specs:
            raise FileNotFoundError(
                f"No image sequences found under {settings['search_root']} with extension {settings['extension']}"
            )

        created_files = []
        print(f"Found {len(sequence_specs)} sequence(s) under {settings['search_root']}")

        for sequence_spec in sequence_specs:
            output_file = convert_to_mp4(
                sequence_spec,
                settings["fps"],
                settings["start_frame"],
                settings["end_frame"]
            )
            created_files.append(output_file)
            print(f"Successfully created {output_file}")

        if created_files:
            open_in_explorer(created_files[-1])
    except Exception as e:
        print(f"Error: {e}")
