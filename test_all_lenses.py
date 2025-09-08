#!/usr/bin/env python3
"""List ALL lenses in lensfun database to find FE lenses"""

import lensfunpy as lf

db = lf.Database()

# Get ALL lenses in the database
all_lenses = db.lenses

print(f"Total lenses in database: {len(all_lenses)}")

# Search for FE lenses (with or without Sony prefix)
fe_lenses = []
gm_lenses = []
sony_lenses = []

for lens in all_lenses:
    model = lens.model.upper()
    maker = lens.maker.upper()
    
    # Check for FE mount
    if 'FE ' in model or model.startswith('FE '):
        fe_lenses.append((lens.maker, lens.model))
    
    # Check for GM designation
    if 'GM' in model:
        gm_lenses.append((lens.maker, lens.model))
    
    # Check for Sony brand
    if 'SONY' in maker:
        sony_lenses.append((lens.maker, lens.model))

print(f"\n=== FE Mount Lenses: {len(fe_lenses)} ===")
for maker, model in fe_lenses[:20]:  # Show first 20
    print(f"  {maker}: {model}")

print(f"\n=== GM Lenses: {len(gm_lenses)} ===")
for maker, model in gm_lenses[:20]:
    print(f"  {maker}: {model}")

print(f"\n=== Sony Brand Lenses: {len(sony_lenses)} ===")
for maker, model in sony_lenses[:20]:
    print(f"  {maker}: {model}")

# Search for Doug's specific focal lengths
doug_patterns = ['24-70', '90mm', '50mm', '70-200', '2.8']
for pattern in doug_patterns:
    matching = []
    for lens in all_lenses:
        if pattern.lower() in lens.model.lower():
            matching.append((lens.maker, lens.model))
    
    print(f"\n=== Lenses with '{pattern}': {len(matching)} ===")
    for maker, model in matching[:10]:  # Show first 10
        print(f"  {maker}: {model}")