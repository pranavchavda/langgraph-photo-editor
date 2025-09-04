"""
Advanced Lens Correction Module using lensfunpy
Falls back to ImageMagick if lensfunpy is not available
"""

import subprocess
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image
from PIL.ExifTags import TAGS, IFD
import numpy as np

# Try to import lensfunpy
LENSFUNPY_AVAILABLE = False
try:
    import lensfunpy as lf
    LENSFUNPY_AVAILABLE = True
    print("✓ lensfunpy available for advanced lens corrections")
except ImportError:
    print("ℹ lensfunpy not available, will use fallback methods")

def get_image_exif_data(image_path: str) -> Dict:
    """Extract EXIF data from image including lens information"""
    try:
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
                # Handle tuple values from LensSpecification
                if isinstance(lens_value, (tuple, list)) and len(lens_value) >= 2:
                    min_focal = lens_value[0] if lens_value[0] else 0
                    max_focal = lens_value[1] if lens_value[1] else 0
                    if min_focal and max_focal:
                        if min_focal == max_focal:
                            lens_model = f"{int(min_focal)}mm"
                        else:
                            lens_model = f"{int(min_focal)}-{int(max_focal)}mm"
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
            if hasattr(focal_value, 'real'):
                focal_length = float(focal_value.real)
            else:
                focal_length = float(focal_value)
        elif 'FocalLengthIn35mmFilm' in exif_dict:
            focal_length = float(exif_dict['FocalLengthIn35mmFilm'])
        
        # Get aperture
        aperture = None
        if 'FNumber' in exif_dict:
            f_value = exif_dict['FNumber']
            if hasattr(f_value, 'real'):
                aperture = float(f_value.real)
            else:
                aperture = float(f_value)
        
        return {
            'lens_model': lens_model,
            'focal_length': focal_length,
            'aperture': aperture,
            'camera_make': exif_dict.get('Make'),
            'camera_model': exif_dict.get('Model')
        }
    except Exception as e:
        print(f"Error reading EXIF data: {e}")
        return {}


