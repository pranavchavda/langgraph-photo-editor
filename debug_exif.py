#!/usr/bin/env python3
"""Debug EXIF data extraction"""

from PIL import Image
from PIL.ExifTags import TAGS, IFD
import sys
from pathlib import Path

def debug_exif(image_path):
    """Debug EXIF data extraction with detailed output"""
    print(f"\nAnalyzing: {image_path}")
    print("=" * 60)
    
    try:
        img = Image.open(image_path)
        exifdata = img.getexif()
        
        if not exifdata:
            print("No EXIF data found")
            return
        
        print(f"Found {len(exifdata)} EXIF tags\n")
        
        # Print all EXIF data
        print("All EXIF Tags:")
        print("-" * 40)
        for tag_id, value in exifdata.items():
            tag = TAGS.get(tag_id, f"Unknown({tag_id})")
            # Limit value display length for readability
            value_str = str(value)[:100] if value else "None"
            print(f"{tag:30} : {value_str}")
        
        # Try IFD data for more detailed EXIF
        print("\n" + "=" * 60)
        print("Checking IFD Data:")
        print("-" * 40)
        
        # Get IFD EXIF data
        ifd_exif = exifdata.get_ifd(IFD.Exif)
        if ifd_exif:
            print(f"Found {len(ifd_exif)} IFD EXIF tags\n")
            for tag_id, value in ifd_exif.items():
                tag = TAGS.get(tag_id, f"Unknown({tag_id})")
                value_str = str(value)[:100] if value else "None"
                print(f"{tag:30} : {value_str}")
        else:
            print("No IFD EXIF data found")
        
        # Check for MakerNote (camera-specific data)
        print("\n" + "=" * 60)
        print("Lens-related tags search:")
        print("-" * 40)
        
        # Search for lens-related information in various places
        lens_tags = ['LensModel', 'Lens', 'LensSpecification', 'LensInfo', 
                     'LensMake', 'LensSerialNumber', 'LensType']
        
        found_lens_info = False
        for tag_name in lens_tags:
            for tag_id, value in exifdata.items():
                if TAGS.get(tag_id) == tag_name:
                    print(f"✓ {tag_name}: {value}")
                    found_lens_info = True
        
        # Also check IFD EXIF
        if ifd_exif:
            for tag_name in lens_tags:
                for tag_id, value in ifd_exif.items():
                    if TAGS.get(tag_id) == tag_name:
                        print(f"✓ {tag_name} (from IFD): {value}")
                        found_lens_info = True
        
        if not found_lens_info:
            print("❌ No lens information found in standard EXIF tags")
            
            # Try to find any tag with "lens" in it (case insensitive)
            print("\nSearching for any tag containing 'lens':")
            for tag_id, value in exifdata.items():
                tag = TAGS.get(tag_id, f"Unknown({tag_id})")
                if 'lens' in tag.lower() and value:
                    print(f"  Found: {tag} = {value}")
        
        # Print focal length info
        print("\n" + "=" * 60)
        print("Focal Length Information:")
        print("-" * 40)
        focal_tags = ['FocalLength', 'FocalLengthIn35mmFilm']
        for tag_name in focal_tags:
            for tag_id, value in exifdata.items():
                if TAGS.get(tag_id) == tag_name:
                    print(f"✓ {tag_name}: {value}")
        
    except Exception as e:
        print(f"Error reading EXIF: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_exif(sys.argv[1])
    else:
        # Test with a sample image if it exists
        test_path = "/tmp/test_image.jpg"
        if Path(test_path).exists():
            debug_exif(test_path)
        else:
            print("Usage: python debug_exif.py <image_path>")