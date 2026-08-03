import os
import numpy as np
from anim import bvh
from anim.animation import Animation
from anim.aistpp import load as load_smpl_motion

def convert_amass_smpl_to_bvh(npz_path, smpl_model_path, output_bvh_path):
    print(f"Loading AMASS SMPL data: {npz_path}")
    
    try:
        anim = load_smpl_motion(
            aistpp_motion_path=npz_path, 
            smpl_path=smpl_model_path
        )
        
        os.makedirs(os.path.dirname(output_bvh_path), exist_ok=True)
        bvh.save(filepath=output_bvh_path, anim=anim)
        print(f"Sucess: {output_bvh_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    NPZ_PATH = "merged_aist_style.npz"
    SMPL_MODEL_PATH = "data/smpl/male/model.npz"
    OUTPUT_BVH_PATH = "motion_output.bvh"
    
    convert_amass_smpl_to_bvh(NPZ_PATH, SMPL_MODEL_PATH, OUTPUT_BVH_PATH)