from anim import amass
from anim import bvh
from anim.animation import Animation

import numpy as np

raw_data = dict(np.load("sitdown.npz", allow_pickle=True))

print(raw_data.keys())

if "mocap_framerate" in raw_data:
    print("mocap_framerate:", raw_data["mocap_framerate"])

print("poses shape:", raw_data["poses"].shape)
if "trans" in raw_data:
    print("trans shape:", raw_data["trans"].shape)

anim_data: Animation = amass.load(
    amass_motion_path="sitdown.npz",
    smplh_path="data/smplh/male/model.npz",
)
source_fps = anim_data.fps
target_fps = 30

step = source_fps / target_fps
indices = np.round(np.arange(0, len(anim_data), step)).astype(int)
indices = indices[indices < len(anim_data)]

anim_data.quats = anim_data.quats[indices]
anim_data.trans = anim_data.trans[indices]

if anim_data.positions is not None:
    anim_data.positions = anim_data.positions[indices]

anim_data.fps = target_fps
output_bvh_path = "sitdown_30fps.bvh"

bvh.save(
    filepath=output_bvh_path,
    anim=anim_data
)


print(f"File directory: {output_bvh_path}")

