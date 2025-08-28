import React, { useState, useEffect } from 'react';
import { Bot, Sparkles } from 'lucide-react';

const TitleBar: React.FC = () => {
  const [platform, setPlatform] = useState<string>('');
  
  useEffect(() => {
    // Get platform info through secure IPC
    window.electronAPI.getPlatform().then(setPlatform).catch(console.error);
  }, []);
  return (
    <div 
      className="h-12 bg-electron-surface border-b border-electron-border flex items-center justify-between px-4 select-none"
      style={{ 
        /* macOS traffic light buttons area */
        paddingLeft: platform === 'darwin' ? '80px' : '16px'
      }}
    >
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-1">
          <Bot className="w-5 h-5 text-electron-accent" />
          <Sparkles className="w-4 h-4 text-agent-gemini" />
        </div>
        <h1 className="text-sm font-semibold text-electron-text">
          Agentic Photo Editor
        </h1>
        <div className="text-xs text-gray-400 bg-electron-border px-2 py-1 rounded">
          LangGraph + Gemini 2.5 Flash
        </div>
      </div>
      
      <div className="flex items-center space-x-4 text-xs text-gray-400">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-agent-analysis rounded-full"></div>
          <span>Claude</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-agent-gemini rounded-full"></div>
          <span>Gemini</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-agent-imagemagick rounded-full"></div>
          <span>ImageMagick</span>
        </div>
      </div>
    </div>
  );
};

export default TitleBar;