def apply_lensfunpy_corrections(image_path: str, output_path: str, exif_data: Dict) -> bool:
    """Apply lens corrections using lensfunpy library"""
    if not LENSFUNPY_AVAILABLE:
        return False
    
    try:
        # Load image
        img = Image.open(image_path)
        img_array = np.array(img)
        height, width = img_array.shape[:2]
        
        # Initialize lensfun database
        db = lf.Database()
        
        # Try to find camera - use any Sony camera as a fallback
        camera = None
        if exif_data.get('camera_make') and exif_data.get('camera_model'):
            cameras = db.find_cameras(
                exif_data['camera_make'], 
                exif_data['camera_model']
            )
            if cameras:
                camera = cameras[0]
                print(f"Found camera: {camera.maker} {camera.model}")
        
        # If no exact camera match, use any Sony camera for FE lens compatibility
        if not camera and exif_data.get('camera_make') and 'sony' in exif_data['camera_make'].lower():
            # Get all cameras and find a Sony one
            all_cameras = db.cameras
            sony_cameras = [cam for cam in all_cameras if 'Sony' in cam.maker]
            if sony_cameras:
                # Prefer a camera that's not a Cybershot (those are compact cameras)
                non_cybershot = [cam for cam in sony_cameras if 'Cybershot' not in cam.model]
                camera = non_cybershot[0] if non_cybershot else sony_cameras[0]
                print(f"Using fallback camera: {camera.maker} {camera.model}")
        
        # Try to find lens
        lens = None
        if exif_data.get('lens_model'):
            lens_model_str = str(exif_data['lens_model'])
            
            # Try exact search first
            if camera:
                lenses = db.find_lenses(camera, None, lens_model_str)
            else:
                # Search without camera constraint
                all_lenses = db.lenses
                lenses = [l for l in all_lenses if lens_model_str.lower() in l.model.lower()]
            
            if not lenses:
                # Try searching for FE prefix specifically
                if 'FE' in lens_model_str:
                    if camera:
                        lenses = db.find_lenses(camera, None, 'FE')
                        # Filter to match our specific lens
                        lenses = [l for l in lenses if any(part in l.model for part in lens_model_str.split() if 'mm' in part or 'f/' in part.lower())]
                    else:
                        all_lenses = db.lenses
                        lenses = [l for l in all_lenses if 'FE' in l.model and any(part in l.model for part in lens_model_str.split() if 'mm' in part or 'f/' in part.lower())]
                
                # Try searching for key focal length and aperture
                if not lenses:
                    import re
                    # Extract focal length range (e.g., "24-70" or "90")
                    focal_match = re.search(r'(\d+)(?:-(\d+))?mm', lens_model_str)
                    aperture_match = re.search(r'f/?([\d.]+)', lens_model_str, re.IGNORECASE)
                    
                    if focal_match:
                        focal_str = focal_match.group(0)  # e.g., "24-70mm" or "90mm"
                        all_lenses = db.lenses
                        # Search for Sony FE lenses with matching focal length
                        lenses = [l for l in all_lenses if 'Sony' in l.maker and 'FE' in l.model and focal_str in l.model]
                        
                        # Further filter by aperture if available
                        if aperture_match and lenses:
                            aperture_str = f"f/{aperture_match.group(1)}"
                            filtered = [l for l in lenses if aperture_str in l.model or aperture_str.replace('/', '') in l.model]
                            if filtered:
                                lenses = filtered
            
            if lenses:
                lens = lenses[0]
                print(f"Found lens profile: {lens.maker} {lens.model}")
        
        if not lens:
            print("No lens profile found in lensfun database")
            return False
        
        # Create modifier
        focal_length = exif_data.get('focal_length', lens.min_focal)
        aperture = exif_data.get('aperture', lens.min_aperture)
        
        mod = lf.Modifier(lens, lens.crop_factor, width, height)
        # Initialize with normal scale
        mod.initialize(
            focal_length,
            aperture,
            1.0,  # distance (1.0 = infinity focus)
            1.0,  # scale
            # Don't pass lens type and flags - let lensfunpy use defaults
        )
        
        # Apply corrections
        # Convert to float32 for processing
        img_float = img_array.astype(np.float32) / 255.0
        
        # Skip geometric corrections - they're too aggressive for Sony FE lenses
        # and cause severe cropping. We'll only use vignetting correction from lensfunpy
        print("Skipping lensfunpy geometry distortion - too aggressive for this lens")
        coords = None
        if coords is not None:
            from scipy.ndimage import map_coordinates
            
            # Reshape coordinates for map_coordinates
            coords = coords.reshape(height, width, 2)
            
            # Check if coordinates go outside bounds
            x_coords = coords[:, :, 0]
            y_coords = coords[:, :, 1]
            
            x_min, x_max = x_coords.min(), x_coords.max()
            y_min, y_max = y_coords.min(), y_coords.max()
            
            print(f"Coordinate bounds: X[{x_min:.1f}, {x_max:.1f}], Y[{y_min:.1f}, {y_max:.1f}] for image {width}x{height}")
            
            # Calculate padding needed to preserve all content
            pad_left = int(max(0, -x_min))
            pad_right = int(max(0, x_max - width + 1))
            pad_top = int(max(0, -y_min))
            pad_bottom = int(max(0, y_max - height + 1))
            
            if pad_left > 0 or pad_right > 0 or pad_top > 0 or pad_bottom > 0:
                print(f"Adding padding to preserve content: L={pad_left}, R={pad_right}, T={pad_top}, B={pad_bottom}")
                
                # Pad the image to accommodate the distortion
                padded_shape = (
                    height + pad_top + pad_bottom,
                    width + pad_left + pad_right,
                    img_float.shape[2] if len(img_float.shape) > 2 else 1
                )
                
                # Create padded image filled with edge colors
                if len(img_float.shape) > 2:
                    padded_img = np.zeros(padded_shape, dtype=np.float32)
                    # Fill with edge colors instead of black
                    padded_img[:, :] = img_float[0, 0]  # Use top-left pixel as fill
                    # Place original image in the center of padded canvas
                    padded_img[pad_top:pad_top+height, pad_left:pad_left+width] = img_float
                else:
                    padded_img = np.pad(img_float, ((pad_top, pad_bottom), (pad_left, pad_right)), 
                                      mode='edge')
                
                # Adjust coordinates for the padded image
                coords[:, :, 0] += pad_left
                coords[:, :, 1] += pad_top
                
                # Apply distortion to padded image
                # map_coordinates returns array same shape as coords (height, width)
                # not the shape of the input padded image
                corrected = np.zeros((height, width, img_float.shape[2] if len(img_float.shape) > 2 else 1), dtype=np.float32)
                for channel in range(img_float.shape[2] if len(img_float.shape) > 2 else 1):
                    if len(img_float.shape) > 2:
                        corrected[:, :, channel] = map_coordinates(
                            padded_img[:, :, channel],
                            [coords[:, :, 1], coords[:, :, 0]],
                            order=1,
                            mode='constant',
                            cval=padded_img[:, :, channel].mean()
                        )
                    else:
                        corrected = map_coordinates(
                            padded_img,
                            [coords[:, :, 1], coords[:, :, 0]],
                            order=1,
                            mode='constant',
                            cval=padded_img.mean()
                        )
                
                # The corrected image is already at original size
                img_float = corrected
                print(f"Corrected image size: {img_float.shape[:2]}")
                
            else:
                # No padding needed, apply directly
                print("No padding needed - applying distortion directly")
                corrected = np.zeros_like(img_float)
                for channel in range(img_float.shape[2] if len(img_float.shape) > 2 else 1):
                    if len(img_float.shape) > 2:
                        corrected[:, :, channel] = map_coordinates(
                            img_float[:, :, channel],
                            [coords[:, :, 1], coords[:, :, 0]],
                            order=1,
                            mode='reflect'
                        )
                    else:
                        corrected = map_coordinates(
                            img_float,
                            [coords[:, :, 1], coords[:, :, 0]],
                            order=1,
                            mode='reflect'
                        )
                img_float = corrected
        
        # Apply vignetting correction
        # Note: apply_color_modification modifies the array in-place and returns an integer status
        try:
            status = mod.apply_color_modification(img_float)
            if status:
                print(f"Applied vignetting correction (status: {status})")
            else:
                print("No vignetting correction needed or available")
        except Exception as e:
            print(f"Warning: Could not apply vignetting correction: {e}")
        
        # Convert back to uint8
        if isinstance(img_float, np.ndarray):
            img_corrected = (img_float * 255).clip(0, 255).astype(np.uint8)
        else:
            print(f"Error: img_float is not an array, it's {type(img_float)}")
            return False
        
        # Save corrected image
        Image.fromarray(img_corrected).save(output_path)
        
        return True
        
    except Exception as e:
        print(f"Error applying lensfunpy corrections: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# Doug's manual lens profiles for fallback
DOUG_LENS_PROFILES = {
    "Sony FE 24-70mm F2.8 GM": {
        "display_name": "Sony FE 24-70mm F2.8 GM",
        "exif_names": ["FE 24-70mm F2.8 GM", "Sony FE 24-70mm F2.8 GM OSS", "24-70mm F2.8"],
        "corrections": {
            "24": {
                "distortion": "0.028 -0.073 0.022",
                "vignetting": "80x80+15+15",
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
            "70": {
                "distortion": "-0.012 0.018 -0.005",
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
                "distortion": "-0.008 0.012 -0.003",
                "vignetting": "30x30+8+8",
                "chromatic_aberration": True
            }
        }
    },
    "Sony FE 50mm F1.4 GM": {
        "display_name": "Sony FE 50mm F1.4 GM",
        "exif_names": ["FE 50mm F1.4 GM", "Sony FE 50mm F1.4 GM", "50mm F1.4"],
        "corrections": {
            "50": {
                "distortion": "0.005 -0.018 0.005",
                "vignetting": "70x70+15+15",
                "chromatic_aberration": True
            }
        }
    },
    "Sony FE 70-200mm F2.8 GM": {
        "display_name": "Sony FE 70-200mm F2.8 GM",
        "exif_names": ["FE 70-200mm F2.8 GM OSS", "Sony FE 70-200mm F2.8 GM", "70-200mm F2.8"],
        "corrections": {
            "70": {
                "distortion": "-0.005 0.008 -0.002",
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
                "distortion": "-0.015 0.020 -0.005",
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


def apply_imagemagick_corrections(image_path: str, output_path: str, correction_params: Dict) -> bool:
    """Apply lens corrections using ImageMagick as fallback"""
    try:
        # Check if ImageMagick is available
        from src.agents_enhanced import get_imagemagick_command
        magick_cmd = get_imagemagick_command()
        
        if not magick_cmd:
            print("⚠️ ImageMagick not found - lens corrections cannot be applied")
            print("  To enable lens corrections, ImageMagick must be installed on the system")
            return False
        
        # Build ImageMagick command
        cmd = [magick_cmd, image_path]
        
        # IMPORTANT: Set virtual pixel method to prevent cropping during distortion
        cmd.extend(['-virtual-pixel', 'edge'])
        
        # Apply distortion correction
        if correction_params.get('distortion'):
            # Use +distort to preserve the full image canvas
            cmd.extend(['+distort', 'Barrel', correction_params['distortion']])
        
        # Skip vignetting command as it ADDS vignetting instead of removing it
        # To REMOVE vignetting, we would need to brighten edges, not darken them
        if correction_params.get('vignetting'):
            # Very subtle overall brightening to compensate for vignetting
            cmd.extend([
                '-fill', 'white',
                '-colorize', '2%'
            ])
        
        # Apply chromatic aberration correction
        if correction_params.get('chromatic_aberration'):
            cmd.extend([
                '-channel', 'R', '-evaluate', 'multiply', '0.998',
                '-channel', 'B', '-evaluate', 'multiply', '1.002',
                '+channel'
            ])
        
        cmd.append(output_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"⚠️ ImageMagick lens correction failed with error:")
            print(f"  {result.stderr}")
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error applying ImageMagick corrections: {e}")
        return False


def detect_lens_from_exif(image_path: str, exif_data: Dict) -> Optional[str]:
    """Try to detect which of Doug's lenses was used based on EXIF data"""
    if not exif_data.get('lens_model'):
        return None
    
    lens_model_exif = str(exif_data['lens_model']).upper()
    # Keep the original for comparison (don't replace hyphens in focal ranges)
    lens_model_normalized = lens_model_exif
    
    # Check each lens profile
    for lens_key, profile in DOUG_LENS_PROFILES.items():
        if lens_key == "None (Auto-detect from EXIF)":
            continue
        
        for exif_name in profile['exif_names']:
            if exif_name.upper() in lens_model_normalized or lens_model_normalized in exif_name.upper():
                print(f"Auto-detected lens: {lens_key}")
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
    Priority: 1. lensfunpy (if available), 2. ImageMagick, 3. Copy original
    """
    
    # Get EXIF data
    exif_data = get_image_exif_data(image_path)
    
    # Determine which lens to use
    lens_to_use = None
    detected_from_exif = False
    
    if selected_lens and selected_lens != "None (Auto-detect from EXIF)":
        lens_to_use = selected_lens
    else:
        lens_to_use = detect_lens_from_exif(image_path, exif_data)
        detected_from_exif = True
        
        if lens_to_use and not focal_length:
            focal_length = exif_data.get('focal_length')
    
    # Skip lensfunpy - it causes severe cropping issues with Sony FE lenses
    # The geometry distortion correction is too aggressive for pre-cropped JPEGs
    # if LENSFUNPY_AVAILABLE and exif_data:
    #     print("Attempting lens corrections with lensfunpy...")
    #     if apply_lensfunpy_corrections(image_path, output_path, exif_data):
    #         return {
    #             'corrections_applied': True,
    #             'method': 'lensfunpy',
    #             'lens_used': lens_to_use or exif_data.get('lens_model'),
    #             'detected_from_exif': detected_from_exif or bool(exif_data.get('lens_model')),
    #             'focal_length': focal_length or exif_data.get('focal_length'),
    #             'message': f"Applied professional lens corrections using lensfun database"
    #         }
    
    # Fall back to manual profiles with ImageMagick
    if lens_to_use and lens_to_use in DOUG_LENS_PROFILES:
        profile = DOUG_LENS_PROFILES[lens_to_use]
        corrections = profile.get('corrections', {})
        
        if corrections:
            # Get appropriate corrections based on focal length
            if len(corrections) > 1 and focal_length:
                focal_key = get_closest_focal_length(focal_length, list(corrections.keys()))
            else:
                focal_key = list(corrections.keys())[0]
            
            correction_params = corrections[focal_key]
            
            print(f"Attempting lens corrections with ImageMagick for {lens_to_use} at {focal_key}mm...")
            if apply_imagemagick_corrections(image_path, output_path, correction_params):
                return {
                    'corrections_applied': True,
                    'method': 'imagemagick',
                    'lens_used': lens_to_use,
                    'detected_from_exif': detected_from_exif,
                    'focal_length': focal_key,
                    'corrections': correction_params,
                    'message': f"Applied lens corrections for {lens_to_use} at {focal_key}mm"
                }
    
    # No corrections applied, copy original
    import shutil
    shutil.copy2(image_path, output_path)
    
    reason = 'No lens corrections available or applicable'
    if lens_to_use:
        reason = f'Lens detected ({lens_to_use}) but ImageMagick not available for corrections'
    
    print(f"⚠️ {reason}")
    
    return {
        'corrections_applied': False,
        'reason': reason,
        'lens_used': lens_to_use,
        'detected_from_exif': detected_from_exif,
        'focal_length': focal_length
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