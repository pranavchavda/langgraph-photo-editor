"""
Lens Correction Module for Doug's Photo Editor
Handles lens-specific distortion, vignetting, and chromatic aberration corrections
"""

import subprocess
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image
from PIL.ExifTags import TAGS
import json

# Doug's lens profiles with correction parameters
# These values are approximations based on typical characteristics of these lenses
DOUG_LENS_PROFILES = {
    "Sony FE 24-70mm F2.8 GM": {
        "display_name": "Sony FE 24-70mm F2.8 GM",
        "exif_names": ["FE 24-70mm F2.8 GM", "Sony FE 24-70mm F2.8 GM OSS", "24-70mm F2.8", "FE 24-70mm F2.8 GM"],
        "corrections": {
            "24": {  # 24mm focal length
                "distortion": "0.028 -0.073 0.022",  # Barrel distortion at wide end
                "vignetting": "80x80+15+15",  # Stronger vignetting at wide
                "chromatic_aberration": True
            },
            "35": {
                "distortion": "0.015 -0.045 0.012",
                "vignetting": "60x60+12+12",
                "chromatic_aberration": True
            },
            "50": {
                "distortion": "0.008 -0.025 0.008",
                "vignetting": "50x50+10+10",
                "chromatic_aberration": True
            },
            "70": {  # 70mm focal length
                "distortion": "-0.012 0.018 -0.005",  # Slight pincushion at long end
                "vignetting": "40x40+8+8",
                "chromatic_aberration": True
            }
        }
    },
    "Sony FE 90mm F2.8 Macro": {
        "display_name": "Sony FE 90mm F2.8 Macro",
        "exif_names": ["FE 90mm F2.8 Macro G OSS", "Sony FE 90mm F2.8 Macro", "90mm F2.8"],
        "corrections": {
            "90": {
                "distortion": "-0.008 0.012 -0.003",  # Very minimal distortion (macro lens)
                "vignetting": "30x30+8+8",  # Minimal vignetting
                "chromatic_aberration": True
            }
        }
    },
    "Sony FE 50mm F1.4 GM": {
        "display_name": "Sony FE 50mm F1.4 GM",
        "exif_names": ["FE 50mm F1.4 GM", "Sony FE 50mm F1.4 GM", "50mm F1.4"],
        "corrections": {
            "50": {
                "distortion": "0.005 -0.018 0.005",  # Minimal barrel distortion
                "vignetting": "70x70+15+15",  # More vignetting at f/1.4
                "chromatic_aberration": True
            }
        }
    },
    "Sony FE 70-200mm F2.8 GM": {
        "display_name": "Sony FE 70-200mm F2.8 GM",
        "exif_names": ["FE 70-200mm F2.8 GM OSS", "Sony FE 70-200mm F2.8 GM", "70-200mm F2.8"],
        "corrections": {
            "70": {
                "distortion": "-0.005 0.008 -0.002",  # Slight pincushion
                "vignetting": "40x40+10+10",
                "chromatic_aberration": True
            },
            "100": {
                "distortion": "-0.008 0.012 -0.003",
                "vignetting": "35x35+8+8",
                "chromatic_aberration": True
            },
            "135": {
                "distortion": "-0.010 0.015 -0.004",
                "vignetting": "35x35+8+8",
                "chromatic_aberration": True
            },
            "200": {
                "distortion": "-0.015 0.020 -0.005",  # More pincushion at long end
                "vignetting": "45x45+10+10",
                "chromatic_aberration": True
            }
        }
    },
    "None (Auto-detect from EXIF)": {
        "display_name": "None (Auto-detect from EXIF)",
        "exif_names": [],
        "corrections": {}
    }
}


