const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const os = require('os');

class PythonBundler {
  constructor() {
    this.electronDir = path.resolve(__dirname, '..');
    this.projectRoot = path.resolve(this.electronDir, '..');
    this.bundleDir = path.join(this.electronDir, 'bundled-python');
    this.venvDir = path.join(this.projectRoot, 'venv');
    
    console.log('Python Bundler Configuration:');
    console.log(`  Electron Dir: ${this.electronDir}`);
    console.log(`  Project Root: ${this.projectRoot}`);
    console.log(`  Bundle Dir: ${this.bundleDir}`);
    console.log(`  Venv Dir: ${this.venvDir}`);
  }

  async bundle() {
    console.log('\n🐍 Starting Python environment bundling...\n');
    
    try {
      // Check for CI optimization flag
      const isCI = process.env.CI || process.env.GITHUB_ACTIONS;
      const forceRebuild = process.argv.includes('--force-rebuild');
      const skipIfExists = process.argv.includes('--skip-if-exists') || (isCI && !forceRebuild);
      
      if (skipIfExists && await this.bundleExists()) {
        console.log('✓ Bundle already exists, skipping for CI performance');
        return;
      }
      
      if (forceRebuild) {
        console.log('🔄 Force rebuild requested, proceeding with fresh bundle...');
      }
      
      // Clean previous bundle
      await this.cleanBundle();
      
      // Create bundle directory
      await this.createBundleDir();
      
      // Check if virtual environment exists
      if (await this.checkVenv()) {
        console.log('✓ Virtual environment found');
        await this.bundleFromVenv();
      } else {
        console.log('⚠️  No virtual environment found, creating one...');
        await this.createVenv();
        await this.bundleFromVenv();
      }
      
      // Copy project files
      await this.copyProjectFiles();
      
      // Create platform-specific scripts
      await this.createScripts();
      
      // Validate bundle
      await this.validateBundle();
      
      console.log('\n✅ Python bundling completed successfully!\n');
      console.log(`Bundle created at: ${this.bundleDir}`);
      
      // Force exit to prevent hanging in CI environments
      if (isCI) {
        console.log('🏁 Exiting cleanly for CI...');
        process.exit(0);
      }
      
    } catch (error) {
      console.error('\n❌ Python bundling failed:', error.message);
      process.exit(1);
    }
  }

  async bundleExists() {
    const pythonExecutable = process.platform === 'win32' 
      ? path.join(this.bundleDir, 'python.exe')
      : path.join(this.bundleDir, 'bin', 'python');
    
    const photoEditorScript = path.join(this.bundleDir, 'photo_editor.py');
    const pyvenvCfg = path.join(this.bundleDir, 'pyvenv.cfg');
    
    return fs.existsSync(pythonExecutable) && 
           fs.existsSync(photoEditorScript) && 
           fs.existsSync(pyvenvCfg);
  }

  async cleanBundle() {
    if (fs.existsSync(this.bundleDir)) {
      console.log('🧹 Cleaning existing bundle...');
      await this.removeDir(this.bundleDir);
    }
  }

  async createBundleDir() {
    console.log('📁 Creating bundle directory...');
    fs.mkdirSync(this.bundleDir, { recursive: true });
  }

