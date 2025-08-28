const fs = require('fs');
const path = require('path');

class AssetPreparer {
  constructor() {
    this.electronDir = path.resolve(__dirname, '..');
    this.assetsDir = path.join(this.electronDir, 'assets');
    
    console.log('Asset Preparer Configuration:');
    console.log(`  Electron Dir: ${this.electronDir}`);
    console.log(`  Assets Dir: ${this.assetsDir}`);
  }

  async prepare() {
    console.log('\n🎨 Preparing application assets...\n');
    
    try {
      // Create assets directory
      await this.createAssetsDir();
      
      // Create application icons
      await this.createIcons();
      
      // Create entitlements for macOS
      await this.createEntitlements();
      
      // Create application metadata
      await this.createMetadata();
      
      console.log('\n✅ Asset preparation completed successfully!\n');
      console.log(`Assets created at: ${this.assetsDir}`);
      
    } catch (error) {
      console.error('\n❌ Asset preparation failed:', error.message);
      process.exit(1);
    }
  }

  async createAssetsDir() {
    if (!fs.existsSync(this.assetsDir)) {
      console.log('📁 Creating assets directory...');
      fs.mkdirSync(this.assetsDir, { recursive: true });
    }
  }

  async createIcons() {
    console.log('🖼️  Creating application icons...');
    
    // For now, we'll create placeholder icon files
    // In a real implementation, you'd want to use actual icon generation tools
    
    const iconSizes = {
      'icon.png': this.createPngIcon(),
      'icon.ico': this.createIcoIcon(),
      'icon.icns': this.createIcnsIcon()
    };
    
    for (const [filename, content] of Object.entries(iconSizes)) {
      const iconPath = path.join(this.assetsDir, filename);
      
      if (!fs.existsSync(iconPath)) {
        if (typeof content === 'string') {
          fs.writeFileSync(iconPath, content);
        } else {
          // For binary files, we'll just create a placeholder
          fs.writeFileSync(iconPath, '');
        }
        console.log(`  ✓ Created ${filename} (placeholder)`);
      } else {
        console.log(`  ✓ ${filename} already exists`);
      }
    }
    
    console.log('\n⚠️  Note: Placeholder icons created. For production, replace with actual icons.');
    console.log('   You can generate proper icons using tools like:');
    console.log('   - https://www.electron.build/icons');
    console.log('   - https://github.com/jaretburkett/electron-icon-maker');
    console.log('   - Online converters like https://iconverticons.com/online/');
  }

  createPngIcon() {
    // This is a minimal SVG that can be converted to PNG
    // In practice, you'd use a proper icon generation tool
    return `<!-- Placeholder PNG icon - replace with actual 512x512 PNG -->\n`;
  }

  createIcoIcon() {
    // Placeholder for Windows ICO file
    return `<!-- Placeholder ICO icon - replace with actual Windows ICO file -->\n`;
  }

  createIcnsIcon() {
    // Placeholder for macOS ICNS file  
    return `<!-- Placeholder ICNS icon - replace with actual macOS ICNS file -->\n`;
  }

  async createEntitlements() {
    console.log('🔐 Creating macOS entitlements...');
    
    const entitlements = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.allow-dyld-environment-variables</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.network.server</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.files.downloads.read-write</key>
    <true/>
    <key>com.apple.security.temporary-exception.files.absolute-path.read-write</key>
    <array>
      <string>/Users/</string>
      <string>/tmp/</string>
      <string>/var/folders/</string>
    </array>
  </dict>
</plist>`;

    const entitlementsPath = path.join(this.assetsDir, 'entitlements.mac.plist');
    fs.writeFileSync(entitlementsPath, entitlements);
    console.log('  ✓ Created entitlements.mac.plist');
  }

  async createMetadata() {
    console.log('📄 Creating application metadata...');
    
    // Create a simple README for the assets directory
    const readme = `# LangGraph Photo Editor Assets

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
`;

    const readmePath = path.join(this.assetsDir, 'README.md');
    fs.writeFileSync(readmePath, readme);
    console.log('  ✓ Created README.md with asset guidelines');

    // Create a simple build info file
    const buildInfo = {
      created: new Date().toISOString(),
      platform: process.platform,
      version: "1.0.0-beta.1",
      electron_version: require('../package.json').devDependencies.electron,
      notes: "Auto-generated assets for LangGraph Photo Editor"
    };

    const buildInfoPath = path.join(this.assetsDir, 'build-info.json');
    fs.writeFileSync(buildInfoPath, JSON.stringify(buildInfo, null, 2));
    console.log('  ✓ Created build-info.json');
  }
}

// Run the asset preparer if this script is called directly
if (require.main === module) {
  const preparer = new AssetPreparer();
  preparer.prepare().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = AssetPreparer;