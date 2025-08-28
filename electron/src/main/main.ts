import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

// Disable GPU acceleration in headless environments or if GPU is not available
if (process.env.CI || process.env.DISPLAY === undefined || process.env.HEADLESS) {
  app.disableHardwareAcceleration();
}

interface ProcessingJob {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  inputPath: string;
  outputPath?: string;
  progress: ProcessingProgress;
  process?: ChildProcess;
}

interface ProcessingProgress {
  stage: string;
  message: string;
  agentStatus: {
    analysis: 'pending' | 'running' | 'completed' | 'error';
    background: 'pending' | 'running' | 'completed' | 'error';
    gemini: 'pending' | 'running' | 'completed' | 'error';
    imagemagick: 'pending' | 'running' | 'completed' | 'error';
    qc: 'pending' | 'running' | 'completed' | 'error';
  };
  qualityScore?: number;
  strategy?: string;
}

class PhotoEditorMain {
  private mainWindow: BrowserWindow | null = null;
  private jobs: Map<string, ProcessingJob> = new Map();
  private pythonExecutable: string = 'python';
  private photoEditorScript: string = '';
  private projectRoot: string = '';

  constructor() {
    this.initializePaths();
    this.setupApp();
  }

  private initializePaths() {
    // Determine if we're in development or production
    const isDev = process.env.NODE_ENV === 'development';
    
    if (isDev) {
      // Development: Find the project root (go up from electron/dist/main or electron/src/main)
      this.projectRoot = path.resolve(__dirname, '..', '..', '..');
      
      // Check for virtual environment first, fallback to system Python
      const venvPython = path.join(this.projectRoot, 'venv', 'bin', 'python');
      const venvPythonWin = path.join(this.projectRoot, 'venv', 'Scripts', 'python.exe');
      
      if (fs.existsSync(venvPython)) {
        this.pythonExecutable = venvPython;
      } else if (fs.existsSync(venvPythonWin)) {
        this.pythonExecutable = venvPythonWin;
      } else {
        // Fallback to system Python
        this.pythonExecutable = process.platform === 'win32' ? 'python.exe' : 'python3';
      }

      this.photoEditorScript = path.join(this.projectRoot, 'photo_editor.py');
    } else {
      // Production: Use bundled Python from app resources
      const appPath = app.getAppPath();
      const resourcesPath = process.resourcesPath || appPath;
      
      // Look for bundled Python in extraResources
      const bundledPythonPath = path.join(resourcesPath, 'bundled-python');
      
      if (fs.existsSync(bundledPythonPath)) {
        // Use bundled Python
        this.projectRoot = bundledPythonPath;
        
        // Platform-specific Python executable paths
        if (process.platform === 'win32') {
          this.pythonExecutable = path.join(bundledPythonPath, 'python.exe');
          // Also check in Scripts subdirectory
          if (!fs.existsSync(this.pythonExecutable)) {
            this.pythonExecutable = path.join(bundledPythonPath, 'Scripts', 'python.exe');
          }
        } else {
          this.pythonExecutable = path.join(bundledPythonPath, 'bin', 'python');
          // Fallback to python3
          if (!fs.existsSync(this.pythonExecutable)) {
            this.pythonExecutable = path.join(bundledPythonPath, 'bin', 'python3');
          }
        }
        
        this.photoEditorScript = path.join(bundledPythonPath, 'photo_editor.py');
      } else {
        // Fallback: try app directory structure
        this.projectRoot = appPath;
        this.pythonExecutable = process.platform === 'win32' ? 'python.exe' : 'python3';
        this.photoEditorScript = path.join(appPath, 'photo_editor.py');
      }
    }
    
    // Verify the script exists
    if (!fs.existsSync(this.photoEditorScript)) {
      console.error(`Photo editor script not found at: ${this.photoEditorScript}`);
    }
    
    // Verify Python executable exists (for bundled Python)
    if (!isDev && !fs.existsSync(this.pythonExecutable)) {
      console.error(`Python executable not found at: ${this.pythonExecutable}`);
    }
    
    console.log(`Development mode: ${isDev}`);
    console.log(`Project root: ${this.projectRoot}`);
    console.log(`Using Python: ${this.pythonExecutable}`);
    console.log(`Using script: ${this.photoEditorScript}`);
    console.log(`Python exists: ${fs.existsSync(this.pythonExecutable)}`);
    console.log(`Script exists: ${fs.existsSync(this.photoEditorScript)}`);
  }

  private setupApp() {
    // This method will be called when Electron has finished initialization
    app.whenReady().then(() => {
      this.createWindow();

      app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
          this.createWindow();
        }
      });
    });

    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') {
        app.quit();
      }
    });

    this.setupIPC();
  }

  private createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      minWidth: 1000,
      minHeight: 700,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'),
      },
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
      icon: this.getAppIcon(),
    });

    // Load the renderer
    if (process.env.NODE_ENV === 'development') {
      this.mainWindow.loadURL('http://localhost:3000');
      this.mainWindow.webContents.openDevTools();
    } else {
      this.mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));
    }

    // Handle external links
    this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
      shell.openExternal(url);
      return { action: 'deny' };
    });
  }

  private getAppIcon(): string {
    const iconsPath = path.join(__dirname, '..', '..', 'assets');
    
    if (process.platform === 'darwin') {
      return path.join(iconsPath, 'icon.icns');
    } else if (process.platform === 'win32') {
      return path.join(iconsPath, 'icon.ico');
    } else {
      return path.join(iconsPath, 'icon.png');
    }
  }

  private setupIPC() {
    // File operations
    ipcMain.handle('select-files', async () => {
      const result = await dialog.showOpenDialog(this.mainWindow!, {
        properties: ['openFile', 'multiSelections'],
        filters: [
          { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'webp'] },
          { name: 'All Files', extensions: ['*'] }
        ]
      });
      
      return result.canceled ? [] : result.filePaths;
    });

    ipcMain.handle('select-directory', async () => {
      const result = await dialog.showOpenDialog(this.mainWindow!, {
        properties: ['openDirectory']
      });
      
      return result.canceled ? null : result.filePaths[0];
    });

    ipcMain.handle('save-directory', async () => {
      const result = await dialog.showOpenDialog(this.mainWindow!, {
        properties: ['openDirectory', 'createDirectory']
      });
      
      return result.canceled ? null : result.filePaths[0];
    });

    // Processing operations
    ipcMain.handle('start-processing', async (event, options: {
      inputPath: string;
      outputDir?: string;
      instructions?: string;
      mode: 'single' | 'batch';
    }) => {
      return this.startProcessing(options);
    });

    ipcMain.handle('cancel-job', async (event, jobId: string) => {
      return this.cancelJob(jobId);
    });

    ipcMain.handle('get-job-status', async (event, jobId: string) => {
      return this.getJobStatus(jobId);
    });

    ipcMain.handle('get-all-jobs', async () => {
      return this.getSerializableJobs();
    });

    // Settings operations
    ipcMain.handle('load-settings', async () => {
      return this.loadSettings();
    });

    ipcMain.handle('save-settings', async (event, settings: any) => {
      return this.saveSettings(settings);
    });

    // API key validation for setup wizard
    ipcMain.handle('validate-api-key', async (event, provider: string, key: string) => {
      return this.validateAPIKey(provider, key);
    });

    // System info
    ipcMain.handle('get-system-info', async () => {
      return {
        platform: process.platform,
        arch: process.arch,
        nodeVersion: process.version,
        electronVersion: process.versions.electron,
        pythonExecutable: this.pythonExecutable,
        photoEditorScript: this.photoEditorScript,
        projectRoot: this.projectRoot,
        scriptExists: fs.existsSync(this.photoEditorScript)
      };
    });

    // Platform info (lightweight for UI styling)
    ipcMain.handle('get-platform', async () => {
      return process.platform;
    });

    // Open file/folder in system
    ipcMain.handle('show-in-folder', async (event, filePath: string) => {
      shell.showItemInFolder(filePath);
    });

    // Save file data for drag-and-drop files
    ipcMain.handle('save-file-data', async (event, options: { fileName: string; fileData: ArrayBuffer }) => {
      return this.saveFileData(options.fileName, options.fileData);
    });
  }

  private async startProcessing(options: {
    inputPath: string;
    outputDir?: string;
    instructions?: string;
    mode: 'single' | 'batch';
  }): Promise<string> {
    // Validate input path
    if (!options.inputPath || options.inputPath.trim() === '') {
      throw new Error('Input path is required and cannot be empty');
    }

    // Check if input path exists
    if (!fs.existsSync(options.inputPath)) {
      throw new Error(`Input path does not exist: ${options.inputPath}`);
    }

    const jobId = this.generateJobId();
    const job: ProcessingJob = {
      id: jobId,
      status: 'pending',
      inputPath: options.inputPath,
      progress: {
        stage: 'initializing',
        message: 'Starting processing...',
        agentStatus: {
          analysis: 'pending',
          background: 'pending',
          gemini: 'pending',
          imagemagick: 'pending',
          qc: 'pending'
        }
      }
    };

    this.jobs.set(jobId, job);

    // Set up output directory - prefer input directory, fallback to user's Documents or temp
    let outputDir: string;
    
    if (options.outputDir) {
      outputDir = options.outputDir;
    } else {
      // Determine output directory based on input path
      const inputStats = fs.statSync(options.inputPath);
      
      if (inputStats.isFile()) {
        // For single files, use the directory containing the input file
        outputDir = path.dirname(options.inputPath);
        
        // If input is in a temp directory (drag-and-drop), use Documents/Pictures
        if (outputDir.includes(os.tmpdir()) || outputDir.includes('temp') || outputDir.includes('Temp')) {
          const userHome = os.homedir();
          const documentsDir = path.join(userHome, 'Documents', 'Agentic Photo Editor');
          const picturesDir = path.join(userHome, 'Pictures', 'Agentic Photo Editor');
          
          // Try Pictures first (more appropriate for images), fallback to Documents
          if (fs.existsSync(path.join(userHome, 'Pictures'))) {
            outputDir = picturesDir;
          } else {
            outputDir = documentsDir;
          }
        }
      } else {
        // For directories (batch mode), use the input directory itself
        outputDir = options.inputPath;
      }
    }
    
    // Ensure output directory exists
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    job.outputPath = outputDir;

    // Build command arguments - use relative path since we're setting cwd
    const args = ['photo_editor.py'];
    
    // Add the command mode and input path
    if (options.mode === 'single') {
      args.push('process');
      args.push(options.inputPath);
    } else {
      args.push('batch');
      args.push(options.inputPath);
    }

    // Always add output directory and JSON output flag
    args.push('--output-dir', outputDir);
    args.push('--json-output');

    // Add instructions if provided
    if (options.instructions && options.instructions.trim() !== '') {
      args.push('--instructions', options.instructions);
    }

    // Debug logging
    console.log('Processing options:', {
      mode: options.mode,
      inputPath: options.inputPath,
      outputDir: outputDir,
      instructions: options.instructions,
      inputPathExists: fs.existsSync(options.inputPath)
    });
    console.log('Command args:', args);

    // Prepare environment with virtual environment paths
    const processEnv = { ...process.env };
    
    // If using venv Python, update PATH to include venv/bin
    if (this.pythonExecutable.includes('venv')) {
      const venvBinDir = path.dirname(this.pythonExecutable);
      processEnv.PATH = `${venvBinDir}${path.delimiter}${processEnv.PATH}`;
      processEnv.VIRTUAL_ENV = path.dirname(venvBinDir);
    }

    console.log(`Starting process: ${this.pythonExecutable} ${args.join(' ')}`);
    console.log(`Working directory: ${this.projectRoot}`);
    console.log(`Environment VIRTUAL_ENV: ${processEnv.VIRTUAL_ENV}`);

    // Start Python process
    try {
      const childProcess = spawn(this.pythonExecutable, args, {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: this.projectRoot,  // Set working directory to project root
        env: processEnv
      });

      job.process = childProcess;
      job.status = 'running';

      // Handle stdout (progress updates)
      childProcess.stdout?.on('data', (data) => {
        this.handleProcessOutput(jobId, data.toString());
      });

      // Handle stderr (errors)
      childProcess.stderr?.on('data', (data) => {
        console.error(`Job ${jobId} error:`, data.toString());
        this.handleProcessError(jobId, data.toString());
      });

      // Handle process completion
      childProcess.on('close', (code) => {
        const job = this.jobs.get(jobId);
        if (job) {
          job.status = code === 0 ? 'completed' : 'failed';
          job.process = undefined;
          
          // Find the output file if processing succeeded
          if (code === 0 && job.outputPath) {
            try {
              const files = fs.readdirSync(job.outputPath);
              const imageFiles = files.filter(f => /\.(jpg|jpeg|png|webp)$/i.test(f));
              if (imageFiles.length > 0) {
                job.outputPath = path.join(job.outputPath, imageFiles[0]);
              }
            } catch (error) {
              console.error('Failed to find output file:', error);
            }
          }
          
          this.mainWindow?.webContents.send('job-completed', {
            jobId,
            success: code === 0,
            finalStatus: job.progress,
            outputPath: job.outputPath
          });
        }
      });

      return jobId;
    } catch (error) {
      job.status = 'failed';
      console.error('Failed to start processing:', error);
      throw error;
    }
  }

  private handleProcessOutput(jobId: string, output: string) {
    const job = this.jobs.get(jobId);
    if (!job) return;

    // Parse JSON progress updates from Python script
    const lines = output.split('\n').filter(line => line.trim());
    
    for (const line of lines) {
      try {
        // Look for JSON objects that contain progress info
        if (line.trim().startsWith('{') && line.trim().endsWith('}')) {
          const progressData = JSON.parse(line.trim());
          
          // Update job progress based on the data structure
          this.updateJobProgress(jobId, progressData);
        } else {
          // Non-JSON output - ignore in JSON mode or log for debugging
          console.log(`Job ${jobId} output: ${line}`);
        }
      } catch (error) {
        // If JSON parsing fails, it might be regular output
        console.log(`Job ${jobId} non-JSON output: ${line}`);
      }
    }
  }

  private updateJobProgress(jobId: string, progressData: any) {
    const job = this.jobs.get(jobId);
    if (!job) return;

    // Handle both direct agent status updates and stage-based updates
    if (progressData.agentStatus) {
      // Direct agent status update from JSON
      Object.assign(job.progress.agentStatus, progressData.agentStatus);
    } else if (progressData.stage) {
      // Map workflow stages to agent status for backward compatibility
      const stageAgentMap: Record<string, keyof typeof job.progress.agentStatus> = {
        'analysis': 'analysis',
        'analysis_complete': 'analysis',
        'gemini_editing': 'gemini',
        'gemini_complete': 'gemini',
        'imagemagick_optimization': 'imagemagick',
        'background_removal': 'background',
        'quality_control': 'qc'
      };

      const agent = stageAgentMap[progressData.stage];
      if (agent) {
        const status = progressData.stage.includes('complete') ? 'completed' :
                      progressData.stage.includes('failed') || progressData.stage.includes('error') ? 'error' : 'running';
        job.progress.agentStatus[agent] = status;
      }
    }

    // Update other progress fields
    if (progressData.message) {
      job.progress.message = progressData.message;
    }
    if (progressData.stage) {
      job.progress.stage = progressData.stage;
    }
    if (progressData.quality_score !== undefined) {
      job.progress.qualityScore = progressData.quality_score;
    }
    if (progressData.strategy) {
      job.progress.strategy = progressData.strategy;
    }
    if (progressData.output_path) {
      job.outputPath = progressData.output_path;
    }
    if (progressData.success !== undefined && progressData.success) {
      job.status = 'completed';
    }

    // Notify renderer of progress update
    this.mainWindow?.webContents.send('job-progress', {
      jobId,
      progress: job.progress
    });
  }

  private handleProcessError(jobId: string, error: string) {
    const job = this.jobs.get(jobId);
    if (!job) return;

    job.progress.message = `Error: ${error}`;
    
    this.mainWindow?.webContents.send('job-error', {
      jobId,
      error: error
    });
  }

  private cancelJob(jobId: string): boolean {
    const job = this.jobs.get(jobId);
    if (!job || !job.process) {
      return false;
    }

    try {
      job.process.kill('SIGTERM');
      job.status = 'failed';
      job.progress.message = 'Processing cancelled by user';
      return true;
    } catch (error) {
      console.error(`Failed to cancel job ${jobId}:`, error);
      return false;
    }
  }

  private getJobStatus(jobId: string): any | null {
    const job = this.jobs.get(jobId);
    if (!job) return null;
    
    // Return serializable version without ChildProcess
    return this.getSerializableJob(job);
  }

  private generateJobId(): string {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getSerializableJob(job: ProcessingJob): any {
    // Create a clean copy without the non-serializable ChildProcess
    const { process, ...serializableJob } = job;
    return serializableJob;
  }

  private getSerializableJobs(): any[] {
    return Array.from(this.jobs.values()).map(job => this.getSerializableJob(job));
  }

  private loadSettings(): any {
    const settingsPath = path.join(os.homedir(), '.agentic-photo-editor', 'settings.json');
    
    try {
      if (fs.existsSync(settingsPath)) {
        const settingsData = fs.readFileSync(settingsPath, 'utf8');
        return JSON.parse(settingsData);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }

    // Return default settings
    return {
      apiKeys: {
        anthropic: '',
        gemini: '',
        removeBg: ''
      },
      processing: {
        qualityThreshold: 8,
        retryAttempts: 2,
        maxConcurrent: 3
      },
      ui: {
        theme: 'dark',
        showPreview: true,
        autoSave: true
      }
    };
  }

  private saveSettings(settings: any): boolean {
    const settingsDir = path.join(os.homedir(), '.agentic-photo-editor');
    const settingsPath = path.join(settingsDir, 'settings.json');

    try {
      // Ensure directory exists
      if (!fs.existsSync(settingsDir)) {
        fs.mkdirSync(settingsDir, { recursive: true });
      }

      fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
      return true;
    } catch (error) {
      console.error('Failed to save settings:', error);
      return false;
    }
  }

  private saveFileData(fileName: string, fileData: ArrayBuffer): string {
    // Validate file extension
    const extension = path.parse(fileName).ext.toLowerCase();
    const allowedExtensions = ['.jpg', '.jpeg', '.png', '.webp'];
    
    if (!allowedExtensions.includes(extension)) {
      throw new Error(`Unsupported file type: ${extension}. Allowed types: ${allowedExtensions.join(', ')}`);
    }

    // Create a temporary directory for drag-and-drop files
    const tempDir = path.join(os.tmpdir(), 'agentic-photo-editor-temp');
    
    // Ensure temp directory exists
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }

    // Generate unique filename to avoid conflicts
    const timestamp = Date.now();
    const baseName = path.parse(fileName).name;
    const uniqueFileName = `${baseName}_${timestamp}${extension}`;
    const tempFilePath = path.join(tempDir, uniqueFileName);

    try {
      // Write the file data to the temporary location
      const buffer = Buffer.from(fileData);
      fs.writeFileSync(tempFilePath, buffer);
      
      console.log(`Saved drag-and-drop file: ${fileName} -> ${tempFilePath}`);
      return tempFilePath;
    } catch (error) {
      console.error('Failed to save file data:', error);
      throw new Error(`Failed to save file: ${fileName}`);
    }
  }

  private async validateAPIKey(provider: string, key: string): Promise<{ valid: boolean; message?: string }> {
    if (!key || key.trim() === '') {
      return { valid: false, message: 'API key is required' };
    }

    try {
      switch (provider.toLowerCase()) {
        case 'anthropic':
          // Basic format validation for Anthropic keys
          if (!key.startsWith('sk-ant-')) {
            return { valid: false, message: 'Invalid Anthropic API key format' };
          }
          
          // For a full validation, you could make a test API call here
          // For now, we'll just check format and length
          if (key.length < 20) {
            return { valid: false, message: 'Anthropic API key appears too short' };
          }
          
          return { valid: true };

        case 'gemini':
          // Basic validation for Gemini keys - they're typically alphanumeric
          if (key.length < 20 || !/^[a-zA-Z0-9_-]+$/.test(key)) {
            return { valid: false, message: 'Invalid Gemini API key format' };
          }
          
          return { valid: true };

        case 'removebg':
          // Remove.bg keys are typically shorter and alphanumeric
          if (key.length < 10 || !/^[a-zA-Z0-9]+$/.test(key)) {
            return { valid: false, message: 'Invalid Remove.bg API key format' };
          }
          
          return { valid: true };

        default:
          return { valid: false, message: 'Unknown API provider' };
      }
    } catch (error) {
      console.error(`API key validation error for ${provider}:`, error);
      return { valid: false, message: 'Validation failed due to an error' };
    }
  }
}

// Initialize the application
new PhotoEditorMain();