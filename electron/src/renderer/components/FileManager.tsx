import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  FolderOpen, 
  FileImage, 
  Play, 
  Trash2, 
  Download,
  Eye,
  Grid,
  List,
  Filter
} from 'lucide-react';

interface FileManagerProps {
  settings?: any;
  onNavigateToProcessing?: () => void;
}

interface ImageFile {
  id: string;
  path: string;
  name: string;
  size: number;
  lastModified: number;
  type: string;
  fileData?: File; // For drag-and-drop files that need to be saved first
}

type ViewMode = 'grid' | 'list';
type FilterType = 'all' | 'jpg' | 'png' | 'webp';

const FileManager: React.FC<FileManagerProps> = ({ settings, onNavigateToProcessing }) => {
  const [selectedFiles, setSelectedFiles] = useState<ImageFile[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [filter, setFilter] = useState<FilterType>('all');
  const [customInstructions, setCustomInstructions] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  // File drop zone
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: ImageFile[] = acceptedFiles.map(file => ({
      id: `${file.name}-${Date.now()}`,
      // For drag-and-drop files, path might be empty, so we store the File object
      path: file.path || '', 
      name: file.name,
      size: file.size,
      lastModified: file.lastModified,
      type: file.type,
      fileData: !file.path ? file : undefined // Store File object if no path (drag-and-drop)
    }));

    setSelectedFiles(prev => [...prev, ...newFiles]);
  }, []);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject
  } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp']
    },
    multiple: true
  });

  // Handle file selection via dialog
  const handleSelectFiles = async () => {
    try {
      const filePaths = await window.electronAPI.selectFiles();
      
      if (filePaths.length > 0) {
        // Convert file paths to ImageFile objects
        const newFiles: ImageFile[] = filePaths.map(filePath => {
          const fileName = filePath.split(/[/\\]/).pop() || '';
          const fileExt = fileName.split('.').pop()?.toLowerCase() || '';
          
          return {
            id: `${fileName}-${Date.now()}`,
            path: filePath,
            name: fileName,
            size: 0, // We don't have file size from path
            lastModified: Date.now(),
            type: `image/${fileExt === 'jpg' ? 'jpeg' : fileExt}`
          };
        });

        setSelectedFiles(prev => [...prev, ...newFiles]);
      }
    } catch (error) {
      console.error('Failed to select files:', error);
    }
  };

  // Handle directory selection
  const handleSelectDirectory = async () => {
    try {
      const directoryPath = await window.electronAPI.selectDirectory();
      
      if (directoryPath) {
        // Start batch processing for directory
        startProcessing(directoryPath, 'batch');
      }
    } catch (error) {
      console.error('Failed to select directory:', error);
    }
  };

  // Remove file from selection
  const removeFile = (fileId: string) => {
    setSelectedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  // Clear all files
  const clearAllFiles = () => {
    setSelectedFiles([]);
  };

  // Start processing
  const startProcessing = async (inputPath?: string, mode: 'single' | 'batch' = 'single') => {
    if (!inputPath && selectedFiles.length === 0) {
      return;
    }

    setIsProcessing(true);

    try {
      // If processing selected files, we'll process them one by one
      if (!inputPath && selectedFiles.length > 0) {
        for (const file of selectedFiles) {
          let filePathToProcess = file.path;
          
          // Handle drag-and-drop files that don't have a path
          if (!filePathToProcess && file.fileData) {
            try {
              // Save the file data to a temporary location first
              filePathToProcess = await window.electronAPI.saveFileData({
                fileName: file.name,
                fileData: await file.fileData.arrayBuffer()
              });
            } catch (error) {
              console.error(`Failed to save drag-and-drop file ${file.name}:`, error);
              continue; // Skip this file
            }
          }
          
          // Skip files that still don't have a valid path
          if (!filePathToProcess) {
            console.error(`Skipping file ${file.name}: no valid path available`);
            continue;
          }
          
          const jobId = await window.electronAPI.startProcessing({
            inputPath: filePathToProcess,
            instructions: customInstructions || undefined,
            mode: 'single'
          });
          
          console.log(`Started processing job: ${jobId} for file: ${file.name}`);
        }
      } else if (inputPath) {
        // Process directory or single file
        const jobId = await window.electronAPI.startProcessing({
          inputPath,
          instructions: customInstructions || undefined,
          mode
        });
        
        console.log(`Started ${mode} processing job: ${jobId}`);
      }

      // Navigate to processing view to see progress
      if (onNavigateToProcessing) {
        setTimeout(() => onNavigateToProcessing(), 500);
      }
      
    } catch (error) {
      console.error('Failed to start processing:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Filter files
  const filteredFiles = selectedFiles.filter(file => {
    if (filter === 'all') return true;
    
    const extension = file.name.split('.').pop()?.toLowerCase();
    switch (filter) {
      case 'jpg': return extension === 'jpg' || extension === 'jpeg';
      case 'png': return extension === 'png';
      case 'webp': return extension === 'webp';
      default: return true;
    }
  });

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return 'Unknown size';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const dropzoneClasses = `
    border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200
    ${isDragActive 
      ? (isDragAccept ? 'dropzone-active' : 'dropzone-reject')
      : 'border-electron-border hover:border-electron-accent'
    }
  `;

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-electron-text mb-2">File Manager</h2>
          <p className="text-gray-400">
            Select images to process with the AI-powered editing pipeline
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* View mode toggle */}
          <div className="flex bg-electron-surface rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${
                viewMode === 'grid' 
                  ? 'bg-electron-accent text-white' 
                  : 'text-gray-400 hover:text-electron-text'
              }`}
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${
                viewMode === 'list' 
                  ? 'bg-electron-accent text-white' 
                  : 'text-gray-400 hover:text-electron-text'
              }`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as FilterType)}
            className="bg-electron-surface border border-electron-border rounded px-3 py-2 text-electron-text"
          >
            <option value="all">All Images</option>
            <option value="jpg">JPG/JPEG</option>
            <option value="png">PNG</option>
            <option value="webp">WebP</option>
          </select>
        </div>
      </div>

      {/* File Drop Zone */}
      {selectedFiles.length === 0 && (
        <div {...getRootProps()} className={dropzoneClasses}>
          <input {...getInputProps()} />
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          
          {isDragActive ? (
            <div>
              {isDragAccept ? (
                <p className="text-electron-accent text-lg font-medium">
                  Drop images here to add them
                </p>
              ) : (
                <p className="text-red-400 text-lg font-medium">
                  Only image files are supported
                </p>
              )}
            </div>
          ) : (
            <div>
              <p className="text-lg font-medium text-electron-text mb-2">
                Drag & drop images here
              </p>
              <p className="text-gray-400 mb-4">
                or click to select files
              </p>
              
              <div className="flex justify-center space-x-4">
                <button
                  onClick={handleSelectFiles}
                  className="bg-electron-accent text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center space-x-2"
                >
                  <FileImage className="w-4 h-4" />
                  <span>Select Files</span>
                </button>
                
                <button
                  onClick={handleSelectDirectory}
                  className="bg-electron-surface border border-electron-border text-electron-text px-4 py-2 rounded-lg hover:bg-electron-border transition-colors flex items-center space-x-2"
                >
                  <FolderOpen className="w-4 h-4" />
                  <span>Select Folder</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="flex-1 flex flex-col">
          {/* File actions */}
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center space-x-4">
              <span className="text-electron-text">
                {filteredFiles.length} of {selectedFiles.length} files
              </span>
              
              <button
                onClick={clearAllFiles}
                className="text-red-400 hover:text-red-300 flex items-center space-x-1"
              >
                <Trash2 className="w-4 h-4" />
                <span>Clear All</span>
              </button>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSelectFiles}
                className="bg-electron-surface border border-electron-border text-electron-text px-3 py-2 rounded hover:bg-electron-border transition-colors"
              >
                Add More Files
              </button>
              
              <button
                onClick={() => startProcessing()}
                disabled={isProcessing || filteredFiles.length === 0}
                className="bg-agent-gemini text-white px-4 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <Play className="w-4 h-4" />
                <span>{isProcessing ? 'Starting...' : 'Process Files'}</span>
              </button>
            </div>
          </div>

          {/* Custom instructions */}
          <div className="mb-4">
            <textarea
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              placeholder="Enter custom processing instructions (optional)..."
              className="w-full bg-electron-surface border border-electron-border rounded-lg p-3 text-electron-text placeholder-gray-500 resize-none"
              rows={2}
            />
          </div>

          {/* Files grid/list */}
          <div className="flex-1 overflow-auto">
            {viewMode === 'grid' ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                <AnimatePresence>
                  {filteredFiles.map((file) => (
                    <motion.div
                      key={file.id}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className="bg-electron-surface border border-electron-border rounded-lg p-4 hover:border-electron-accent transition-colors group"
                    >
                      <div className="aspect-square bg-electron-border rounded mb-3 flex items-center justify-center">
                        <FileImage className="w-8 h-8 text-gray-400" />
                      </div>
                      
                      <h4 className="font-medium text-electron-text text-sm mb-1 truncate" title={file.name}>
                        {file.name}
                      </h4>
                      
                      <p className="text-xs text-gray-400 mb-2">
                        {formatFileSize(file.size)}
                      </p>
                      
                      <button
                        onClick={() => removeFile(file.id)}
                        className="w-full bg-red-500 bg-opacity-20 text-red-400 text-xs py-1 rounded hover:bg-opacity-30 transition-colors opacity-0 group-hover:opacity-100"
                      >
                        Remove
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            ) : (
              <div className="space-y-2">
                <AnimatePresence>
                  {filteredFiles.map((file) => (
                    <motion.div
                      key={file.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="bg-electron-surface border border-electron-border rounded-lg p-4 flex items-center justify-between hover:border-electron-accent transition-colors group"
                    >
                      <div className="flex items-center space-x-3">
                        <FileImage className="w-8 h-8 text-gray-400" />
                        <div>
                          <h4 className="font-medium text-electron-text text-sm">
                            {file.name}
                          </h4>
                          <p className="text-xs text-gray-400">
                            {formatFileSize(file.size)}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => window.electronAPI.showInFolder(file.path)}
                          className="text-gray-400 hover:text-electron-text p-2"
                          title="Show in folder"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        
                        <button
                          onClick={() => removeFile(file.id)}
                          className="text-red-400 hover:text-red-300 p-2"
                          title="Remove file"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileManager;