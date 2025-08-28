import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Info,
  Terminal,
  Folder,
  Cpu,
  HardDrive,
  RefreshCw
} from 'lucide-react';

interface SystemStatusProps {
  systemInfo: any;
}

interface StatusItem {
  name: string;
  status: 'success' | 'error' | 'warning' | 'info';
  message: string;
  details?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const SystemStatus: React.FC<SystemStatusProps> = ({ systemInfo }) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentSystemInfo, setCurrentSystemInfo] = useState(systemInfo);

  useEffect(() => {
    setCurrentSystemInfo(systemInfo);
  }, [systemInfo]);

  const refreshSystemInfo = async () => {
    setIsRefreshing(true);
    try {
      const newSystemInfo = await window.electronAPI.getSystemInfo();
      setCurrentSystemInfo(newSystemInfo);
    } catch (error) {
      console.error('Failed to refresh system info:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const getStatusItems = (): StatusItem[] => {
    if (!currentSystemInfo) {
      return [{
        name: 'System Information',
        status: 'error',
        message: 'Unable to load system information',
        details: 'Please restart the application'
      }];
    }

    const items: StatusItem[] = [];

    // Python executable check
    items.push({
      name: 'Python Runtime',
      status: currentSystemInfo.pythonExecutable ? 'success' : 'error',
      message: currentSystemInfo.pythonExecutable 
        ? `Found: ${currentSystemInfo.pythonExecutable}`
        : 'Python not found',
      details: currentSystemInfo.pythonExecutable 
        ? 'Python runtime is available for processing'
        : 'Python is required to run the photo editing pipeline'
    });

    // Photo editor script check
    items.push({
      name: 'Photo Editor Script',
      status: currentSystemInfo.scriptExists ? 'success' : 'error',
      message: currentSystemInfo.scriptExists 
        ? 'Script found and accessible'
        : 'Script not found',
      details: currentSystemInfo.photoEditorScript,
      action: !currentSystemInfo.scriptExists ? {
        label: 'Show Expected Location',
        onClick: () => window.electronAPI.showInFolder(currentSystemInfo.photoEditorScript)
      } : undefined
    });

    // Platform information
    items.push({
      name: 'Platform',
      status: 'info',
      message: `${currentSystemInfo.platform} (${currentSystemInfo.arch})`,
      details: 'Operating system and architecture information'
    });

    // Node.js version
    items.push({
      name: 'Node.js',
      status: 'info',
      message: currentSystemInfo.nodeVersion,
      details: 'JavaScript runtime version'
    });

    // Electron version
    items.push({
      name: 'Electron',
      status: 'info',
      message: currentSystemInfo.electronVersion,
      details: 'Desktop app framework version'
    });

    return items;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case 'info':
        return <Info className="w-5 h-5 text-blue-400" />;
      default:
        return <Info className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'border-green-400 bg-green-400 bg-opacity-5';
      case 'error': return 'border-red-400 bg-red-400 bg-opacity-5';
      case 'warning': return 'border-yellow-400 bg-yellow-400 bg-opacity-5';
      case 'info': return 'border-blue-400 bg-blue-400 bg-opacity-5';
      default: return 'border-gray-600 bg-electron-surface';
    }
  };

  const statusItems = getStatusItems();
  const hasErrors = statusItems.some(item => item.status === 'error');
  const hasWarnings = statusItems.some(item => item.status === 'warning');

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold text-electron-text mb-2">System Status</h2>
            <p className="text-gray-400">
              System information and diagnostic checks
            </p>
          </div>
          
          <button
            onClick={refreshSystemInfo}
            disabled={isRefreshing}
            className="bg-electron-surface border border-electron-border text-electron-text px-4 py-2 rounded-lg hover:bg-electron-border transition-colors flex items-center space-x-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>

        {/* Overall Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-lg p-6 mb-6 border ${
            hasErrors 
              ? 'border-red-400 bg-red-400 bg-opacity-5' 
              : hasWarnings
              ? 'border-yellow-400 bg-yellow-400 bg-opacity-5'
              : 'border-green-400 bg-green-400 bg-opacity-5'
          }`}
        >
          <div className="flex items-center space-x-3 mb-3">
            {hasErrors ? (
              <XCircle className="w-6 h-6 text-red-400" />
            ) : hasWarnings ? (
              <AlertTriangle className="w-6 h-6 text-yellow-400" />
            ) : (
              <CheckCircle className="w-6 h-6 text-green-400" />
            )}
            <h3 className="text-lg font-semibold text-electron-text">
              {hasErrors 
                ? 'System Issues Detected' 
                : hasWarnings
                ? 'System Warnings'
                : 'System Ready'
              }
            </h3>
          </div>
          
          <p className={`${
            hasErrors ? 'text-red-300' : hasWarnings ? 'text-yellow-300' : 'text-green-300'
          }`}>
            {hasErrors 
              ? 'Some components need attention before the photo editor can function properly.'
              : hasWarnings
              ? 'The system is functional but some features may be limited.'
              : 'All system components are working correctly.'
            }
          </p>
        </motion.div>

        {/* Detailed Status Items */}
        <div className="space-y-4">
          {statusItems.map((item, index) => (
            <motion.div
              key={item.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`rounded-lg p-4 border ${getStatusColor(item.status)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  {getStatusIcon(item.status)}
                  
                  <div className="flex-1">
                    <h4 className="font-semibold text-electron-text mb-1">
                      {item.name}
                    </h4>
                    
                    <p className="text-electron-text text-sm mb-2">
                      {item.message}
                    </p>
                    
                    {item.details && (
                      <p className="text-xs text-gray-400">
                        {item.details}
                      </p>
                    )}
                  </div>
                </div>

                {item.action && (
                  <button
                    onClick={item.action.onClick}
                    className="bg-electron-accent text-white px-3 py-1 rounded text-xs hover:bg-blue-600 transition-colors"
                  >
                    {item.action.label}
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* System Information Card */}
        {currentSystemInfo && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-electron-surface rounded-lg p-6 mt-8"
          >
            <div className="flex items-center space-x-2 mb-4">
              <Terminal className="w-5 h-5 text-electron-accent" />
              <h3 className="text-lg font-semibold text-electron-text">System Information</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-electron-text mb-3 flex items-center space-x-2">
                  <Cpu className="w-4 h-4" />
                  <span>Runtime</span>
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Platform:</span>
                    <span className="text-electron-text">{currentSystemInfo.platform}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Architecture:</span>
                    <span className="text-electron-text">{currentSystemInfo.arch}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Node.js:</span>
                    <span className="text-electron-text">{currentSystemInfo.nodeVersion}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Electron:</span>
                    <span className="text-electron-text">{currentSystemInfo.electronVersion}</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-electron-text mb-3 flex items-center space-x-2">
                  <Folder className="w-4 h-4" />
                  <span>Paths</span>
                </h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-400 block">Python:</span>
                    <span className="text-electron-text text-xs font-mono">
                      {currentSystemInfo.pythonExecutable}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400 block">Script:</span>
                    <span className="text-electron-text text-xs font-mono break-all">
                      {currentSystemInfo.photoEditorScript}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Troubleshooting Tips */}
        {hasErrors && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="bg-electron-surface rounded-lg p-6 mt-6"
          >
            <h3 className="text-lg font-semibold text-electron-text mb-4 flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
              <span>Troubleshooting</span>
            </h3>

            <div className="space-y-3 text-sm">
              {!currentSystemInfo?.scriptExists && (
                <div className="p-3 bg-red-400 bg-opacity-10 border border-red-400 rounded">
                  <p className="text-red-300 font-medium mb-2">Photo Editor Script Missing</p>
                  <p className="text-red-200 text-xs">
                    The photo_editor.py script was not found at the expected location. 
                    Make sure you're running the Electron app from the correct directory, 
                    or that the Python script exists at: {currentSystemInfo?.photoEditorScript}
                  </p>
                </div>
              )}

              {!currentSystemInfo?.pythonExecutable && (
                <div className="p-3 bg-red-400 bg-opacity-10 border border-red-400 rounded">
                  <p className="text-red-300 font-medium mb-2">Python Not Found</p>
                  <p className="text-red-200 text-xs">
                    Python is required to run the AI photo editing pipeline. 
                    Please install Python 3.8+ and ensure it's available in your system PATH.
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default SystemStatus;