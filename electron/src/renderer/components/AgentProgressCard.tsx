import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';

interface AgentProgressCardProps {
  name: string;
  description: string;
  icon: React.ReactNode;
  status: 'pending' | 'running' | 'completed' | 'error';
  colorClass: string;
  details?: string;
}

const AgentProgressCard: React.FC<AgentProgressCardProps> = ({
  name,
  description,
  icon,
  status,
  colorClass,
  details
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'pending':
        return <Clock className="w-5 h-5 text-gray-400" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'pending': return 'Waiting...';
      case 'running': return 'Processing...';
      case 'completed': return 'Completed';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'pending': return 'text-gray-400';
      case 'running': return 'text-blue-400';
      case 'completed': return 'text-green-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getBorderClass = () => {
    switch (status) {
      case 'pending': return 'border-gray-600';
      case 'running': return `border-blue-400 ${colorClass}`;
      case 'completed': return 'border-green-400';
      case 'error': return 'border-red-400';
      default: return 'border-gray-600';
    }
  };

  const getBackgroundClass = () => {
    switch (status) {
      case 'running': return 'bg-blue-400 bg-opacity-5';
      case 'completed': return 'bg-green-400 bg-opacity-5';
      case 'error': return 'bg-red-400 bg-opacity-5';
      default: return 'bg-electron-surface';
    }
  };

  return (
    <motion.div
      className={`
        rounded-lg p-4 border transition-all duration-300
        ${getBorderClass()}
        ${getBackgroundClass()}
      `}
      animate={{
        scale: status === 'running' ? [1, 1.02, 1] : 1,
      }}
      transition={{
        duration: 2,
        repeat: status === 'running' ? Infinity : 0,
        ease: "easeInOut"
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={`${colorClass} ${status === 'running' ? 'animate-pulse' : ''}`}>
          {icon}
        </div>
        {getStatusIcon()}
      </div>

      <h4 className="font-semibold text-electron-text text-sm mb-1">
        {name}
      </h4>

      <p className="text-xs text-gray-400 mb-3">
        {description}
      </p>

      <div className="flex items-center justify-between">
        <span className={`text-xs font-medium ${getStatusColor()}`}>
          {getStatusText()}
        </span>
        
        {status === 'running' && (
          <motion.div
            className="w-12 h-1 bg-gray-600 rounded-full overflow-hidden"
          >
            <motion.div
              className={`h-full bg-blue-400 rounded-full`}
              animate={{
                x: ['-100%', '100%']
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            />
          </motion.div>
        )}
      </div>

      {details && (
        <p className="text-xs text-gray-300 mt-2 pt-2 border-t border-electron-border">
          {details}
        </p>
      )}
    </motion.div>
  );
};

export default AgentProgressCard;