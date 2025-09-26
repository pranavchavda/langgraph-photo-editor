"""
G'MIC Repair Agent
Uses G'MIC (GREYC's Magic for Image Computing) for advanced defect repair
Provides powerful despeckle, denoise, and inpainting capabilities
"""

import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional
import shutil


def check_gmic_available() -> bool:
    """Check if G'MIC is installed and available"""
    return shutil.which('gmic') is not None


async def gmic_repair_agent(
    image_path: str,
    mask_path: Optional[str] = None,
    repair_mode: str = "auto",
    denoise_strength: int = 30,
    despeckle_size: int = 5
) -> Dict[str, Any]:
    """
    🔧 Repair image defects using G'MIC filters
    
    Args:
        image_path: Path to image to repair
        mask_path: Optional defect mask for guided repair
        repair_mode: "auto", "dust", "scratches", "full"
        denoise_strength: Denoising strength (0-100)
        despeckle_size: Maximum size of spots to remove (pixels)
    
    Returns:
        Dictionary with:
        - success: Boolean indicating if repair succeeded
        - output_path: Path to repaired image
        - filters_applied: List of G'MIC filters used
        - message: Status message
    """
    
    # Check if G'MIC is available
    if not check_gmic_available():
        print("⚠️ G'MIC not installed, skipping repair")
        return {
            "success": False,
            "output_path": image_path,
            "message": "G'MIC not available, returning original",
            "filters_applied": []
        }
    
    try:
        # Prepare output path - preserve original format
        original_suffix = Path(image_path).suffix or '.png'
        output_path = str(Path("/tmp") / f"gmic_repaired_{Path(image_path).stem}{original_suffix}")
        filters_applied = []
        
        # Build G'MIC command
        cmd = ["gmic", image_path]
        
        if repair_mode == "auto" or repair_mode == "full":
            # Comprehensive repair pipeline - using CORRECT G'MIC syntax
            
            # 1. Remove hot pixels (mask_size, threshold%)
            cmd.extend(["-remove_hotpixels", "3,10%"])
            filters_applied.append("remove_hotpixels")
            
            # 2. Median filter to remove salt-and-pepper noise (size)
            cmd.extend(["-median", "3"])
            filters_applied.append("median(3)")
            
            # 3. Denoise - correct syntax: std_s, std_r, patch_size, lookup_size, smoothness
            cmd.extend(["-denoise", "5,5,5,6,1"])
            filters_applied.append("denoise")
            
            # 4. Final smoothing - correct syntax: amplitude, sharpness, anisotropy, alpha, sigma, dl, da
            cmd.extend(["-smooth", "5,0.7,0.3,0.6,1.1,0.8,30"])
            filters_applied.append("smooth")
            
        elif repair_mode == "dust":
            # Focus on dust removal - CORRECT syntax
            cmd.extend([
                "-remove_hotpixels", "5,10%",  # Larger mask, 10% threshold
                "-median", "2",  # Small median filter
                "-denoise", "3,3,5,6,1"  # Gentle denoise
            ])
            filters_applied.extend(["remove_hotpixels", "median", "denoise"])
            
        elif repair_mode == "scratches":
            # Focus on scratch removal
            # Use anisotropic smoothing which is good for preserving edges while removing scratches
            cmd.extend([
                "-anisotropic_smoothing", "60,0.7,0.3,0.6,1.1,0.8,30,2",
                "-median", "3"  # Median filter can help with linear defects
            ])
            filters_applied.extend(["anisotropic_smoothing", "median"])
        
        # Output
        cmd.extend(["-output", output_path])
        
        print(f"🔧 Running G'MIC repair with filters: {', '.join(filters_applied)}")
        print(f"   Command: {' '.join(cmd[:3])} ... {' '.join(cmd[-2:])}")
        
        # Execute G'MIC
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        if result.returncode != 0:
            print(f"❌ G'MIC error: {result.stderr}")
            return {
                "success": False,
                "output_path": image_path,
                "message": f"G'MIC failed: {result.stderr[:200]}",
                "filters_applied": filters_applied
            }
        
        # Verify output exists
        if not Path(output_path).exists():
            print("❌ G'MIC output not found")
            return {
                "success": False,
                "output_path": image_path,
                "message": "G'MIC did not produce output",
                "filters_applied": filters_applied
            }
        
        print(f"✅ G'MIC repair complete: {output_path}")
        return {
            "success": True,
            "output_path": output_path,
            "filters_applied": filters_applied,
            "message": f"Applied {len(filters_applied)} G'MIC filters"
        }
        
    except subprocess.TimeoutExpired:
        print("❌ G'MIC timeout")
        return {
            "success": False,
            "output_path": image_path,
            "message": "G'MIC processing timeout",
            "filters_applied": []
        }
    except Exception as e:
        print(f"❌ G'MIC error: {e}")
        return {
            "success": False,
            "output_path": image_path,
            "message": str(e),
            "filters_applied": []
        }


async def gmic_custom_filter(
    image_path: str,
    filter_command: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply custom G'MIC filter command
    
    Args:
        image_path: Input image
        filter_command: G'MIC filter command (e.g., "-blur 5 -sharpen 300")
        output_path: Optional output path
    
    Returns:
        Result dictionary
    """
    if not check_gmic_available():
        return {
            "success": False,
            "output_path": image_path,
            "message": "G'MIC not available"
        }
    
    if not output_path:
        original_suffix = Path(image_path).suffix or '.png'
        output_path = str(Path("/tmp") / f"gmic_custom_{Path(image_path).stem}{original_suffix}")
    
    try:
        # Build command
        cmd = ["gmic", image_path] + filter_command.split() + ["-output", output_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and Path(output_path).exists():
            return {
                "success": True,
                "output_path": output_path,
                "message": f"Applied custom filter: {filter_command}"
            }
        else:
            return {
                "success": False,
                "output_path": image_path,
                "message": f"Filter failed: {result.stderr[:200]}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "output_path": image_path,
            "message": str(e)
        }


# G'MIC filter presets for common repairs
GMIC_PRESETS = {
    "light_denoise": "-denoise 20,0,5,0 -smooth 1,0,1,1,2,0,0",
    "heavy_denoise": "-denoise 50,0,10,0 -bilateral 10,7",
    "remove_dust": "-remove_hotpixels 3,10 -despeckle 5 -median 2",
    "remove_scratches": "-repair_clones 20,200,0,1 -anisotropic_smoothing 60,0.7,0.3,0.6,1.1,0.8,30,2",
    "enhance_details": "-sharpen 300 -local_normalization 5,6,5,20,0,1",
    "color_enhance": "-autocolor -normalize_local 2,2,1,0,0",
    "fix_chromatic": "-chromatic_aberrations -0.5,-0.5",
    "reduce_noise_preserve_edges": "-nlmeans 4,4,10",
    "smart_blur": "-blur_anisotropic 60,0.7,0.3,0.6,1.1,0.8,30,2"
}


async def apply_gmic_preset(
    image_path: str,
    preset: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply a predefined G'MIC filter preset
    
    Args:
        image_path: Input image
        preset: Name of preset from GMIC_PRESETS
        output_path: Optional output path
    
    Returns:
        Result dictionary
    """
    if preset not in GMIC_PRESETS:
        return {
            "success": False,
            "output_path": image_path,
            "message": f"Unknown preset: {preset}. Available: {list(GMIC_PRESETS.keys())}"
        }
    
    filter_command = GMIC_PRESETS[preset]
    result = await gmic_custom_filter(image_path, filter_command, output_path)
    result["preset_used"] = preset
    return result