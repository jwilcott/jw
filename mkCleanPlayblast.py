#Make Clean H264 Playbast + Gif

import maya.cmds as cmds # type: ignore
import os
import subprocess

def create_playblast():
    # Get scene name and directory
    scene_path = cmds.file(q=True, sceneName=True)
    if not scene_path:
        cmds.warning("Please save your scene before running the script.")
        return
    
    scene_dir, scene_name = os.path.split(scene_path)
    base_name, _ = os.path.splitext(scene_name)
    
    # Define render directory
    render_dir = cmds.workspace(q=True, rd=True) + cmds.workspace(fileRuleEntry="images")
    
    # Get render settings from Maya
    file_prefix = cmds.getAttr("defaultRenderGlobals.imageFilePrefix")
    if "<scene>" in file_prefix:
        file_prefix = file_prefix.replace("<scene>", base_name)
    
    # Define output file paths
    mov_path = os.path.join(render_dir, f"{file_prefix}.mov")
    gif_path = os.path.join(render_dir, f"{file_prefix}.gif")

    # Get all model panels
    model_panels = cmds.getPanel(type="modelPanel")

    # Store current UI settings
    hud_state = cmds.optionVar(q="displayHUD")

    # Track resolution gate, overscan, and 2D Pan/Zoom state per camera
    res_gate_states = {}
    overscan_states = {}
    pan_zoom_states = {}

    # Disable HUD, resolution gate, adjust overscan, and disable 2D Pan/Zoom for all cameras in viewports
    cmds.optionVar(iv=("displayHUD", 0))
    for panel in model_panels:
        if cmds.modelEditor(panel, q=True, exists=True):
            camera = cmds.modelPanel(panel, q=True, camera=True)
            if cmds.objectType(camera) == "transform":
                camera_shape = cmds.listRelatives(camera, shapes=True)[0]
            else:
                camera_shape = camera

            # Store resolution gate state and disable it
            res_gate_states[camera_shape] = cmds.getAttr(f"{camera_shape}.displayResolution")
            cmds.setAttr(f"{camera_shape}.displayResolution", 0)

            # Store overscan value and set to 1.0
            overscan_states[camera_shape] = cmds.getAttr(f"{camera_shape}.overscan")
            cmds.setAttr(f"{camera_shape}.overscan", 1.0)

            # Store 2D Pan/Zoom state and disable it
            pan_zoom_states[camera_shape] = cmds.getAttr(f"{camera_shape}.panZoomEnabled")
            cmds.setAttr(f"{camera_shape}.panZoomEnabled", 0)

    try:
        # Create the playblast (on-screen, but does NOT open the file)
        cmds.playblast(format="qt", compression="H.264", quality=90,
                       filename=mov_path, forceOverwrite=True,
                       clearCache=True, percent=100,
                       showOrnaments=False, offScreen=False,  # Keeps it on-screen
                       viewer=False,  # Prevents auto-opening in VLC or any media player
                       widthHeight=[cmds.getAttr("defaultResolution.width") // 2,
                                    cmds.getAttr("defaultResolution.height") // 2],
                       startTime=cmds.playbackOptions(q=True, minTime=True),
                       endTime=cmds.playbackOptions(q=True, maxTime=True))

        print(f"Playblast saved to: {mov_path}")

        # Convert to GIF using ffmpeg (overwrite existing files)
        ffmpeg_cmd = f'ffmpeg -y -i "{mov_path}" -vf "fps=10,scale=640:-1:flags=lanczos" -loop 0 "{gif_path}"'
        try:
            subprocess.run(ffmpeg_cmd, shell=True, check=True)
            print(f"GIF created: {gif_path}")
        except subprocess.CalledProcessError as e:
            cmds.warning(f"FFmpeg conversion failed: {e}")

    finally:
        # Restore HUD setting
        cmds.optionVar(iv=("displayHUD", hud_state))

        # Restore resolution gate, overscan, and 2D Pan/Zoom states for all cameras
        for camera_shape in res_gate_states.keys():
            cmds.setAttr(f"{camera_shape}.displayResolution", res_gate_states[camera_shape])
            cmds.setAttr(f"{camera_shape}.overscan", 1.3)  # Restore overscan to 1.3
            cmds.setAttr(f"{camera_shape}.panZoomEnabled", pan_zoom_states[camera_shape])  # Restore 2D Pan/Zoom

    # Open the folder in Windows Explorer and select the .mov file
    try:
        subprocess.run(["explorer", "/select,", os.path.normpath(mov_path)], check=True)
    except Exception as e:
        print(f"Error while opening directory in Explorer: {e}")
    
create_playblast()
