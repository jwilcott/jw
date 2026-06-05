import maya.cmds as cmds
import maya.mel as mel


AOV_NAME = "PuzzleMatte"
OBJECT_ID_NAME = "rsObjectId"
OBJECT_ID = 1


def _has_attr(node, attr):
    return cmds.attributeQuery(attr, node=node, exists=True)


def _set_attr_if_exists(node, attr, value, attr_type=None):
    if not _has_attr(node, attr):
        return False

    plug = "{}.{}".format(node, attr)
    if attr_type:
        cmds.setAttr(plug, value, type=attr_type)
    else:
        cmds.setAttr(plug, value)
    return True


def _existing_puzzle_matte_aov():
    for node in cmds.ls(type="RedshiftAOV") or []:
        if _has_attr(node, "aovType") and cmds.getAttr("{}.aovType".format(node)) == "Puzzle Matte":
            return node
    return None


def _create_puzzle_matte_aov():
    node = _existing_puzzle_matte_aov()
    if node:
        return node

    if cmds.objExists(AOV_NAME):
        node = cmds.createNode("RedshiftAOV")
        node = cmds.rename(node, AOV_NAME)
    else:
        try:
            mel.eval('rsCreateAov -type "Puzzle Matte" -name "{}";'.format(AOV_NAME))
            node = AOV_NAME if cmds.objExists(AOV_NAME) else _existing_puzzle_matte_aov()
        except Exception:
            node = cmds.createNode("RedshiftAOV", name=AOV_NAME)

    if not node:
        cmds.error("Could not create a Redshift Puzzle Matte AOV.")

    return node


def setup_puzzle_matte_aov():
    aov = _create_puzzle_matte_aov()

    _set_attr_if_exists(aov, "aovType", "Puzzle Matte", "string")
    _set_attr_if_exists(aov, "aovName", "Puzzle Matte", "string")
    _set_attr_if_exists(aov, "name", AOV_NAME, "string")
    _set_attr_if_exists(aov, "enabled", 1)
    _set_attr_if_exists(aov, "fileFormat", 2)  # PNG
    _set_attr_if_exists(aov, "pngBits", 8)
    _set_attr_if_exists(aov, "mode", 1)  # Object ID
    _set_attr_if_exists(aov, "redId", 1)
    _set_attr_if_exists(aov, "greenId", 2)
    _set_attr_if_exists(aov, "blueId", 3)

    try:
        mel.eval('if(`frameLayout -exists "rsLayout_AovAOVsFrame"`) redshiftUpdateActiveAovList;')
    except Exception:
        pass

    return aov


def _selection_for_object_id():
    selection = cmds.ls(selection=True, long=True) or []
    dag_selection = cmds.ls(selection, dagObjects=True, long=True) or []
    if not dag_selection:
        cmds.error("Select the geo you want to add to {}.".format(OBJECT_ID_NAME))
    return selection


def create_object_id_set(selection):
    if cmds.objExists(OBJECT_ID_NAME) and cmds.nodeType(OBJECT_ID_NAME) == "RedshiftObjectId":
        object_id_node = OBJECT_ID_NAME
        _set_attr_if_exists(object_id_node, "objectId", OBJECT_ID)
        cmds.sets(selection, edit=True, forceElement=object_id_node)
        cmds.select(selection, replace=True)
        return object_id_node

    cmds.select(selection, replace=True)

    try:
        object_id_node = mel.eval("redshiftCreateObjectIdNode()")
    except Exception:
        object_id_node = cmds.createNode("RedshiftObjectId")
        cmds.sets(selection, edit=True, forceElement=object_id_node)

    if object_id_node != OBJECT_ID_NAME:
        if cmds.objExists(OBJECT_ID_NAME):
            object_id_node = cmds.rename(object_id_node, "{}#".format(OBJECT_ID_NAME))
        else:
            object_id_node = cmds.rename(object_id_node, OBJECT_ID_NAME)

    _set_attr_if_exists(object_id_node, "objectId", OBJECT_ID)
    cmds.sets(selection, edit=True, forceElement=object_id_node)
    cmds.select(selection, replace=True)

    return object_id_node


def main():
    selection = _selection_for_object_id()
    aov = setup_puzzle_matte_aov()
    object_id_node = create_object_id_set(selection)

    print("Created/updated {} AOV.".format(aov))
    print("Created {} with Object ID {} and added selected geo.".format(object_id_node, OBJECT_ID))


if __name__ == "__main__":
    main()
