import maya.cmds as cmds

textures = set()

for material in cmds.ls(materials=True) or []:
    for attr in ("baseColor", "diffuseColor", "color"):
        if not cmds.attributeQuery(attr, node=material, exists=True):
            continue

        sources = cmds.listConnections(
            material + "." + attr, source=True, destination=False
        ) or []

        for source in sources:
            upstream = [source] + (cmds.listHistory(source) or [])
            textures.update(
                node for node in upstream
                if cmds.nodeType(node) == "file"
            )

cmds.undoInfo(openChunk=True)
try:
    for texture in sorted(textures):
        try:
            # Prevent color-space rules from overriding this setting.
            if cmds.attributeQuery(
                "ignoreColorSpaceFileRules", node=texture, exists=True
            ):
                cmds.setAttr(texture + ".ignoreColorSpaceFileRules", True)

            cmds.setAttr(texture + ".colorSpace", "sRGB", type="string")
            print("Set to sRGB: " + texture)
        except RuntimeError as error:
            cmds.warning("{}: {}".format(texture, error))
finally:
    cmds.undoInfo(closeChunk=True)