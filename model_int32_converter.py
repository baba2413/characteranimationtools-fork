import numpy as np

src = "data/smpl/male/model.npz"
dst = "data/smpl/male/model_int32.npz"

model = dict(np.load(src, allow_pickle=True))

model["kintree_table"] = model["kintree_table"].astype(np.int32)

np.savez(dst, **model)

print("saved:", dst)