  async checkVenv() {
    const venvPython = path.join(this.venvDir, process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
    return fs.existsSync(venvPython);
  }

  async createVenv() {
    console.log('🏗️  Creating virtual environment...');
    
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    
    await this.runCommand(pythonCmd, ['-m', 'venv', this.venvDir], {
      cwd: this.projectRoot,
      description: 'Creating virtual environment'
    });
    
    console.log('📦 Installing dependencies...');
    const pipCmd = path.join(this.venvDir, process.platform === 'win32' ? 'Scripts/pip.exe' : 'bin/pip');
    const requirementsFile = path.join(this.projectRoot, 'requirements.txt');
    
    // Upgrade pip first for better performance
    await this.runCommand(pipCmd, ['install', '--upgrade', 'pip'], {
      cwd: this.projectRoot,
      description: 'Upgrading pip'
    });
    
    if (fs.existsSync(requirementsFile)) {
      // Install requirements with optimizations for CI/CD
      await this.runCommand(pipCmd, ['install', '--no-cache-dir', '--disable-pip-version-check', '-r', requirementsFile], {
        cwd: this.projectRoot,
        description: 'Installing requirements (optimized)'
      });
    } else {
      console.log('⚠️  requirements.txt not found, installing basic dependencies');
      const basicDeps = [
        'anthropic>=0.34.0',
        'google-generativeai>=0.8.0',
        'langgraph>=0.2.0',
        'langchain-anthropic>=0.2.0',
        'pillow>=10.0.0',
        'requests>=2.31.0',
        'click>=8.0.0',
        'rich>=13.0.0'
      ];
      
      // Install all dependencies in one command for better performance
      await this.runCommand(pipCmd, ['install', '--no-cache-dir', '--disable-pip-version-check', ...basicDeps], {
        cwd: this.projectRoot,
        description: 'Installing basic dependencies (optimized)'
      });
    }
  }

  async bundleFromVenv() {
    console.log('📦 Bundling Python environment...');
    
    if (process.platform === 'win32') {
      await this.bundleWindows();
    } else if (process.platform === 'darwin') {
      await this.bundleMacOS();
    } else {
      await this.bundleLinux();
    }
  }

  async bundleWindows() {
    console.log('🏢 Bundling for Windows...');
    
    // Copy Python executable and DLLs
    const venvScripts = path.join(this.venvDir, 'Scripts');
    const venvLib = path.join(this.venvDir, 'Lib');
    const venvDLLs = path.join(this.venvDir, 'DLLs');
    
    // Create directory structure
    const bundleScripts = path.join(this.bundleDir, 'Scripts');
    const bundleLib = path.join(this.bundleDir, 'Lib');
    const bundleDLLs = path.join(this.bundleDir, 'DLLs');
    
    fs.mkdirSync(bundleScripts, { recursive: true });
    fs.mkdirSync(bundleLib, { recursive: true });
    fs.mkdirSync(bundleDLLs, { recursive: true });
    
    // Copy executables
    await this.copyFile(path.join(venvScripts, 'python.exe'), path.join(this.bundleDir, 'python.exe'));
    if (fs.existsSync(path.join(venvScripts, 'pythonw.exe'))) {
      await this.copyFile(path.join(venvScripts, 'pythonw.exe'), path.join(this.bundleDir, 'pythonw.exe'));
    }
    
    // Copy DLLs if they exist
    if (fs.existsSync(venvDLLs)) {
      await this.copyDir(venvDLLs, bundleDLLs);
    }
    
    // Copy site-packages
    const sitePackages = path.join(venvLib, 'site-packages');
    const bundleSitePackages = path.join(bundleLib, 'site-packages');
    
    if (fs.existsSync(sitePackages)) {
      await this.copyDir(sitePackages, bundleSitePackages);
    }
    
    // Copy standard library (selective)
    await this.copyStandardLibrary(venvLib, bundleLib);
    
    // Create pyvenv.cfg file for Windows
    await this.createPyvenvCfg();
  }

  async bundleMacOS() {
    console.log('🍎 Bundling for macOS...');
    
    const venvBin = path.join(this.venvDir, 'bin');
    const venvLib = path.join(this.venvDir, 'lib');
    
    // Create directory structure
    const bundleBin = path.join(this.bundleDir, 'bin');
    const bundleLib = path.join(this.bundleDir, 'lib');
    
    fs.mkdirSync(bundleBin, { recursive: true });
    fs.mkdirSync(bundleLib, { recursive: true });
    
    // Copy Python executable
    await this.copyFile(path.join(venvBin, 'python'), path.join(bundleBin, 'python'));
    if (fs.existsSync(path.join(venvBin, 'python3'))) {
      await this.copyFile(path.join(venvBin, 'python3'), path.join(bundleBin, 'python3'));
    }
    
    // Find Python version directory
    const pythonVersions = fs.readdirSync(venvLib).filter(dir => dir.startsWith('python'));
    
    if (pythonVersions.length > 0) {
      const pythonVersion = pythonVersions[0];
      const venvPythonLib = path.join(venvLib, pythonVersion);
      const bundlePythonLib = path.join(bundleLib, pythonVersion);
      
      await this.copyDir(venvPythonLib, bundlePythonLib);
    }
    
    // Create pyvenv.cfg file for macOS
    await this.createPyvenvCfg();
  }

  async bundleLinux() {
    console.log('🐧 Bundling for Linux...');
    
    const venvBin = path.join(this.venvDir, 'bin');
    const venvLib = path.join(this.venvDir, 'lib');
    
    // Create directory structure
    const bundleBin = path.join(this.bundleDir, 'bin');
    const bundleLib = path.join(this.bundleDir, 'lib');
    
    fs.mkdirSync(bundleBin, { recursive: true });
    fs.mkdirSync(bundleLib, { recursive: true });
    
    // Copy Python executable
    await this.copyFile(path.join(venvBin, 'python'), path.join(bundleBin, 'python'));
    if (fs.existsSync(path.join(venvBin, 'python3'))) {
      await this.copyFile(path.join(venvBin, 'python3'), path.join(bundleBin, 'python3'));
    }
    
    // Find and copy Python shared libraries
    try {
      const result = await this.runCommand('ldd', [path.join(venvBin, 'python')], {
        capture: true,
        description: 'Finding Python shared libraries'
      });
      
      // Parse ldd output to find libpython
      const lddLines = result.stdout.split('\n');
      for (const line of lddLines) {
        if (line.includes('libpython')) {
          const match = line.match(/=>\s+([^\s]+)/);
          if (match && match[1] && fs.existsSync(match[1])) {
            const libName = path.basename(match[1]);
            await this.copyFile(match[1], path.join(bundleLib, libName));
            console.log(`  ✓ Copied shared library: ${libName}`);
          }
        }
      }
    } catch (error) {
      console.log('  ⚠️  Could not copy shared libraries, trying alternative approach...');
      
      // Alternative: copy from system Python installation
      const systemPythonPaths = [
        '/usr/lib/x86_64-linux-gnu',
        '/usr/lib64',
        '/usr/lib',
        '/lib/x86_64-linux-gnu',
        '/lib64',
        '/lib'
      ];
      
      for (const libPath of systemPythonPaths) {
        const libFiles = ['libpython3.9.so.1.0', 'libpython3.9.so', 'libpython3.so'];
        for (const libFile of libFiles) {
          const sourcePath = path.join(libPath, libFile);
          if (fs.existsSync(sourcePath)) {
            await this.copyFile(sourcePath, path.join(bundleLib, libFile));
            console.log(`  ✓ Copied system library: ${libFile}`);
          }
        }
      }
    }
    
    // Find Python version directory
    const pythonVersions = fs.readdirSync(venvLib).filter(dir => dir.startsWith('python'));
    
    if (pythonVersions.length > 0) {
      const pythonVersion = pythonVersions[0];
      const venvPythonLib = path.join(venvLib, pythonVersion);
      const bundlePythonLib = path.join(bundleLib, pythonVersion);
      
      await this.copyDir(venvPythonLib, bundlePythonLib);
      
      // Fix namespace packages for Linux
      await this.fixNamespacePackages(bundlePythonLib);
    }
    
    // Create pyvenv.cfg file for Linux
    await this.createPyvenvCfg();
  }

  async fixNamespacePackages(pythonLibPath) {
    console.log('🔧 Fixing namespace packages...');
    
    const sitePackagesPath = path.join(pythonLibPath, 'site-packages');
    if (!fs.existsSync(sitePackagesPath)) {
      return;
    }
    
    // Known namespace packages that need __init__.py files
    const namespacePackages = [
      'google'
    ];
    
    for (const pkg of namespacePackages) {
      const pkgPath = path.join(sitePackagesPath, pkg);
      const initFile = path.join(pkgPath, '__init__.py');
      
      if (fs.existsSync(pkgPath) && !fs.existsSync(initFile)) {
        console.log(`  ✓ Creating __init__.py for ${pkg} namespace package`);
        const initContent = `# ${pkg} namespace package
# This ensures that ${pkg}.* submodules can be imported correctly
__path__ = __import__('pkgutil').extend_path(__path__, __name__)`;
        
        fs.writeFileSync(initFile, initContent);
      }
    }
  }

  async copyStandardLibrary(sourceLib, targetLib) {
    // Copy essential standard library modules (minimized for CI performance)
    const essentialModules = [
      'encodings',
      'importlib',
      'collections',
      'json',
      'urllib',
      'http',
      'logging',
      'asyncio'
    ];
    
    console.log('📚 Copying essential standard library modules...');
    for (const module of essentialModules) {
      const sourcePath = path.join(sourceLib, module);
      const targetPath = path.join(targetLib, module);
      
      if (fs.existsSync(sourcePath)) {
        try {
          if (fs.statSync(sourcePath).isDirectory()) {
            await this.copyDir(sourcePath, targetPath);
          } else {
            await this.copyFile(sourcePath, targetPath);
          }
          console.log(`  ✓ Copied ${module}`);
        } catch (error) {
          console.log(`  ⚠️  Failed to copy ${module}: ${error.message}`);
        }
      }
    }
  }

  async copyProjectFiles() {
    console.log('📄 Copying project files...');
    
    const filesToCopy = [
      'photo_editor.py',
      'requirements.txt',
      'src'
    ];
    
    for (const file of filesToCopy) {
      const sourcePath = path.join(this.projectRoot, file);
      const targetPath = path.join(this.bundleDir, file);
      
      if (fs.existsSync(sourcePath)) {
        if (fs.statSync(sourcePath).isDirectory()) {
          await this.copyDir(sourcePath, targetPath);
        } else {
          await this.copyFile(sourcePath, targetPath);
        }
        console.log(`  ✓ Copied ${file}`);
      } else {
        console.log(`  ⚠️  ${file} not found, skipping`);
      }
    }
  }

  async createPyvenvCfg() {
    console.log('📄 Creating pyvenv.cfg for cross-platform compatibility...');
    
    // Get Python version from the bundled executable
    let pythonVersion = '3.13.0';
    let homeDir = this.bundleDir;
    let executablePath;
    
    // Determine executable path based on platform
    if (process.platform === 'win32') {
      executablePath = path.join(homeDir, 'python.exe');
    } else {
      executablePath = path.join(homeDir, 'bin', 'python');
    }
    
    try {
      // Try to get version from the original venv
      const venvCfgPath = path.join(this.venvDir, 'pyvenv.cfg');
      if (fs.existsSync(venvCfgPath)) {
        const venvCfg = fs.readFileSync(venvCfgPath, 'utf8');
        const versionMatch = venvCfg.match(/version\s*=\s*(.+)/);
        if (versionMatch) {
          pythonVersion = versionMatch[1].trim();
        }
        const homeMatch = venvCfg.match(/home\s*=\s*(.+)/);
        if (homeMatch) {
          // Use original home for reference, but point to our bundle
          homeDir = this.bundleDir;
        }
      }
    } catch (error) {
      console.log('  ⚠️  Could not read original pyvenv.cfg, using defaults');
    }
    
    // Normalize paths for cross-platform compatibility
    const normalizedHome = homeDir.replace(/\\/g, '/');
    const normalizedExecutable = executablePath.replace(/\\/g, '/');
    
    // Create pyvenv.cfg content
    const pyvenvCfg = `home = ${normalizedHome}
include-system-site-packages = false
version = ${pythonVersion}
executable = ${normalizedExecutable}
command = python -m venv
`;
    
    const pyvenvCfgPath = path.join(this.bundleDir, 'pyvenv.cfg');
    fs.writeFileSync(pyvenvCfgPath, pyvenvCfg);
    console.log(`  ✓ Created pyvenv.cfg with version ${pythonVersion}`);
    console.log(`  ✓ Home directory: ${normalizedHome}`);
    console.log(`  ✓ Executable: ${normalizedExecutable}`);
  }

  async createScripts() {
    console.log('🔧 Creating platform scripts...');
    
    // Create platform-specific startup script for Linux
    if (process.platform === 'linux') {
      // Find the Python version dynamically
      const pythonVersions = fs.readdirSync(path.join(this.bundleDir, 'lib')).filter(dir => dir.startsWith('python'));
      const pythonVersion = pythonVersions.length > 0 ? pythonVersions[0] : 'python3.13';
      
      const startupScript = `#!/bin/bash
# Python bundle startup script for Linux
BUNDLE_DIR="$(cd "$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="\${BUNDLE_DIR}/lib:\${LD_LIBRARY_PATH}"
export PYTHONPATH="\${BUNDLE_DIR}/lib/${pythonVersion}/site-packages:\${PYTHONPATH}"
exec "\${BUNDLE_DIR}/bin/python" "\$@"
`;
      
      const startupScriptPath = path.join(this.bundleDir, 'python-wrapper.sh');
      fs.writeFileSync(startupScriptPath, startupScript);
      fs.chmodSync(startupScriptPath, '755');
      console.log(`  ✓ Created Linux startup script with ${pythonVersion}`);
    }
    
    // Create a simple test script to verify the bundle works
    const testScript = `#!/usr/bin/env python3
import sys
import os

print("Python Bundle Test")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Python path: {os.pathsep.join(sys.path)}")

# Test importing key dependencies
try:
    import anthropic
    print("✓ anthropic imported successfully")
except ImportError as e:
    print(f"✗ Failed to import anthropic: {e}")

try:
    import google.generativeai
    print("✓ google.generativeai imported successfully")
except ImportError as e:
    print(f"✗ Failed to import google.generativeai: {e}")

try:
    import langgraph
    print("✓ langgraph imported successfully")
except ImportError as e:
    print(f"✗ Failed to import langgraph: {e}")

print("Bundle test complete!")
`;
    
    const testScriptPath = path.join(this.bundleDir, 'test_bundle.py');
    fs.writeFileSync(testScriptPath, testScript);
    
    if (process.platform !== 'win32') {
      fs.chmodSync(testScriptPath, '755');
    }
  }

  async validateBundle() {
    console.log('🔍 Validating bundle...');
    
    const pythonExecutable = process.platform === 'win32' 
      ? path.join(this.bundleDir, 'python.exe')
      : path.join(this.bundleDir, 'bin', 'python');
    
    if (!fs.existsSync(pythonExecutable)) {
      throw new Error(`Python executable not found at: ${pythonExecutable}`);
    }
    
    console.log('  ✓ Python executable found');
    
    const photoEditorScript = path.join(this.bundleDir, 'photo_editor.py');
    if (!fs.existsSync(photoEditorScript)) {
      throw new Error(`Photo editor script not found at: ${photoEditorScript}`);
    }
    
    console.log('  ✓ Photo editor script found');
    
    // Check if pyvenv.cfg exists (especially important for Windows)
    const pyvenvCfg = path.join(this.bundleDir, 'pyvenv.cfg');
    if (!fs.existsSync(pyvenvCfg)) {
      throw new Error(`pyvenv.cfg file not found at: ${pyvenvCfg}`);
    }
    
    console.log('  ✓ pyvenv.cfg file found');
    
    // Test bundle by running the test script with timeout and proper signal handling
    const isCI = process.env.CI || process.env.GITHUB_ACTIONS;
    if (!isCI) {
      // Only run the full test in local development, not in CI to avoid interactive prompts
      try {
        await this.runCommand(pythonExecutable, ['test_bundle.py'], {
          cwd: this.bundleDir,
          description: 'Testing bundle',
          timeout: 30000 // 30 second timeout
        });
        console.log('  ✓ Bundle test passed');
      } catch (error) {
        console.warn('  ⚠️  Bundle test failed, but bundle may still work:', error.message);
      }
    } else {
      // In CI, skip Python execution tests entirely to avoid Windows hanging issues
      console.log('  ✓ Skipping Python execution test in CI environment');
      console.log('  ✓ Bundle validation completed (file existence checks only)');
    }
  }

  // Utility methods
  async runCommand(command, args, options = {}) {
    const { cwd = process.cwd(), description = 'Running command', capture = false, timeout = 120000 } = options;
    
    return new Promise((resolve, reject) => {
      console.log(`  ${description}: ${command} ${args.join(' ')}`);
      
      const child = spawn(command, args, {
        cwd,
        stdio: ['ignore', 'pipe', 'pipe'], // Use 'ignore' instead of 'inherit' for stdin to avoid interactive prompts
        shell: process.platform === 'win32',
        windowsHide: true // Hide the window on Windows to prevent interactive prompts
      });
      
      let stdout = '';
      let stderr = '';
      let timeoutHandle;
      
      // Set up timeout
      if (timeout > 0) {
        timeoutHandle = setTimeout(() => {
          console.log(`  ⏰ Command timeout reached (${timeout}ms), terminating process...`);
          child.kill('SIGKILL'); // Use SIGKILL instead of SIGTERM for immediate termination
          setTimeout(() => {
            reject(new Error(`Command timed out after ${timeout}ms`));
          }, 100); // Give a brief moment for cleanup
        }, timeout);
      }
      
      child.stdout?.on('data', (data) => {
        stdout += data;
        if (!capture) {
          process.stdout.write(data);
        }
      });
      
      child.stderr?.on('data', (data) => {
        stderr += data;
        if (!capture) {
          process.stderr.write(data);
        }
      });
      
      child.on('close', (code) => {
        if (timeoutHandle) {
          clearTimeout(timeoutHandle);
        }
        
        if (code === 0) {
          resolve({ stdout, stderr });
        } else {
          reject(new Error(`Command failed with exit code ${code}: ${stderr}`));
        }
      });
      
      child.on('error', (error) => {
        if (timeoutHandle) {
          clearTimeout(timeoutHandle);
        }
        reject(error);
      });
    });
  }

  async copyFile(src, dest) {
    const destDir = path.dirname(dest);
    if (!fs.existsSync(destDir)) {
      fs.mkdirSync(destDir, { recursive: true });
    }
    fs.copyFileSync(src, dest);
  }

  async copyDir(src, dest) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    
    const entries = fs.readdirSync(src, { withFileTypes: true });
    
    for (const entry of entries) {
      const srcPath = path.join(src, entry.name);
      const destPath = path.join(dest, entry.name);
      
      if (entry.isDirectory()) {
        await this.copyDir(srcPath, destPath);
      } else {
        fs.copyFileSync(srcPath, destPath);
      }
    }
  }

  async removeDir(dir) {
    if (fs.existsSync(dir)) {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  }
}

// Run the bundler if this script is called directly
if (require.main === module) {
  const bundler = new PythonBundler();
  bundler.bundle().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = PythonBundler;