import os
import maya.cmds as cmds

def open_most_recent_file():
    recent_files = cmds.optionVar(q='RecentFilesList')
    if recent_files:
        most_recent_file = recent_files[0]
        if os.path.exists(most_recent_file):
            cmds.file(most_recent_file, open=True, force=True)
            cmds.inViewMessage(amg=f"<hl>Opened recent file:</hl>\n{most_recent_file}", pos='topCenter', fade=True)
        else:
            cmds.warning("The most recent file doesn't exist anymore.")
    else:
        cmds.warning("No recent files found.")

open_most_recent_file()
