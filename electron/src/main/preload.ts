import { contextBridge, ipcRenderer } from 'electron';

// Define the API interface
export interface ElectronAPI {
  // File operations
  selectFiles: () => Promise<string[]>;
  selectDirectory: () => Promise<string | null>;
  saveDirectory: () => Promise<string | null>;
  showInFolder: (filePath: string) => Promise<void>;
  saveFileData: (options: { fileName: string; fileData: ArrayBuffer }) => Promise<string>;

  // Processing operations
  startProcessing: (options: {
    inputPath: string;
    outputDir?: string;
    instructions?: string;
    mode: 'single' | 'batch';
  }) => Promise<string>;
  cancelJob: (jobId: string) => Promise<boolean>;
  getJobStatus: (jobId: string) => Promise<any>;
  getAllJobs: () => Promise<any[]>;

  // Settings operations
  loadSettings: () => Promise<any>;
  saveSettings: (settings: any) => Promise<boolean>;
  validateAPIKey: (provider: string, key: string) => Promise<{ valid: boolean; message?: string }>;

  // System info
  getSystemInfo: () => Promise<{
    platform: string;
    arch: string;
    nodeVersion: string;
    electronVersion: string;
    pythonExecutable: string;
    photoEditorScript: string;
    scriptExists: boolean;
  }>;
  
  // Platform info for UI styling (immediate access)
  getPlatform: () => Promise<string>;

  // Event listeners
  onJobProgress: (callback: (data: { jobId: string; progress: any }) => void) => void;
  onJobCompleted: (callback: (data: { jobId: string; success: boolean; finalStatus: any }) => void) => void;
  onJobError: (callback: (data: { jobId: string; error: string }) => void) => void;

  // Remove event listeners
  removeAllListeners: (channel: string) => void;
}

// Expose the API to the renderer process
const electronAPI: ElectronAPI = {
  // File operations
  selectFiles: () => ipcRenderer.invoke('select-files'),
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  saveDirectory: () => ipcRenderer.invoke('save-directory'),
  showInFolder: (filePath: string) => ipcRenderer.invoke('show-in-folder', filePath),
  saveFileData: (options) => ipcRenderer.invoke('save-file-data', options),

  // Processing operations
  startProcessing: (options) => ipcRenderer.invoke('start-processing', options),
  cancelJob: (jobId: string) => ipcRenderer.invoke('cancel-job', jobId),
  getJobStatus: (jobId: string) => ipcRenderer.invoke('get-job-status', jobId),
  getAllJobs: () => ipcRenderer.invoke('get-all-jobs'),

  // Settings operations
  loadSettings: () => ipcRenderer.invoke('load-settings'),
  saveSettings: (settings: any) => ipcRenderer.invoke('save-settings', settings),
  validateAPIKey: (provider: string, key: string) => ipcRenderer.invoke('validate-api-key', provider, key),

  // System info
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  getPlatform: () => ipcRenderer.invoke('get-platform'),

  // Event listeners
  onJobProgress: (callback) => {
    ipcRenderer.on('job-progress', (event, data) => callback(data));
  },
  onJobCompleted: (callback) => {
    ipcRenderer.on('job-completed', (event, data) => callback(data));
  },
  onJobError: (callback) => {
    ipcRenderer.on('job-error', (event, data) => callback(data));
  },

  // Remove event listeners
  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel);
  }
};

// Expose the API to the renderer
contextBridge.exposeInMainWorld('electronAPI', electronAPI);