import React from 'react';
import { motion } from 'framer-motion';
import { 
  FolderOpen, 
  Play, 
  Settings, 
  Info,
  AlertTriangle
} from 'lucide-react';
import { View } from '../App';

interface SidebarProps {
  currentView: View;
  onViewChange: (view: View) => void;
  systemInfo?: any;
}

interface NavItem {
  id: View;
  label: string;
  icon: React.ReactNode;
  description: string;
  badge?: React.ReactNode;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  currentView, 
  onViewChange, 
  systemInfo 
}) => {
  const hasSystemIssues = systemInfo && !systemInfo.scriptExists;

  const navItems: NavItem[] = [
    {
      id: 'files',
      label: 'File Manager',
      icon: <FolderOpen className="w-5 h-5" />,
      description: 'Select and manage images'
    },
    {
      id: 'processing',
      label: 'Processing',
      icon: <Play className="w-5 h-5" />,
      description: 'View active processing jobs'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: <Settings className="w-5 h-5" />,
      description: 'Configure API keys and preferences'
    },
    {
      id: 'system',
      label: 'System Status',
      icon: <Info className="w-5 h-5" />,
      description: 'System information and diagnostics',
      badge: hasSystemIssues ? (
        <AlertTriangle className="w-4 h-4 text-red-400" />
      ) : undefined
    }
  ];

  return (
    <div className="w-64 bg-electron-surface border-r border-electron-border flex flex-col">
      <div className="p-4">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
          Navigation
        </h2>
        
        <nav className="space-y-1">
          {navItems.map((item) => (
            <motion.button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`
                w-full text-left p-3 rounded-lg transition-colors duration-200 group
                ${currentView === item.id 
                  ? 'bg-electron-accent text-white' 
                  : 'text-electron-text hover:bg-electron-border'
                }
              `}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`
                    ${currentView === item.id 
                      ? 'text-white' 
                      : 'text-gray-400 group-hover:text-electron-text'
                    }
                  `}>
                    {item.icon}
                  </div>
                  <div>
                    <div className="font-medium text-sm">
                      {item.label}
                    </div>
                    <div className={`
                      text-xs 
                      ${currentView === item.id 
                        ? 'text-blue-100' 
                        : 'text-gray-500 group-hover:text-gray-400'
                      }
                    `}>
                      {item.description}
                    </div>
                  </div>
                </div>
                {item.badge}
              </div>
            </motion.button>
          ))}
        </nav>
      </div>
      
      {/* Status indicator */}
      <div className="mt-auto p-4 border-t border-electron-border">
        <div className="flex items-center space-x-2 text-xs">
          <div className={`
            w-2 h-2 rounded-full 
            ${hasSystemIssues ? 'bg-red-400' : 'bg-green-400'}
          `}></div>
          <span className="text-gray-400">
            {hasSystemIssues ? 'System needs attention' : 'System ready'}
          </span>
        </div>
        
        {systemInfo && (
          <div className="mt-2 text-xs text-gray-500">
            <div>Python: {systemInfo.pythonExecutable}</div>
            <div>Platform: {systemInfo.platform}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;