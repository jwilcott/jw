import maya.cmds as cmds
import subprocess

# Specify GPUs to use (edit as needed, e.g., "0,1")
gpu_ids = "0"
by_frame = "1"
# Grab the current open Maya scene filepath
current_file = cmds.file(q=True, sceneName=True)

if current_file:
    # Get the render frame range from render settings
    start_frame = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
    end_frame = int(cmds.getAttr("defaultRenderGlobals.endFrame"))
    
    # Command to render with selected GPU(s) and every 30th frame
    render_cmd = f'start cmd /k Render -s {start_frame} -e {end_frame} -b {by_frame} "{current_file}"'

    # Run the subprocess
    subprocess.Popen(render_cmd, shell=True)

    print(f'Started headless Redshift render on GPU(s) {gpu_ids} for file:\n{current_file}')
    print(f'Rendering frames {start_frame} to {end_frame} by {by_frame}')
else:
    print("No Maya scene file is open! Please save your file first.")
