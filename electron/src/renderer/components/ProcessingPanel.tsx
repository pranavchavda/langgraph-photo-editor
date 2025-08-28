import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, 
  Pause, 
  Square, 
  RotateCcw, 
  CheckCircle, 
  XCircle,
  Clock,
  Zap,
  Brain,
  Palette,
  Image as ImageIcon,
  Eye
} from 'lucide-react';
import AgentProgressCard from './AgentProgressCard';

interface ProcessingPanelProps {
  settings?: any;
}

interface ProcessingJob {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  inputPath: string;
  outputPath?: string;
  progress: ProcessingProgress;
  startTime?: number;
  endTime?: number;
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

const ProcessingPanel: React.FC<ProcessingPanelProps> = ({ settings }) => {
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [activeJob, setActiveJob] = useState<ProcessingJob | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(Date.now());

  useEffect(() => {
    loadJobs();
    
    // Set up event listeners for real-time updates
    window.electronAPI.onJobProgress(handleJobProgress);
    window.electronAPI.onJobCompleted(handleJobCompleted);
    window.electronAPI.onJobError(handleJobError);

    return () => {
      window.electronAPI.removeAllListeners('job-progress');
      window.electronAPI.removeAllListeners('job-completed');
      window.electronAPI.removeAllListeners('job-error');
    };
  }, []);

  // Auto-refresh active job for real-time updates
  useEffect(() => {
    if (!activeJob || activeJob.status !== 'running') return;

    const interval = setInterval(async () => {
      try {
        const updatedJob = await window.electronAPI.getJobStatus(activeJob.id);
        if (updatedJob) {
          setActiveJob(updatedJob);
          setLastUpdate(Date.now());
          
          // Update the jobs list as well
          setJobs(prev => prev.map(job => 
            job.id === updatedJob.id ? updatedJob : job
          ));
        }
      } catch (error) {
        console.error('Failed to refresh job status:', error);
      }
    }, 1000); // Refresh every second for running jobs

    return () => clearInterval(interval);
  }, [activeJob?.id, activeJob?.status]);

  const loadJobs = async () => {
    try {
      const allJobs = await window.electronAPI.getAllJobs();
      setJobs(allJobs);
      
      // Set the first running job as active
      const runningJob = allJobs.find((job: ProcessingJob) => job.status === 'running');
      if (runningJob) {
        setActiveJob(runningJob);
      } else if (allJobs.length > 0) {
        setActiveJob(allJobs[0]);
      }
    } catch (error) {
      console.error('Failed to load jobs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleJobProgress = (data: { jobId: string; progress: ProcessingProgress }) => {
    setJobs(prev => prev.map(job => 
      job.id === data.jobId 
        ? { ...job, progress: data.progress }
        : job
    ));

    // Update active job if it's the one being updated
    if (activeJob?.id === data.jobId) {
      setActiveJob(prev => prev ? { ...prev, progress: data.progress } : null);
      setLastUpdate(Date.now()); // Trigger re-render for smooth updates
    }
  };

  const handleJobCompleted = (data: { jobId: string; success: boolean; finalStatus: ProcessingProgress; outputPath?: string }) => {
    setJobs(prev => prev.map(job => 
      job.id === data.jobId 
        ? { 
            ...job, 
            status: data.success ? 'completed' : 'failed',
            progress: data.finalStatus,
            outputPath: data.outputPath || job.outputPath,
            endTime: Date.now()
          }
        : job
    ));

    // Update active job
    if (activeJob?.id === data.jobId) {
      setActiveJob(prev => prev ? { 
        ...prev, 
        status: data.success ? 'completed' : 'failed',
        progress: data.finalStatus,
        outputPath: data.outputPath || prev.outputPath,
        endTime: Date.now()
      } : null);
    }
  };

  const handleJobError = (data: { jobId: string; error: string }) => {
    setJobs(prev => prev.map(job => 
      job.id === data.jobId 
        ? { 
            ...job, 
            status: 'failed',
            progress: { ...job.progress, message: `Error: ${data.error}` },
            endTime: Date.now()
          }
        : job
    ));
  };

  const cancelJob = async (jobId: string) => {
    try {
      await window.electronAPI.cancelJob(jobId);
      setJobs(prev => prev.map(job => 
        job.id === jobId 
          ? { ...job, status: 'failed', progress: { ...job.progress, message: 'Cancelled by user' } }
          : job
      ));
    } catch (error) {
      console.error('Failed to cancel job:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-5 h-5 text-yellow-400" />;
      case 'running': return <Play className="w-5 h-5 text-blue-400 animate-pulse" />;
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'failed': return <XCircle className="w-5 h-5 text-red-400" />;
      default: return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const formatDuration = (startTime?: number, endTime?: number) => {
    if (!startTime) return 'Not started';
    const end = endTime || Date.now();
    const duration = Math.round((end - startTime) / 1000);
    
    if (duration < 60) return `${duration}s`;
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}m ${seconds}s`;
  };

  const getFileName = (path: string) => {
    return path.split(/[/\\]/).pop() || path;
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-electron-accent mx-auto mb-4"></div>
          <p className="text-electron-text">Loading processing jobs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex">
      {/* Job list sidebar */}
      <div className="w-80 bg-electron-surface border-r border-electron-border flex flex-col">
        <div className="p-4 border-b border-electron-border">
          <h3 className="font-semibold text-electron-text mb-2">Processing Jobs</h3>
          <p className="text-sm text-gray-400">{jobs.length} total jobs</p>
        </div>

        <div className="flex-1 overflow-auto">
          {jobs.length === 0 ? (
            <div className="p-4 text-center text-gray-400">
              <ImageIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No processing jobs yet</p>
              <p className="text-xs mt-1">Start processing files from the File Manager</p>
            </div>
          ) : (
            <div className="space-y-2 p-2">
              {jobs.map((job) => (
                <motion.div
                  key={job.id}
                  onClick={() => setActiveJob(job)}
                  className={`
                    p-3 rounded-lg cursor-pointer transition-colors border
                    ${activeJob?.id === job.id 
                      ? 'bg-electron-accent border-electron-accent text-white' 
                      : 'bg-electron-bg border-electron-border hover:border-electron-accent'
                    }
                  `}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(job.status)}
                      <span className={`text-sm font-medium ${
                        activeJob?.id === job.id ? 'text-white' : 'text-electron-text'
                      }`}>
                        {getFileName(job.inputPath)}
                      </span>
                    </div>
                    
                    {job.status === 'running' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          cancelJob(job.id);
                        }}
                        className="text-red-400 hover:text-red-300 p-1"
                        title="Cancel job"
                      >
                        <Square className="w-3 h-3" />
                      </button>
                    )}
                  </div>

                  <div className={`text-xs ${
                    activeJob?.id === job.id ? 'text-blue-100' : 'text-gray-400'
                  }`}>
                    <div>{job.progress.message}</div>
                    <div className="mt-1">
                      {formatDuration(job.startTime, job.endTime)}
                      {job.progress.qualityScore && (
                        <span className="ml-2">• Quality: {job.progress.qualityScore}/10</span>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Active job details */}
      <div className="flex-1 p-6 overflow-auto">
        {!activeJob ? (
          <div className="h-full flex items-center justify-center text-center">
            <div>
              <Zap className="w-16 h-16 text-gray-400 mx-auto mb-4 opacity-50" />
              <h3 className="text-xl font-semibold text-electron-text mb-2">
                No Job Selected
              </h3>
              <p className="text-gray-400">
                Select a processing job from the sidebar to view details
              </p>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            {/* Job header */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-electron-text mb-2">
                    {getFileName(activeJob.inputPath)}
                  </h2>
                  <p className="text-gray-400">{activeJob.inputPath}</p>
                </div>
                
                <div className="flex items-center space-x-4">
                  {getStatusIcon(activeJob.status)}
                  <div className="text-right">
                    <div className="text-sm font-medium text-electron-text flex items-center space-x-2">
                      <span>{activeJob.status.charAt(0).toUpperCase() + activeJob.status.slice(1)}</span>
                      {activeJob.status === 'running' && (
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" title="Live updates active" />
                      )}
                    </div>
                    <div className="text-xs text-gray-400">
                      {formatDuration(activeJob.startTime, activeJob.endTime)}
                      {activeJob.status === 'running' && (
                        <span className="ml-2 text-green-400">• Live</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Job stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-electron-surface rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Brain className="w-5 h-5 text-agent-analysis" />
                    <span className="font-medium text-electron-text">Strategy</span>
                  </div>
                  <p className="text-lg text-electron-text capitalize">
                    {activeJob.progress.strategy || 'Determining...'}
                  </p>
                </div>

                <div className="bg-electron-surface rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Eye className="w-5 h-5 text-agent-qc" />
                    <span className="font-medium text-electron-text">Quality Score</span>
                  </div>
                  <p className="text-lg text-electron-text">
                    {activeJob.progress.qualityScore !== undefined 
                      ? `${activeJob.progress.qualityScore}/10`
                      : 'Pending...'
                    }
                  </p>
                </div>

                <div className="bg-electron-surface rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Clock className="w-5 h-5 text-gray-400" />
                    <span className="font-medium text-electron-text">Duration</span>
                  </div>
                  <p className="text-lg text-electron-text">
                    {formatDuration(activeJob.startTime, activeJob.endTime)}
                  </p>
                </div>
              </div>
            </div>

            {/* Agent progress cards */}
            <div className="space-y-4 mb-6">
              <h3 className="text-lg font-semibold text-electron-text mb-4">
                5-Agent Processing Pipeline
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <AgentProgressCard
                  name="Analysis"
                  description="Claude analyzes image and determines strategy"
                  icon={<Brain className="w-6 h-6" />}
                  status={activeJob.progress.agentStatus.analysis}
                  colorClass="agent-analysis"
                />

                <AgentProgressCard
                  name="Background Removal"
                  description="Professional background removal"
                  icon={<ImageIcon className="w-6 h-6" />}
                  status={activeJob.progress.agentStatus.background}
                  colorClass="agent-background"
                />

                <AgentProgressCard
                  name="Gemini 2.5 Flash"
                  description="AI-powered image editing"
                  icon={<Palette className="w-6 h-6" />}
                  status={activeJob.progress.agentStatus.gemini}
                  colorClass="agent-gemini"
                />

                <AgentProgressCard
                  name="ImageMagick"
                  description="Traditional image optimization"
                  icon={<Zap className="w-6 h-6" />}
                  status={activeJob.progress.agentStatus.imagemagick}
                  colorClass="agent-imagemagick"
                />

                <AgentProgressCard
                  name="Quality Control"
                  description="Claude validates final result"
                  icon={<Eye className="w-6 h-6" />}
                  status={activeJob.progress.agentStatus.qc}
                  colorClass="agent-qc"
                />
              </div>
            </div>

            {/* Current status message */}
            <div className="bg-electron-surface rounded-lg p-4">
              <h4 className="font-medium text-electron-text mb-2">Current Status</h4>
              <p className="text-gray-300">{activeJob.progress.message}</p>
              
              {activeJob.status === 'running' && (
                <div className="mt-4">
                  <button
                    onClick={() => cancelJob(activeJob.id)}
                    className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors flex items-center space-x-2"
                  >
                    <Square className="w-4 h-4" />
                    <span>Cancel Processing</span>
                  </button>
                </div>
              )}

              {(activeJob.outputPath || activeJob.status === 'completed') && (
                <div className="mt-4 p-3 bg-green-500 bg-opacity-10 border border-green-500 rounded-lg">
                  <p className="text-green-400 font-medium mb-2">
                    {activeJob.status === 'completed' ? 'Processing Complete!' : 'Processing In Progress...'}
                  </p>
                  {activeJob.outputPath && (
                    <>
                      <p className="text-sm text-gray-300 mb-2">Output: {getFileName(activeJob.outputPath)}</p>
                      <button
                        onClick={() => window.electronAPI.showInFolder(activeJob.outputPath!)}
                        className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 transition-colors"
                      >
                        Show in Folder
                      </button>
                    </>
                  )}
                  {!activeJob.outputPath && activeJob.status === 'completed' && (
                    <p className="text-sm text-yellow-300">Output file location not available</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingPanel;