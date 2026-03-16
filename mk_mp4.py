#Make Mp4 from image sequence using render settings from Maya
#Open File explorer after conversion and select the new mp4 file

import os
import argparse
import subprocess
import maya.cmds as cmds
import glob

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


def detect_sequence_bounds(input_dir, base_name, frame_padding, extension):
    pattern = os.path.join(input_dir, f"{base_name}.{'?' * frame_padding}{extension}")
    candidates = glob.glob(pattern)
    import re
    frame_regex = re.compile(rf"^{re.escape(base_name)}\.(\d{{{frame_padding}}}){re.escape(extension)}$")

    frame_numbers = []
    for fn in candidates:
        name = os.path.basename(fn)
        match = frame_regex.match(name)
        if match:
            frame_numbers.append(int(match.group(1)))

    return sorted(frame_numbers)


def find_image_sequence_from_maya_settings():
    """
    Find the image sequence based on Maya's render settings.
    """
    # Get render settings from Maya
    render_dir = os.path.normpath(cmds.workspace(q=True, rd=True) + cmds.workspace(fileRuleEntry="images"))
    file_prefix = normalize_prefix(resolve_render_tokens(cmds.getAttr("defaultRenderGlobals.imageFilePrefix")))

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

    if image_format == 8:
        extension = ".jpg"
    elif image_format == 32:
        extension = ".exr"
    elif image_format == 0:
        extension = ".iff"
    else:
        extension = ".png"

    prefix_dir = os.path.dirname(file_prefix)
    base_name = os.path.basename(file_prefix)
    input_dir = os.path.normpath(os.path.join(render_dir, prefix_dir))

    frame_pattern = f"{base_name}.%0{frame_padding}d{extension}"
    return input_dir, frame_pattern, extension, fps, start_frame, end_frame, base_name, frame_padding


def convert_to_mp4(input_dir, frame_pattern, fps, output_file, start_frame, end_frame, file_prefix, frame_padding, extension):
    """
    Convert an image sequence into an H.264 MP4 video.
    """
    # Ensure the frame sequence exists and find actual range
    frame_numbers = detect_sequence_bounds(input_dir, file_prefix, frame_padding, extension)
    if not frame_numbers:
        raise FileNotFoundError(f"No images found matching {file_prefix}.{frame_pattern} in {input_dir}")

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
    output_file = os.path.join(input_dir, f"{file_prefix}.mp4").replace("\\", "/")

    # Debug: Print paths
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
    env["PATH"] += os.pathsep + "C:/ffmpeg/ffmpeg-master-latest-win64-gpl/bin"  # Update with your ffmpeg path

    print("Running command:", " ".join(command))
    try:
        result = subprocess.run(command, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("FFmpeg Output:\n", result.stdout)
        print("FFmpeg Errors:\n", result.stderr)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed with exit code {result.returncode}")

        # Open the directory containing the file in Explorer and select the new MP4 file
        directory = os.path.abspath(os.path.dirname(output_file))
        if not os.path.exists(directory):
            print(f"Directory does not exist: {directory}")
            return

        print(f"Opening directory and selecting file: {output_file}")
        try:
            subprocess.run(["explorer", "/select,", os.path.normpath(output_file)], check=True)
        except Exception as e:
            print(f"Error while opening directory in Explorer: {e}")
    except Exception as e:
        print(f"Error while running FFmpeg: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert an image sequence to an H.264 MP4 video based on Maya render settings.")

    args = parser.parse_args()

    try:
        input_dir, frame_pattern, extension, fps, start_frame, end_frame, file_prefix, frame_padding = find_image_sequence_from_maya_settings()
        output_file = os.path.join(input_dir, f"{file_prefix}.mp4")

        convert_to_mp4(input_dir, frame_pattern, fps, output_file, start_frame, end_frame, file_prefix, frame_padding, extension)
        print(f"Successfully created {output_file}")
    except Exception as e:
        print(f"Error: {e}")
