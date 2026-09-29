# Example job: build a titled scene — solid background, lower-third bar and text, a
# color correction filter — then screenshot it. Re-runnable: every
# helper creates or updates, so running it twice changes nothing.
#
#   OUT=/tmp/obs-out bash obs-run.sh example-scene-setup.py \
#       --arg scene="Skill Demo" --arg title="Hello from obs-websocket"
import os

scene = ARGS.get("scene", "Skill Demo")
title = ARGS.get("title", "Hello from obs-websocket")
prefix = ARGS.get("prefix", scene)  # input names are global in OBS — namespace them per scene

video = call("GetVideoSettings")
W, H = video["baseWidth"], video["baseHeight"]

ensure_scene(scene)

# Full-canvas background: color sources take width/height and an ABGR color int.
bg = f"{prefix} · Background"
ensure_input(scene, bg, "color_source_v3", {"color": obs_color("#0b1f3a"), "width": W, "height": H})

# Lower-third bar, pinned to the bottom-left by its own alignment point.
bar = f"{prefix} · Bar"
ensure_input(scene, bar, "color_source_v3",
             {"color": obs_color("#00adefe6"), "width": int(W * 0.45), "height": int(H * 0.11)})
set_transform(scene, bar, positionX=int(W * 0.04), positionY=int(H * 0.92), alignment=9)  # 9 = bottom|left

# Text: the kind differs per platform, so ask OBS which one it has.
kind = input_kind("text_ft2_source_v2", "text_gdiplus_v3", "text_gdiplus_v2")
text = f"{prefix} · Title"
ensure_input(scene, text, kind, text_settings(kind, title, size=int(H * 0.05), color="#ffffff"))
set_transform(scene, text, positionX=int(W * 0.06), positionY=int(H * 0.865), alignment=1)  # 1 = left, v-center

# Items stack in creation order; make sure the text sits above the bar.
call("SetSceneItemIndex", sceneName=scene, sceneItemId=item_id(scene, text),
     sceneItemIndex=len(call("GetSceneItemList", sceneName=scene)["sceneItems"]) - 1)

# color_filter_v2 works in linear light: brightness is added after linearizing, so even
# -0.05 clips a dark background to black. Saturation/contrast are the safe knobs here.
ensure_filter(bg, "Tone", "color_filter_v2", {"brightness": 0.0, "saturation": 0.15})

call("SetCurrentProgramScene", sceneName=scene)
shot = screenshot(scene, os.path.join(OUT, "skill-demo.png"), width=960)
print("scene:", scene)
print("items:", [i["sourceName"] for i in call("GetSceneItemList", sceneName=scene)["sceneItems"]])
print("screenshot:", shot)
