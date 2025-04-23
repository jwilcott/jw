#Removes Arnold

import maya.cmds as cmds

def safely_unload_plugins(plugins):
    for plugin in plugins:
        if cmds.pluginInfo(plugin, q=True, loaded=True):
            try:
                # Check for nodes using the plugin
                nodes_using_plugin = []
                # Get node types directly associated with the plugin
                node_types = cmds.pluginInfo(plugin, q=True, dependNode=True) or []

                # Add known problematic Arnold node types explicitly, including defaults
                known_arnold_types = [
                    "aiOptions", "aiAOVDriver", "aiAOVFilter", "aiImagerDenoiserOidn",
                    "defaultArnoldFilter", "defaultArnoldRenderOptions", "defaultArnoldDriver",
                    "defaultArnoldDisplayDriver", "defaultArnoldDenoiser"
                ]
                for nt in known_arnold_types:
                    # Check if the node type exists before adding
                    # Use cmds.nodeType to check existence robustly
                    if cmds.nodeType(nt, isTypeName=True) and nt not in node_types:
                        node_types.append(nt)

                # Also add specific default node names directly to the list to delete
                default_arnold_nodes = [
                    "defaultArnoldFilter", "defaultArnoldRenderOptions", "defaultArnoldDriver",
                    "defaultArnoldDisplayDriver", "defaultArnoldDenoiser"
                ]
                for node_name in default_arnold_nodes:
                    if cmds.objExists(node_name):
                        nodes_using_plugin.append(node_name)

                if node_types:
                    for node_type in node_types:
                        # Check if node type exists before listing
                        if cmds.ls(type=node_type):
                            nodes = cmds.ls(type=node_type)
                            if nodes:
                                nodes_using_plugin.extend(nodes)

                # Remove duplicates
                nodes_using_plugin = list(set(nodes_using_plugin))

                if nodes_using_plugin:
                    print(f"Plugin {plugin} is currently used by the following nodes:")
                    for node in nodes_using_plugin:
                        print(f"- {node}")
                    print(f"Deleting nodes using plugin {plugin}...")
                    try:
                        # Filter out nodes that might be locked or non-deletable default nodes
                        deletable_nodes = [n for n in nodes_using_plugin if cmds.objExists(n) and not cmds.lockNode(n, q=True)]
                        if deletable_nodes:
                            cmds.delete(deletable_nodes)
                            print(f"Successfully deleted nodes: {', '.join(deletable_nodes)}")
                        else:
                            print("No deletable nodes found or remaining nodes are locked.")
                    except Exception as delete_error:
                        print(f"Failed to delete some nodes: {delete_error}")
                        print(f"Attempting to force unload plugin {plugin} despite potential remaining usage.")
                else:
                    print(f"No nodes found using plugin {plugin}. Proceeding with unload.")

                # Attempt to unload the plugin
                cmds.unloadPlugin(plugin)
                print(f"Successfully unloaded plugin: {plugin}")
            except Exception as e:
                print(f"Failed to unload plugin {plugin}: {e}")
        else:
            print(f"Plugin {plugin} is not loaded.")

# List of plugins to unload
plugins_to_remove = ["mtoa"]

safely_unload_plugins(plugins_to_remove)