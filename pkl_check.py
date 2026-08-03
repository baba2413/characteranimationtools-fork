import pickle
import numpy as np

pkl_path = "merged.pkl"

with open(pkl_path, "rb") as f:
    data = pickle.load(f)

print("type(data):", type(data))

if isinstance(data, dict):
    print("\n전체 keys:")
    print(list(data.keys()))

    print("\nkey별 정보:")
    for key, value in data.items():
        print("=" * 60)
        print("key:", key)
        print("type:", type(value))

        if hasattr(value, "shape"):
            print("shape:", value.shape)
            print("dtype:", getattr(value, "dtype", None))

        elif isinstance(value, list):
            print("len:", len(value))
            if len(value) > 0:
                print("first item type:", type(value[0]))
                if hasattr(value[0], "shape"):
                    print("first item shape:", value[0].shape)

        elif isinstance(value, tuple):
            print("len:", len(value))
            if len(value) > 0:
                print("first item type:", type(value[0]))

        else:
            print("value:", value)
else:
    print("dict가 아닙니다.")
    print(data)


# import numpy as np

# data = np.load("파일명.npz", allow_pickle=True)

# print(data.files)

# for k in data.files:
#     v = data[k]
#     print(k, type(v), getattr(v, "shape", None), getattr(v, "dtype", None))