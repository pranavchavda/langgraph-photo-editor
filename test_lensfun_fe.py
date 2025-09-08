#!/usr/bin/env python3
"""Search lensfun database for FE lenses without Sony prefix"""

import lensfunpy as lf

db = lf.Database()

# List all cameras to find Sony
print("=== All Sony cameras ===")
all_cameras = db.cameras
sony_cameras = [cam for cam in all_cameras if 'Sony' in cam.maker]
print(f"Found {len(sony_cameras)} Sony cameras")
for cam in sony_cameras[:10]:
    print(f"  - {cam.maker} {cam.model}")

if sony_cameras:
    # Pick a Sony camera
    camera = sony_cameras[0]
    print(f"\n=== Using: {camera.maker} {camera.model} ===")
    
    # Get all lenses
    all_lenses = db.find_lenses(camera, None, None)
    
    # Look for FE lenses (without Sony prefix)
    fe_lenses = [lens for lens in all_lenses if 'FE' in lens.model]
    print(f"\nFound {len(fe_lenses)} FE lenses:")
    for lens in fe_lenses:
        print(f"  - {lens.maker} {lens.model}")
    
    # Search for Doug's specific lenses
    doug_lens_patterns = ["FE 24-70", "FE 90", "FE 50", "FE 70-200"]
    for pattern in doug_lens_patterns:
        matching = [lens for lens in all_lenses if pattern in lens.model]
        print(f"\nLenses matching '{pattern}':")
        for lens in matching:
            print(f"  - {lens.maker} {lens.model}")