#Make ProRes 422 with Alpha from image sequence using render settings from Maya
#Open File explorer after conversion and select the new ProRes 422 file

import os
import argparse
import subprocess
import maya.cmds as cmds
import glob

def find_image_sequence_from_maya_settings():
    """
    Find the image sequence based on Maya's render settings.
    """
    # Get render settings from Maya
    render_dir = cmds.workspace(q=True, rd=True) + cmds.workspace(fileRuleEntry="images")
    file_prefix = cmds.getAttr("defaultRenderGlobals.imageFilePrefix")
    if "<scene>" in file_prefix:
        scene_name = os.path.splitext(os.path.basename(cmds.file(q=True, sceneName=True)))[0]
        file_prefix = file_prefix.replace("<scene>", scene_name)

    frame_padding = cmds.getAttr("defaultRenderGlobals.extensionPadding")
    image_format = cmds.getAttr("defaultRenderGlobals.imageFormat")

    # Map Maya time units to FPS values
    fps_mapping = {
        "film": 24,
        "pal": 25,
        "ntsc": 30,
        "show": 48,
        "palf": 50,
        "ntscf": 60,
        "59.94fps": 59.94  # Added 59.94 FPS mapping
    }
    fps = fps_mapping.get(cmds.currentUnit(q=True, time=True), 24)  # Default to 24 FPS if not found
    # Debug: Check Maya's time unit setting and computed fps
    print(f"Scene frame rate detected: {cmds.currentUnit(q=True, time=True)} -> {fps} FPS")

    start_frame = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
    end_frame = int(cmds.getAttr("defaultRenderGlobals.endFrame"))

    if image_format == 8:
        extension = ".jpg"
    elif image_format == 32:
        extension = ".exr"
    elif image_format == 0:
        extension = ".iff"
    else:
        extension = ".png"  # Default fallback

    frame_pattern = f"{file_prefix}.%0{frame_padding}d{extension}"
    return render_dir, frame_pattern, extension, fps, start_frame, end_frame, file_prefix

def convert_to_prores(input_dir, frame_pattern, fps, output_file, start_frame, end_frame, file_prefix):
    """
    Convert an image sequence into a ProRes 422 video.
    """
    # Ensure the frame sequence exists
    image_files = glob.glob(os.path.join(input_dir, file_prefix + ".*"))
    if not image_files:
        raise FileNotFoundError(f"No images found matching {file_prefix} in {input_dir}")

    # Ensure proper quoting of paths with spaces
    input_path = os.path.join(input_dir, frame_pattern).replace("\\", "/")
    output_file = os.path.join(input_dir, f"{file_prefix}.mov").replace("\\", "/")

    # Debug: Print paths
    print(f"Input path: {input_path}")
    print(f"Output file: {output_file}")
    print(f"Start frame: {start_frame}")

    # Add overwrite flag if the file already exists
    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists. It will be overwritten.")

    # ffmpeg command to convert image sequence to ProRes with alpha channel using ProRes 4444
    command = [
        "ffmpeg",
        "-y",  # Automatically overwrite existing files
        "-framerate", str(fps),
        "-start_number", str(start_frame),
        "-i", input_path,
        "-frames:v", str(end_frame - start_frame + 1),
        "-c:v", "prores_ks",
        "-profile:v", "4444",  # Use profile 4444 for alpha channel
        "-pix_fmt", "yuva444p10le",
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

        # Open the directory containing the file in Explorer and select the new ProRes file
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
    parser = argparse.ArgumentParser(description="Convert an image sequence to a ProRes 422 MOV video based on Maya render settings.")
    args = parser.parse_args()

    try:
        input_dir, frame_pattern, extension, fps, start_frame, end_frame, file_prefix = find_image_sequence_from_maya_settings()
        output_file = os.path.join(input_dir, f"{file_prefix}.mov")

        convert_to_prores(input_dir, frame_pattern, fps, output_file, start_frame, end_frame, file_prefix)
        print(f"Successfully created {output_file}")
    except Exception as e:
        print(f"Error: {e}")