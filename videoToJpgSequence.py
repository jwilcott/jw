#Convert .Move or .MP4 to JPG sequence for animated textures and image planes

import os
import subprocess
import maya.cmds as cmds # type: ignore

def main():
    # Prompt user for a .mov or .mp4 file using Maya's file dialog
    file_filter = "Video Files (*.mov *.mp4)"
    video_file = cmds.fileDialog2(fileFilter=file_filter, dialogStyle=2, fileMode=1)
    if not video_file:
        cmds.warning("No file selected.")
        return
    video_file = video_file[0]
    
    # Determine output folder based on the input file name
    base_dir = os.path.dirname(video_file)
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_dir = os.path.join(base_dir, base_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Build ffmpeg command to extract JPG sequence
    # Modified: include movie name as prefix for the image sequence
    output_pattern = os.path.join(output_dir, f"{base_name}_%04d.jpg")
    command = [
        "ffmpeg",
        "-y",                   # Overwrite output files without asking
        "-i", video_file,       # Input video file
        "-q:v", "2",            # Image quality setting
        output_pattern         # Output naming pattern
    ]
    
    # Ensure ffmpeg is in PATH
    env = os.environ.copy()
    env["PATH"] += os.pathsep + "C:/ffmpeg/ffmpeg-master-latest-win64-gpl/bin"  # Adjust ffmpeg path as needed
    
    # Execute the ffmpeg command
    print("Running command:", " ".join(command))
    result = subprocess.run(command, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("FFmpeg Output:\n", result.stdout)
    print("FFmpeg Errors:\n", result.stderr)
    if result.returncode != 0:
        cmds.warning("FFmpeg conversion failed.")
        return
    
    # Open the output directory in Explorer
    subprocess.run(["explorer", os.path.normpath(output_dir)])
    
if __name__ == "__main__":
    main()
