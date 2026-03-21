import maya.cmds as cmds


def select_all_keys_in_scene():
    anim_curves = [
        curve
        for curve in (cmds.ls(type="animCurve") or [])
        if cmds.nodeType(curve).startswith("animCurveT")
    ]

    if not anim_curves:
        cmds.warning("No time-based animation keys found in this scene.")
        return

    cmds.selectKey(anim_curves, replace=True, keyframe=True)

    print("Selected all keys in the scene.")


if __name__ == "__main__":
    select_all_keys_in_scene()
