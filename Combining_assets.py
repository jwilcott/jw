import maya.cmds as cmds

def matches_all(name, keywords):
    return all(k in name for k in keywords)

def matches_any(name, keywords):
    return any(k in name for k in keywords)

def find_by_keywords(objs, keywords):
    return [obj for obj in objs if all(k.lower() in obj.lower() for k in keywords)]

# Get the selected object and remove "_Jersey" from its name
sel = cmds.ls(selection=True)
if not sel:
    cmds.warning("No object selected.")
else:
    selJersey = sel[0].replace("_Jersey", "")

    # Find all objects that contain selJersey in their name and are DAG objects (transforms)
    matches = cmds.ls(f"*{selJersey}*", type="transform")
    print(f"Found {len(matches)} matching objects for '{selJersey}':")
    for obj in matches:
        print(f"  {obj}")

    # Find specific objects
    jersey = find_by_keywords(matches, ["jersey"])
    bat = find_by_keywords(matches, ["bat"])
    hat = find_by_keywords(matches, ["hat"])
    crossed = find_by_keywords(matches, ["crossed"])
    black_hair = find_by_keywords(matches, ["black", "hair"])
    blonde_hair = find_by_keywords(matches, ["blonde", "hair"])
    blue_hair = find_by_keywords(matches, ["blue", "hair"])
    brown_hair = find_by_keywords(matches, ["brown", "hair"])
    red_hair = find_by_keywords(matches, ["red", "hair"])

    # Define groups
    group_dict = {
        f"{selJersey}_Base": jersey + bat + hat,
        f"{selJersey}_BaseCrossed": jersey + crossed + hat,
        f"{selJersey}_Hair_Black": jersey + bat + black_hair,
        f"{selJersey}_Hair_Black_Crossed": jersey + crossed + black_hair,
        f"{selJersey}_Hair_Blonde": jersey + bat + blonde_hair,
        f"{selJersey}_Hair_Blonde_Crossed": jersey + crossed + blonde_hair,
        f"{selJersey}_Hair_Blue": jersey + bat + blue_hair,
        f"{selJersey}_Hair_Blue_Crossed": jersey + crossed + blue_hair,
        f"{selJersey}_Hair_Brown": jersey + bat + brown_hair,
        f"{selJersey}_Hair_Brown_Crossed": jersey + crossed + brown_hair,
        f"{selJersey}_Hair_Red": jersey + bat + red_hair,
        f"{selJersey}_Hair_Red_Crossed": jersey + crossed + red_hair,
    }

    # Remove duplicates in each group and skip groups missing a hair color
    for group_name, objs in group_dict.items():
        # Skip group if it's a hair group and the hair color object is missing
        if "Hair_Black" in group_name and not black_hair:
            continue
        if "Hair_Blonde" in group_name and not blonde_hair:
            continue
        if "Hair_Blue" in group_name and not blue_hair:
            continue
        if "Hair_Brown" in group_name and not brown_hair:
            continue
        if "Hair_Red" in group_name and not red_hair:
            continue

        unique_objs = list(dict.fromkeys(objs))  # preserves order, removes duplicates
        if unique_objs:
            dup_objs = cmds.duplicate(unique_objs, rr=True)
            group = cmds.group(dup_objs, name=group_name)
            cmds.parent(group, world=True)