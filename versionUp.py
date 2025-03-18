import maya.cmds as cmds
import os
import re

def version_up_scene():
    # Get the current scene file
    current_scene = cmds.file(q=True, sn=True)
    if not current_scene:
        cmds.error("Scene has not been saved yet. Please save your scene before versioning up.")
        return

    directory, filename = os.path.split(current_scene)
    
    # Look for a version pattern "v" followed by digits.
    match = re.search(r'(v)(\d+)', filename, re.IGNORECASE)
    if match:
        old_version = match.group(0)
        version_num = int(match.group(2))
        # Increment the version number
        new_version_num = version_num + 1
        # Maintain the original zero padding
        width = len(match.group(2))
        new_version = 'v' + str(new_version_num).zfill(width)
        # Replace the old version string with the new version string (only the first occurrence)
        new_filename = filename.replace(old_version, new_version, 1)
    else:
        # If no version string found, append _v001 before the extension
        base, ext = os.path.splitext(filename)
        new_filename = base + '_v001' + ext

    new_filepath = os.path.join(directory, new_filename)
    
    # Rename and save the scene to the new file
    cmds.file(rename=new_filepath)
    cmds.file(save=True, type='mayaAscii')
    print("Scene versioned up and saved as:", new_filepath)

version_up_scene()
# filepath: c:\Users\jwilc\Documents\maya\scripts\jw\versionUp.py