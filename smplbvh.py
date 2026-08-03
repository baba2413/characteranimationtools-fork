from anim import amass, bvh
from anim.animation import Animation
import numpy as np
import pickle


with open("merged.pkl", "rb") as f:
    data = pickle.load(f)

orig = dict(np.load("data/amass/squat_smplh.npz", allow_pickle=True))
amass_like = {
    "poses": data["full_pose"].astype(np.float32),
    "betas": data["betas"].astype(np.float32),
    "gender": np.array(data["gender"]),
    "mocap_framerate": orig["mocap_framerate"],
    "trans": orig["trans"].astype(np.float32),
}

np.savez("merged_amass_like.npz", **amass_like)
anim_data: Animation = amass.load(
    amass_motion_path="merged_amass_like.npz",
    smplh_path="data/smpl/male/model_int32.npz",
    load_hand=False,
    num_betas=10,
)

output_bvh_path = "squat_bvh_smpl.bvh"

bvh.save(
    filepath=output_bvh_path,
    anim=anim_data,
)

print(f"File directory: {output_bvh_path}")