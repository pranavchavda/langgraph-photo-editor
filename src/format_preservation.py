"""
Format Preservation Module
Handles conversion back to original formats after processing
"""

from pathlib import Path
from typing import Optional
from PIL import Image
import os
import shutil

from .quality_config import get_quality_settings, get_save_kwargs


def preserve_original_format(
    processed_path: str,
    original_path: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Convert processed image back to original format if preservation is enabled

    Args:
        processed_path: Path to the processed image (usually WebP)
        original_path: Path to the original image
        output_dir: Optional output directory

    Returns:
        Path to the final output file
    """
    settings = get_quality_settings()

    # Check if we should preserve format
    if not settings.get("preserve_original_format", False):
        return processed_path

    # Get original format
    original_ext = Path(original_path).suffix.lower()
    processed_ext = Path(processed_path).suffix.lower()

    # If already in correct format, return
    if original_ext == processed_ext:
        return processed_path

    # Determine output path
    if output_dir:
        output_base = Path(output_dir) / Path(processed_path).name
    else:
        output_base = Path(processed_path)

    # Create output path with original extension
    output_path = output_base.with_suffix(original_ext)

    print(f"🔄 Converting back to original format: {processed_ext} → {original_ext}")

    try:
        # Special handling for AVIF
        if original_ext == '.avif':
            # Check if pillow-avif-plugin is available
            try:
                import pillow_avif

                # Open processed image and save as AVIF
                with Image.open(processed_path) as img:
                    # Get AVIF-specific save parameters
                    save_kwargs = get_save_kwargs('AVIF', settings)
                    img.save(str(output_path), **save_kwargs)

                print(f"✅ Saved as AVIF with quality {settings.get('webp_quality', 95)}")

                # Remove the WebP version if different from output
                if str(output_path) != processed_path and Path(processed_path).exists():
                    try:
                        os.remove(processed_path)
                        print(f"🧹 Removed intermediate WebP file")
                    except:
                        pass

                return str(output_path)

            except ImportError:
                print("⚠️ pillow-avif-plugin not installed, cannot save as AVIF")
                print("  To enable AVIF output: pip install pillow-avif-plugin")
                # Fall through to keep as WebP

        # For other formats, use standard PIL
        elif original_ext in ['.jpg', '.jpeg', '.png']:
            with Image.open(processed_path) as img:
                # Get format-specific save parameters
                format_name = 'JPEG' if original_ext in ['.jpg', '.jpeg'] else 'PNG'
                save_kwargs = get_save_kwargs(format_name, settings)

                # Handle transparency for JPEG
                if format_name == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB for JPEG
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    rgb_img.save(str(output_path), **save_kwargs)
                else:
                    img.save(str(output_path), **save_kwargs)

                print(f"✅ Saved as {format_name} with quality {settings.get('jpeg_quality' if format_name == 'JPEG' else 'png_compression', 95)}")

                # Remove the WebP version if different from output
                if str(output_path) != processed_path and Path(processed_path).exists():
                    try:
                        os.remove(processed_path)
                        print(f"🧹 Removed intermediate WebP file")
                    except:
                        pass

                return str(output_path)

    except Exception as e:
        print(f"❌ Failed to convert to {original_ext}: {e}")
        print(f"   Keeping as {processed_ext}")

    # If conversion failed or format not supported, keep processed version
    return processed_path


def check_resolution_preserved(original_path: str, processed_path: str) -> tuple[bool, str]:
    """
    Check if the processed image maintains the original resolution

    Returns:
        Tuple of (resolution_preserved, message)
    """
    try:
        with Image.open(original_path) as original_img:
            original_size = original_img.size

        with Image.open(processed_path) as processed_img:
            processed_size = processed_img.size

        if original_size == processed_size:
            return True, f"Resolution preserved: {original_size[0]}x{original_size[1]}"
        else:
            size_ratio = (processed_size[0] * processed_size[1]) / (original_size[0] * original_size[1])
            return False, (f"Resolution changed: {original_size[0]}x{original_size[1]} → "
                         f"{processed_size[0]}x{processed_size[1]} ({size_ratio:.1%} of original)")

    except Exception as e:
        return False, f"Could not check resolution: {e}"


def get_file_size_comparison(original_path: str, processed_path: str) -> str:
    """
    Get a comparison of file sizes
    """
    try:
        original_size = Path(original_path).stat().st_size
        processed_size = Path(processed_path).stat().st_size

        ratio = processed_size / original_size

        if ratio < 0.1:
            emoji = "⚠️"  # More than 90% reduction - might indicate problem
        elif ratio < 0.5:
            emoji = "📉"  # 50-90% reduction
        elif ratio < 0.9:
            emoji = "✅"  # 10-50% reduction - good
        elif ratio < 1.1:
            emoji = "≈"   # Similar size
        else:
            emoji = "📈"  # Larger

        return (f"{emoji} Size: {original_size / 1024 / 1024:.1f}MB → "
                f"{processed_size / 1024 / 1024:.1f}MB ({ratio:.1%})")

    except Exception as e:
        return f"Could not compare sizes: {e}"