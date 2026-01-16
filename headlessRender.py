import maya.cmds as cmds
import subprocess

# Specify by frame
by_frame = "1"

# Grab the current open Maya scene filepath
current_file = cmds.file(q=True, sceneName=True)

if current_file:
    # Get the render frame range from render settings
    start_frame = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
    end_frame = int(cmds.getAttr("defaultRenderGlobals.endFrame"))
    
    # Command to render and every nth frame
    render_cmd = f'start cmd /k Render -s {start_frame} -e {end_frame} -b {by_frame} "{current_file}"'

    # Run the subprocess
    subprocess.Popen(render_cmd, shell=True)

