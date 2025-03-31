import maya.cmds as cmds
import pyperclip

def copy_scene_path_to_clipboard():
    """Copy the current Maya scene file path to the clipboard."""
    scene_path = cmds.file(query=True, sceneName=True)
    
    if not scene_path:
        cmds.warning("The current scene has not been saved yet.")
    else:
        pyperclip.copy(scene_path)
        print(f"Scene path copied to clipboard: {scene_path}")

if __name__ == "__main__":
    copy_scene_path_to_clipboard()