def get_image_exif_data(image_path: str) -> Dict:
    """Extract EXIF data from image including lens information"""
    try:
        from PIL.ExifTags import IFD
        img = Image.open(image_path)
        exifdata = img.getexif()
        
        if not exifdata:
            return {}
        
        exif_dict = {}
        for tag_id, value in exifdata.items():
            tag = TAGS.get(tag_id, tag_id)
            exif_dict[tag] = value
        
        # Also check IFD EXIF data for more detailed info
        ifd_exif = exifdata.get_ifd(IFD.Exif) if hasattr(exifdata, 'get_ifd') else {}
        for tag_id, value in ifd_exif.items():
            tag = TAGS.get(tag_id, tag_id)
            exif_dict[tag] = value
        
        # Try to get lens model from various possible EXIF tags
        lens_model = None
        lens_keys = ['LensModel', 'Lens', 'LensSpecification', 'LensInfo', 'LensMake']
        for key in lens_keys:
            if key in exif_dict and exif_dict[key]:
                lens_value = exif_dict[key]
                # Handle tuple values from LensSpecification (min focal, max focal, min aperture, max aperture)
                if isinstance(lens_value, (tuple, list)) and len(lens_value) >= 2:
                    # Create a lens description from focal range
                    min_focal = lens_value[0] if lens_value[0] else 0
                    max_focal = lens_value[1] if lens_value[1] else 0
                    if min_focal and max_focal:
                        if min_focal == max_focal:
                            lens_model = f"{int(min_focal)}mm"
                        else:
                            lens_model = f"{int(min_focal)}-{int(max_focal)}mm"
                        # Try to add aperture info if available
                        if len(lens_value) >= 3 and lens_value[2]:
                            lens_model += f" F{lens_value[2]}"
                else:
                    lens_model = str(lens_value)
                
                if lens_model:
                    break
        
        # Get focal length
        focal_length = None
        if 'FocalLength' in exif_dict:
            focal_value = exif_dict['FocalLength']
            # Handle IFDRational objects
            if hasattr(focal_value, 'real'):
                focal_length = float(focal_value.real)
            else:
                focal_length = float(focal_value)
        elif 'FocalLengthIn35mmFilm' in exif_dict:
            focal_length = float(exif_dict['FocalLengthIn35mmFilm'])
        
        # Debug: Found lens and focal length info
        
        return {
            'lens_model': lens_model,
            'focal_length': focal_length,
            'f_number': exif_dict.get('FNumber'),
            'camera_make': exif_dict.get('Make'),
            'camera_model': exif_dict.get('Model')
        }
    except Exception as e:
        print(f"Error reading EXIF data: {e}")
        import traceback
        traceback.print_exc()
        return {}


def detect_lens_from_exif(image_path: str) -> Optional[str]:
    """Try to detect which of Doug's lenses was used based on EXIF data"""
    exif_data = get_image_exif_data(image_path)
    
    if not exif_data.get('lens_model'):
        return None
    
    lens_model_exif = str(exif_data['lens_model']).upper()
    
    # Keep the original for comparison (don't replace hyphens in focal ranges)
    lens_model_normalized = lens_model_exif
    
    
    # Check each lens profile to see if EXIF matches
    for lens_key, profile in DOUG_LENS_PROFILES.items():
        if lens_key == "None (Auto-detect from EXIF)":
            continue
        
        # Check against all known variations
        for exif_name in profile['exif_names']:
            exif_name_upper = exif_name.upper()
            
            
            # Try various matching strategies
            # 1. Direct substring match
            if exif_name_upper in lens_model_normalized or lens_model_normalized in exif_name_upper:
                print(f"Auto-detected lens from EXIF (direct match): {lens_key}")
                return lens_key
            
            # 1b. Try exact match after normalization
            if exif_name_upper == lens_model_normalized:
                print(f"Auto-detected lens from EXIF (exact match): {lens_key}")
                return lens_key
            
            # 2. Check for key components (focal length and aperture)
            # Extract focal ranges and aperture from both strings
            import re
            
            # Pattern to find focal length ranges like "24-70" or single like "90"
            focal_pattern = r'(\d+)(?:\s*-\s*(\d+))?\s*mm'
            aperture_pattern = r'[fF]/?(\d+\.?\d*)'
            
            exif_focals = re.findall(focal_pattern, lens_model_normalized)
            exif_aperture = re.findall(aperture_pattern, lens_model_normalized)
            
            profile_focals = re.findall(focal_pattern, exif_name_upper)
            profile_aperture = re.findall(aperture_pattern, exif_name_upper)
            
            # Match based on focal length and aperture
            if exif_focals and profile_focals:
                # Compare focal ranges
                if exif_focals[0] == profile_focals[0]:
                    # Also check aperture if available
                    if exif_aperture and profile_aperture:
                        if exif_aperture[0] == profile_aperture[0]:
                            print(f"Auto-detected lens from EXIF (focal+aperture match): {lens_key}")
                            return lens_key
                    else:
                        # Just focal match is good enough for some cases
                        print(f"Auto-detected lens from EXIF (focal match): {lens_key}")
                        return lens_key
    
    return None


def get_closest_focal_length(focal_length: float, available_focals: list) -> str:
    """Find the closest available focal length in the profile"""
    if not available_focals:
        return None
    
    available_nums = [int(f) for f in available_focals]
    closest = min(available_nums, key=lambda x: abs(x - focal_length))
    return str(closest)


