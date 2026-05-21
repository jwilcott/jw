import maya.cmds as cmds
import colorsys

# Get selected object
sel = cmds.ls(selection=True, dag=True, shapes=True)
if not sel:
    raise RuntimeError("No object selected.")
shape = sel[0]

# Find the shader
shading_engine = cmds.listConnections(shape, type='shadingEngine')
if not shading_engine:
    raise RuntimeError("No shading engine connected.")
shader = cmds.ls(cmds.listConnections(shading_engine[0] + ".surfaceShader"), materials=True)[0]

# Find the texture connected to the 'color' input
color_conn = cmds.listConnections(shader + ".color", source=True, destination=False, plugs=True)
if not color_conn:
    raise RuntimeError("No texture connected to color.")
original_texture = color_conn[0]

# Create a layeredTexture
layered_tex = cmds.shadingNode("layeredTexture", asTexture=True, name="layeredTexture_replace")

# Plug layeredTexture into shader
cmds.connectAttr(layered_tex + ".outColor", shader + ".color", force=True)

# Convert HSV to RGB
h, s, v = 27.009 / 360.0, 0.715, 0.699
r, g, b = colorsys.hsv_to_rgb(h, s, v)

# Create solid color node
const_color = cmds.shadingNode("plusMinusAverage", asUtility=True, name="solidColor_for_layeredTex")
cmds.setAttr(const_color + ".operation", 1)
cmds.setAttr(const_color + ".input3D[0]", r, g, b, type="double3")

# Plug original texture into input[0] (bottom layer)
cmds.connectAttr(original_texture, layered_tex + ".inputs[0].color", force=True)
cmds.connectAttr(original_texture.replace(".outColor", ".outAlpha"), layered_tex + ".inputs[0].alpha", force=True)
cmds.setAttr(layered_tex + ".inputs[0].blendMode", 1)  # Over

# Plug solid color into input[1] (top layer)
cmds.connectAttr(const_color + ".output3D", layered_tex + ".inputs[1].color", force=True)
cmds.setAttr(layered_tex + ".inputs[1].blendMode", 1)  # Over

print("LayeredTexture: original texture on bottom, tint on top, both using blendMode 'Over'.")
