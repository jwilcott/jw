import maya.cmds as cmds
import subprocess

# Specify GPUs to use (edit as needed, e.g., "0,1")
gpu_ids = "0"

# Grab the current open Maya scene filepath
current_file = cmds.file(q=True, sceneName=True)

if current_file:
    # Command to render with selected GPU(s)
    render_cmd = f'start cmd /k Render "{current_file}"'

    # Run the subprocess
    subprocess.Popen(render_cmd, shell=True)

    print(f'Started headless Redshift render on GPU(s) {gpu_ids} for file:\n{current_file}')
else:
    print("No Maya scene file is open! Please save your file first.")