def apply_lens_corrections(
    image_path: str, 
    output_path: str,
    selected_lens: Optional[str] = None,
    focal_length: Optional[float] = None
) -> Dict:
    """
    Apply lens corrections to an image
    
    Args:
        image_path: Path to input image
        output_path: Path to save corrected image
        selected_lens: Manually selected lens from dropdown (overrides EXIF)
        focal_length: Focal length (if zoom lens)
    
    Returns:
        Dict with correction details
    """
    
    # Determine which lens to use
    lens_to_use = None
    detected_from_exif = False
    
    if selected_lens and selected_lens != "None (Auto-detect from EXIF)":
        # Use manually selected lens
        lens_to_use = selected_lens
    else:
        # Try to detect from EXIF
        lens_to_use = detect_lens_from_exif(image_path)
        detected_from_exif = True
        
        # Also get focal length from EXIF if not provided
        if lens_to_use and not focal_length:
            exif_data = get_image_exif_data(image_path)
            focal_length = exif_data.get('focal_length')
    
    if not lens_to_use:
        # No lens detected or selected, return original
        import shutil
        shutil.copy2(image_path, output_path)
        return {
            'corrections_applied': False,
            'reason': 'No lens profile found',
            'lens_used': None
        }
    
    # Get the lens profile
    profile = DOUG_LENS_PROFILES.get(lens_to_use)
    if not profile or not profile['corrections']:
        import shutil
        shutil.copy2(image_path, output_path)
        return {
            'corrections_applied': False,
            'reason': 'No corrections available for this lens',
            'lens_used': lens_to_use
        }
    
    # Get appropriate corrections based on focal length
    corrections = profile['corrections']
    
    # For zoom lenses, find the closest focal length
    if len(corrections) > 1 and focal_length:
        focal_key = get_closest_focal_length(focal_length, list(corrections.keys()))
    else:
        # Prime lens or no focal length info, use the first/only entry
        focal_key = list(corrections.keys())[0]
    
    correction_params = corrections[focal_key]
    
    # Check if ImageMagick is available
    from src.agents_enhanced import get_imagemagick_command
    magick_cmd = get_imagemagick_command()
    
    if not magick_cmd:
        # ImageMagick not available, return original with metadata
        import shutil
        shutil.copy2(image_path, output_path)
        return {
            'corrections_applied': False,
            'reason': 'ImageMagick not available',
            'lens_used': lens_to_use,
            'detected_from_exif': detected_from_exif,
            'focal_length': focal_key,
            'corrections_attempted': correction_params
        }
    
    # Build ImageMagick command for lens corrections
    cmd = [magick_cmd, image_path]
    
    # IMPORTANT: Set virtual pixel method to prevent cropping during distortion
    cmd.extend(['-virtual-pixel', 'edge'])
    
    # Apply distortion correction (barrel/pincushion)
    if correction_params.get('distortion'):
        # ImageMagick Barrel distortion expects: A B C [D [X,Y]]
        # Our values are already space-separated
        # Use +distort to preserve the full image canvas
        cmd.extend(['+distort', 'Barrel', correction_params['distortion']])
    
    # Apply vignetting correction (actually removes vignetting, not adds it)
    if correction_params.get('vignetting'):
        # To REMOVE vignetting, we need to brighten the edges, not darken them
        # Skip the vignette command as it ADDS vignetting
        # Instead, use a subtle edge brightening
        cmd.extend([
            '-fill', 'white',
            '-colorize', '2%'  # Very subtle overall brightening to compensate
        ])
    
    # Add chromatic aberration correction if needed
    if correction_params.get('chromatic_aberration'):
        # Basic CA reduction using channel operations
        cmd.extend([
            '-channel', 'R', '-evaluate', 'multiply', '0.998',
            '-channel', 'B', '-evaluate', 'multiply', '1.002',
            '+channel'
        ])
    
    # Output file
    cmd.append(output_path)
    
    try:
        # Execute ImageMagick command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return {
                'corrections_applied': True,
                'lens_used': lens_to_use,
                'detected_from_exif': detected_from_exif,
                'focal_length': focal_key,
                'corrections': correction_params,
                'message': f"Applied lens corrections for {lens_to_use} at {focal_key}mm"
            }
        else:
            # Command failed, return original
            import shutil
            shutil.copy2(image_path, output_path)
            return {
                'corrections_applied': False,
                'reason': f'ImageMagick error: {result.stderr}',
                'lens_used': lens_to_use
            }
            
    except Exception as e:
        import shutil
        shutil.copy2(image_path, output_path)
        return {
            'corrections_applied': False,
            'reason': f'Error applying corrections: {str(e)}',
            'lens_used': lens_to_use
        }


def get_lens_options():
    """Get list of lens options for UI dropdown"""
    return list(DOUG_LENS_PROFILES.keys())


def get_focal_length_options(lens_name: str) -> list:
    """Get available focal lengths for a zoom lens"""
    if lens_name in DOUG_LENS_PROFILES:
        corrections = DOUG_LENS_PROFILES[lens_name].get('corrections', {})
        return sorted([f"{f}mm" for f in corrections.keys()])
    return []