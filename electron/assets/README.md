# LangGraph Photo Editor Assets

This directory contains application assets for electron-builder packaging.

## Files:

- **icon.png** - Main application icon (512x512 PNG)
- **icon.ico** - Windows application icon (ICO format)
- **icon.icns** - macOS application icon (ICNS format)
- **entitlements.mac.plist** - macOS code signing entitlements

## Icon Generation

For production builds, replace the placeholder icons with proper application icons:

1. **Create a high-resolution source image** (1024x1024 or larger)
2. **Use icon generation tools:**
   - [electron-icon-maker](https://github.com/jaretburkett/electron-icon-maker)
   - [iconverticons.com](https://iconverticons.com/online/)
   - Adobe Illustrator or similar design tools

3. **Icon specifications:**
   - PNG: 512x512 pixels, transparent background
   - ICO: Multi-resolution Windows icon (16x16 to 256x256)
   - ICNS: Multi-resolution macOS icon (16x16 to 1024x1024)

## Code Signing

For macOS distribution:
1. Join the Apple Developer Program
2. Create signing certificates
3. Update build configuration with proper signing identity
4. Test on different macOS versions

For Windows distribution:
1. Obtain a code signing certificate
2. Configure electron-builder with certificate details
3. Test installer on different Windows versions
