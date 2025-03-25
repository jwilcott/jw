#Sync the timeline frame range to the render settings in Maya

import maya.cmds as cmds

def sync_frame_range_to_render_settings():
    # Query the timeline slider frame range
    start_frame = cmds.playbackOptions(query=True, minTime=True)
    end_frame = cmds.playbackOptions(query=True, maxTime=True)
    
    # Update render settings to match timeline frame range
    cmds.setAttr("defaultRenderGlobals.startFrame", start_frame)
    cmds.setAttr("defaultRenderGlobals.endFrame", end_frame)
    print("Render settings updated: startFrame = {}, endFrame = {}".format(start_frame, end_frame))

if __name__ == '__main__':
    sync_frame_range_to_render_settings()
