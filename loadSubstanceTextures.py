import maya.cmds as cmds
import maya.mel as mel
import time  # Import time module for adding delays

def _is_plugin_loaded(plugin_name):
    try:
        return cmds.pluginInfo(plugin_name, query=True, loaded=True)
    except Exception:
        return False


def load_substance_plugins():
    plugins = [
        "Substance.mll",
        "substanceconnector.mll",
        "substanceworkflow.py",
        "substancemaya.mll",
    ]

    loaded_any = False
    failed = []

    for plugin in plugins:
        if _is_plugin_loaded(plugin):
            print("Plugin already loaded: {0}".format(plugin))
            loaded_any = True
            continue

        try:
            cmds.loadPlugin(plugin)
            print("Successfully loaded: {0}".format(plugin))
            loaded_any = True
            time.sleep(0.2)
        except Exception as error:
            failed.append((plugin, str(error)))
            print("Failed to load {0}: {1}".format(plugin, error))

    if failed:
        print("Substance plugin load finished with failures:")
        for plugin, reason in failed:
            print("  - {0}: {1}".format(plugin, reason))

    try:
        mel.eval("SubstancePluginImageWorkflow;")
        print("SubstancePluginImageWorkflow initialized.")
        loaded_any = True
    except Exception as error:
        print("SubstancePluginImageWorkflow init failed: {0}".format(error))

    return loaded_any


def run_substance_workflow():
    if not load_substance_plugins():
        message = "No Substance plugins are loaded. Skipping SubstancePluginImageWorkflow."
        print(message)
        cmds.warning(message)
        return
    print("Substance workflow complete.")


def loadSubstanceTextures():
    run_substance_workflow()


run_substance_workflow()