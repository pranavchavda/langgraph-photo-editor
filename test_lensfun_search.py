#!/usr/bin/env python3
"""Search lensfun database for Sony lenses"""

import lensfunpy as lf

db = lf.Database()

# Search for Sony Alpha cameras (mirrorless)
print("=== Searching for Sony Alpha/ILCE cameras ===")
for search_term in ["Alpha", "ILCE", "a7", "A7"]:
    cameras = db.find_cameras("Sony", search_term)
    print(f"\nSearch '{search_term}': Found {len(cameras)} cameras")
    for cam in cameras[:5]:  # Show first 5
        print(f"  - {cam.maker} {cam.model}")

# Use a common Sony mirrorless camera
cameras = db.find_cameras("Sony", "ILCE")
if cameras:
    camera = cameras[0]
    print(f"\n=== Using camera: {camera.maker} {camera.model} ===")
    
    # Search for lenses
    print("\nSearching for all lenses compatible with this camera:")
    all_lenses = db.find_lenses(camera, None, None)
    print(f"Total lenses: {len(all_lenses)}")
    
    # Show some lenses
    print("\nFirst 10 lenses:")
    for lens in all_lenses[:10]:
        print(f"  - {lens.maker} {lens.model}")
    
    # Search for specific lens patterns
    search_terms = ["24-70", "90mm", "50mm", "70-200", "2.8", "GM", "FE"]
    for term in search_terms:
        lenses = db.find_lenses(camera, None, term)
        print(f"\nLenses matching '{term}': {len(lenses)}")
        for lens in lenses[:3]:
            print(f"  - {lens.maker} {lens.model}")
else:
    print("No Sony ILCE cameras found")

# Also try searching without camera constraint
print("\n=== Direct lens search (no camera) ===")
search_terms = ["Sony FE", "24-70", "2.8"]
for term in search_terms:
    lenses = db.search_lenses(term) if hasattr(db, 'search_lenses') else []
    print(f"\nDirect search for '{term}': {len(lenses) if lenses else 'Method not available'}")