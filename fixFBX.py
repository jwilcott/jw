import maya.cmds as cmds


FBX_PLUGIN_NAMES = ("fbxmaya", "fbxmaya.mll")


def _is_plugin_loaded(plugin_name):
    try:
        return cmds.pluginInfo(plugin_name, query=True, loaded=True)
    except Exception:
        return False


def _load_plugin(plugin_name):
    cmds.loadPlugin(plugin_name)
    print("Loaded FBX plugin: {0}".format(plugin_name))
    return plugin_name


def reload_fbx_plugin():
    loaded_plugins = [plugin for plugin in FBX_PLUGIN_NAMES if _is_plugin_loaded(plugin)]
    plugin_to_load = loaded_plugins[0] if loaded_plugins else FBX_PLUGIN_NAMES[0]

    for plugin in loaded_plugins:
        try:
            cmds.unloadPlugin(plugin, force=True)
            print("Unloaded FBX plugin: {0}".format(plugin))
        except Exception as error:
            message = "Could not unload {0}: {1}".format(plugin, error)
            print(message)
            cmds.warning(message)

    try:
        return _load_plugin(plugin_to_load)
    except Exception as first_error:
        print("Failed to load FBX plugin {0}: {1}".format(plugin_to_load, first_error))

    for plugin in FBX_PLUGIN_NAMES:
        if plugin == plugin_to_load:
            continue
        try:
            return _load_plugin(plugin)
        except Exception as error:
            print("Failed to load FBX plugin {0}: {1}".format(plugin, error))

    message = "FBX plugin reload failed. Tried: {0}".format(", ".join(FBX_PLUGIN_NAMES))
    cmds.warning(message)
    return None


def fixFBX():
    return reload_fbx_plugin()


reload_fbx_plugin()
