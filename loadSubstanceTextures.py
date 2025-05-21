import maya.cmds as cmds
import maya.mel as mel
import time  # Import time module for adding delays

# List of plugins to load
plugins = [
    "Substance.mll",
    "substanceconnector.mll",
    "substancelink.mll",
    "substancemaya.mll",
    "substanceworkflow.py"
]

# Load each plugin one at a time
for plugin in plugins:
    if not cmds.pluginInfo(plugin, query=True, loaded=True):
        try:
            cmds.loadPlugin(plugin)
            print(f"Successfully loaded: {plugin}")
            time.sleep(1)  # Add a 1-second delay between loading plugins
        except Exception as e:
            print(f"Failed to load {plugin}: {e}")
            break  # Stop loading further plugins if one fails
    else:
        print(f"Plugin already loaded: {plugin}")

# Execute the MEL command
try:
    mel.eval("SubstancePluginImageWorkflow")
    print("MEL command executed successfully.")
except Exception as e:
    print(f"Failed to execute MEL command: {e}")