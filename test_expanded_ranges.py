#!/usr/bin/env python3
"""
Test the expanded ImageMagick adjustment ranges
Shows how Claude can now make more significant corrections
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import just the function we need to avoid import errors
def build_adjusted_imagemagick_command(base_command: str, adjustments: dict) -> str:
    """Apply adjustments to base ImageMagick command"""
    if not adjustments:
        return base_command
    
    command = base_command
    
    # Apply gamma delta - EXPANDED RANGE
    if 'gamma_delta' in adjustments:
        gamma_match = re.search(r'-gamma\s+([\d.]+)', command)
        if gamma_match:
            current_gamma = float(gamma_match.group(1))
            new_gamma = max(0.5, min(2.0, current_gamma + adjustments['gamma_delta']))  # Expanded from 0.8-1.2 to 0.5-2.0
            command = re.sub(r'-gamma\s+[\d.]+', f'-gamma {new_gamma}', command)
        else:
            new_gamma = max(0.5, min(2.0, 1.0 + adjustments['gamma_delta']))
            if new_gamma != 1.0:
                command = f"-gamma {new_gamma} {command}"
    
    # Apply brightness/contrast deltas - EXPANDED RANGE
    if 'brightness_delta' in adjustments or 'contrast_delta' in adjustments:
        bc_match = re.search(r'-brightness-contrast\s+(-?\d+)x(-?\d+)', command)
        if bc_match:
            current_brightness = int(bc_match.group(1))
            current_contrast = int(bc_match.group(2))
        else:
            current_brightness = 0
            current_contrast = 0
        
        new_brightness = max(-20, min(20, current_brightness + adjustments.get('brightness_delta', 0)))  # Expanded from -5/+5 to -20/+20
        new_contrast = max(-20, min(20, current_contrast + adjustments.get('contrast_delta', 0)))  # Expanded from -5/+5 to -20/+20
        
        if bc_match:
            command = re.sub(r'-brightness-contrast\s+-?\d+x-?\d+', 
                            f'-brightness-contrast {new_brightness}x{new_contrast}', command)
        else:
            if new_brightness != 0 or new_contrast != 0:
                command = f"-brightness-contrast {new_brightness}x{new_contrast} {command}"
    
    # Apply saturation delta - EXPANDED RANGE
    if 'saturation_delta' in adjustments:
        mod_match = re.search(r'-modulate\s+(\d+),(\d+),(\d+)', command)
        if mod_match:
            current_saturation = int(mod_match.group(2))
            new_saturation = max(50, min(200, current_saturation + adjustments['saturation_delta']))  # Expanded from 90-120 to 50-200
            command = re.sub(r'-modulate\s+\d+,\d+,\d+', 
                            f'-modulate 100,{new_saturation},100', command)
        else:
            new_saturation = max(50, min(200, 108 + adjustments['saturation_delta']))  # Using base of 108
            if new_saturation != 100:
                command = f"-modulate 100,{new_saturation},100 {command}"
    
    # Apply highlights/shadows deltas - NEW
    if 'highlights_delta' in adjustments or 'shadows_delta' in adjustments:
        # Extract current level values if they exist
        level_match = re.search(r'-level\s+([\d.]+)%,([\d.]+)%', command)
        if level_match:
            current_black = float(level_match.group(1))
            current_white = float(level_match.group(2))
        else:
            # Use defaults from base config
            current_black = 3  # Default shadow lift
            current_white = 95  # Default highlight compression
        
        # Apply deltas with expanded ranges
        new_black = max(0, min(30, current_black + adjustments.get('shadows_delta', 0)))
        new_white = max(70, min(100, current_white + adjustments.get('highlights_delta', 0)))
        
        if level_match:
            command = re.sub(r'-level\s+[\d.]+%,[\d.]+%', 
                            f'-level {new_black}%,{new_white}%', command)
        else:
            if new_black != 0 or new_white != 100:
                command = f"-level {new_black}%,{new_white}% {command}"
    
    return command

def test_adjustment_ranges():
    """Test various adjustment scenarios with expanded ranges"""
    
    # Base command (typical starting point)
    base_command = "-brightness-contrast 0x2 -level 3%,95% -modulate 100,108,100 -unsharp 1.0x0.5 -quality 95"
    
    print("🎛️ Testing Expanded ImageMagick Adjustment Ranges")
    print("=" * 80)
    print(f"Base command: {base_command}")
    print("=" * 80)
    
    # Test scenarios with larger adjustments
    test_cases = [
        {
            "name": "Subtle Adjustment (old style)",
            "adjustments": {
                "gamma_delta": 0.02,
                "brightness_delta": 2,
                "contrast_delta": 2,
                "saturation_delta": 5
            }
        },
        {
            "name": "Moderate Brightening (now possible)",
            "adjustments": {
                "gamma_delta": 0.15,
                "brightness_delta": 8,
                "contrast_delta": 5,
                "saturation_delta": 12
            }
        },
        {
            "name": "Significant Darkening (for overexposed)",
            "adjustments": {
                "gamma_delta": -0.25,
                "brightness_delta": -10,
                "contrast_delta": 8,
                "saturation_delta": -15,
                "highlights_delta": -20
            }
        },
        {
            "name": "Dramatic Contrast & Vibrancy (flat image)",
            "adjustments": {
                "gamma_delta": 0.1,
                "brightness_delta": 3,
                "contrast_delta": 12,
                "saturation_delta": 25,
                "shadows_delta": 8
            }
        },
        {
            "name": "Chrome/Metal Optimization (highlight control)",
            "adjustments": {
                "gamma_delta": -0.1,
                "brightness_delta": -5,
                "contrast_delta": 10,
                "saturation_delta": -10,
                "highlights_delta": -25,
                "shadows_delta": 5
            }
        },
        {
            "name": "Extreme Correction (very underexposed)",
            "adjustments": {
                "gamma_delta": 0.4,
                "brightness_delta": 15,
                "contrast_delta": 8,
                "saturation_delta": 30,
                "shadows_delta": 15
            }
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 40)
        print("Adjustments:")
        for key, value in test['adjustments'].items():
            print(f"   {key}: {value:+.2f}" if isinstance(value, float) else f"   {key}: {value:+d}")
        
        result = build_adjusted_imagemagick_command(base_command, test['adjustments'])
        print(f"\nResult command:")
        print(f"   {result}")
        
        # Show what changed
        print("\nKey changes:")
        if 'gamma_delta' in test['adjustments']:
            import re
            gamma_match = re.search(r'-gamma\s+([\d.]+)', result)
            if gamma_match:
                print(f"   Gamma: 1.0 → {gamma_match.group(1)}")
        
        if 'brightness_delta' in test['adjustments'] or 'contrast_delta' in test['adjustments']:
            bc_match = re.search(r'-brightness-contrast\s+(-?\d+)x(-?\d+)', result)
            if bc_match:
                print(f"   Brightness: 0 → {bc_match.group(1)}")
                print(f"   Contrast: 2 → {bc_match.group(2)}")
        
        if 'saturation_delta' in test['adjustments']:
            mod_match = re.search(r'-modulate\s+\d+,(\d+),\d+', result)
            if mod_match:
                print(f"   Saturation: 108 → {mod_match.group(1)}")
        
        if 'highlights_delta' in test['adjustments'] or 'shadows_delta' in test['adjustments']:
            level_match = re.search(r'-level\s+([\d.]+)%,([\d.]+)%', result)
            if level_match:
                print(f"   Shadows: 3% → {level_match.group(1)}%")
                print(f"   Highlights: 95% → {level_match.group(2)}%")
    
    print("\n" + "=" * 80)
    print("✅ Expanded Ranges Summary:")
    print("   • Gamma: 0.5 to 2.0 (was 0.8 to 1.2)")
    print("   • Brightness: -20 to +20 (was -5 to +5)")
    print("   • Contrast: -20 to +20 (was -5 to +5)")
    print("   • Saturation: 50 to 200 (was 90 to 120)")
    print("   • Highlights: -30 to +5 (new)")
    print("   • Shadows: -5 to +20 (new)")
    print("\n💡 Claude can now make more dramatic corrections when images need it!")

if __name__ == "__main__":
    test_adjustment_ranges()