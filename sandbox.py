import maya.cmds as cmds


KEYWORDS = ("joints", "att", "cage")


def unlock_all_channels():
	all_nodes = cmds.ls(long=True) or []
	unlocked_count = 0

	for node in all_nodes:
		locked_attrs = cmds.listAttr(node, locked=True) or []
		for attr in locked_attrs:
			full_attr = f"{node}.{attr}"
			try:
				cmds.setAttr(full_attr, lock=False)
				unlocked_count += 1
			except Exception:
				pass

	print(f"Unlocked {unlocked_count} channel(s).")
	return unlocked_count


def delete_matching_objects(keywords=KEYWORDS):
	all_nodes = cmds.ls(dag=True, long=True) or []
	matching = [
		node for node in all_nodes if any(keyword in node.lower() for keyword in keywords)
	]

	if not matching:
		cmds.warning("No matching objects found.")
		return []

	to_delete = []
	for node in sorted(matching, key=lambda value: value.count("|")):
		if not any(node.startswith(parent + "|") for parent in to_delete):
			to_delete.append(node)

	cmds.delete(to_delete)
	print(f"Deleted {len(to_delete)} object(s).")
	return to_delete


unlock_all_channels()
delete_matching_objects()