import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TitleBar from './components/TitleBar';
import Sidebar from './components/Sidebar';
import FileManager from './components/FileManager';
import ProcessingPanel from './components/ProcessingPanel';
import SettingsPanel from './components/SettingsPanel';
import SystemStatus from './components/SystemStatus';
import SetupWizard from './components/SetupWizard';

export type View = 'files' | 'processing' | 'settings' | 'system';

interface AppSettings {
  apiKeys: {
    anthropic: string;
    gemini: string;
    removeBg: string;
  };
  processing: {
    qualityThreshold: number;
    retryAttempts: number;
    maxConcurrent: number;
  };
  ui: {
    theme: string;
    showPreview: boolean;
    autoSave: boolean;
  };
}

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('files');
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showSetupWizard, setShowSetupWizard] = useState(false);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Load settings and system info
      const [settingsData, systemData] = await Promise.all([
        window.electronAPI.loadSettings(),
        window.electronAPI.getSystemInfo()
      ]);

      setSettings(settingsData);
      setSystemInfo(systemData);

      // Check if setup is complete (API keys configured)
      const isSetupComplete = settingsData.setupComplete || (
        settingsData.apiKeys?.anthropic && 
        settingsData.apiKeys?.gemini
      );

      if (!isSetupComplete) {
        setShowSetupWizard(true);
      } else if (!systemData.scriptExists) {
        // If setup is complete but script missing, show system status
        setCurrentView('system');
      }
    } catch (error) {
      console.error('Failed to initialize app:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveSettings = async (newSettings: AppSettings) => {
    try {
      await window.electronAPI.saveSettings(newSettings);
      setSettings(newSettings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleSetupComplete = async () => {
    // Reload settings to get the updated values
    try {
      const settingsData = await window.electronAPI.loadSettings();
      setSettings(settingsData);
      setShowSetupWizard(false);
      setCurrentView('files');
    } catch (error) {
      console.error('Failed to reload settings after setup:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="h-screen bg-electron-bg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-electron-accent mx-auto mb-4"></div>
          <p className="text-electron-text">Loading Agentic Photo Editor...</p>
        </div>
      </div>
    );
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case 'files':
        return (
          <FileManager 
            settings={settings} 
            onNavigateToProcessing={() => setCurrentView('processing')}
          />
        );
      case 'processing':
        return <ProcessingPanel settings={settings} />;
      case 'settings':
        return (
          <SettingsPanel 
            settings={settings} 
            onSave={handleSaveSettings}
            onResetSetup={() => setShowSetupWizard(true)}
          />
        );
      case 'system':
        return <SystemStatus systemInfo={systemInfo} />;
      default:
        return <FileManager settings={settings} />;
    }
  };

  // Show setup wizard if needed
  if (showSetupWizard) {
    return <SetupWizard onComplete={handleSetupComplete} />;
  }

  return (
    <div className="h-screen bg-electron-bg text-electron-text flex flex-col overflow-hidden">
      <TitleBar />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar 
          currentView={currentView} 
          onViewChange={setCurrentView}
          systemInfo={systemInfo}
        />
        
        <main className="flex-1 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentView}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {renderCurrentView()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

export default App;