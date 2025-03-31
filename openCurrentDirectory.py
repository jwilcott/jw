# This script opens the directory of the currently active Maya scene file.

import os
from maya import cmds

def open_current_directory():
    # Get current file path
    current_file = cmds.file(query=True, sceneName=True)
    
    if not current_file:
        cmds.warning("No file is currently open")
        return
    
    # Get the directory path and open it
    dir_path = os.path.dirname(current_file)
    try:
        os.startfile(dir_path)
        print(f"Opened directory: {dir_path}")
    except Exception as e:
        cmds.warning(f"Failed to open directory: {str(e)}")

# Create a shelf button or run directly
if __name__ == "__main__":
    open_current_directory()
