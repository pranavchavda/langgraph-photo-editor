#!/usr/bin/env python3
"""
Create a side-by-side comparison of Lanczos vs AI upscaling
"""

from PIL import Image, ImageDraw, ImageFont

# Load the images
original = Image.open('/tmp/test_simple.jpg')
lanczos = Image.open('/tmp/upscaled_lanczos.png')
ai = Image.open('/tmp/upscaled_ai.png')

# Create a comparison image
width = 400 * 3 + 40  # 3 images + padding
height = 400 + 60  # image height + text space

comparison = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(comparison)

# Paste images
comparison.paste(original.resize((400, 400), Image.Resampling.NEAREST), (10, 40))
comparison.paste(lanczos, (420, 40))
comparison.paste(ai, (830, 40))

# Add labels
try:
    # Try to use a better font if available
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
except:
    font = ImageFont.load_default()

draw.text((110, 10), "Original (200x200)", fill='black', font=font)
draw.text((520, 10), "Lanczos (400x400)", fill='black', font=font)
draw.text((930, 10), "AI Upscaled (400x400)", fill='black', font=font)

# Add performance info
try:
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
except:
    small_font = ImageFont.load_default()

draw.text((110, 450), "Nearest neighbor resize", fill='gray', font=small_font)
draw.text((520, 450), "0.009 seconds", fill='gray', font=small_font)
draw.text((930, 450), "4.2 seconds", fill='gray', font=small_font)

# Save comparison
comparison.save('/tmp/upscaling_comparison.png')
print("✅ Comparison image saved to /tmp/upscaling_comparison.png")

# Also create a zoomed-in comparison for better detail
# Take a 50x50 crop from center and zoom it 4x
crop_size = 50
crop_x = 75  # Center of the green circle
crop_y = 75

zoom_width = crop_size * 4 * 3 + 40
zoom_height = crop_size * 4 + 60

zoom_comparison = Image.new('RGB', (zoom_width, zoom_height), 'white')
zoom_draw = ImageDraw.Draw(zoom_comparison)

# Crop and zoom each image
original_crop = original.crop((crop_x, crop_y, crop_x + crop_size, crop_y + crop_size))
lanczos_crop = lanczos.crop((crop_x * 2, crop_y * 2, (crop_x + crop_size) * 2, (crop_y + crop_size) * 2))
ai_crop = ai.crop((crop_x * 2, crop_y * 2, (crop_x + crop_size) * 2, (crop_y + crop_size) * 2))

# Resize for display
zoom_comparison.paste(original_crop.resize((200, 200), Image.Resampling.NEAREST), (10, 40))
zoom_comparison.paste(lanczos_crop.resize((200, 200), Image.Resampling.NEAREST), (220, 40))
zoom_comparison.paste(ai_crop.resize((200, 200), Image.Resampling.NEAREST), (430, 40))

# Add labels
zoom_draw.text((60, 10), "Original", fill='black', font=font)
zoom_draw.text((270, 10), "Lanczos", fill='black', font=font)
zoom_draw.text((460, 10), "AI Upscaled", fill='black', font=font)

zoom_comparison.save('/tmp/upscaling_zoom_comparison.png')
print("✅ Zoomed comparison saved to /tmp/upscaling_zoom_comparison.png")

print("\n📊 Comparison images created:")
print("1. Full comparison: /tmp/upscaling_comparison.png")
print("2. Zoomed detail: /tmp/upscaling_zoom_comparison.png")