import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Key, 
  Settings, 
  Eye, 
  EyeOff, 
  Save, 
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  Zap,
  Palette,
  Monitor
} from 'lucide-react';

interface SettingsPanelProps {
  settings: any;
  onSave: (settings: any) => Promise<void>;
  onResetSetup?: () => void;
}

interface ValidationResult {
  field: string;
  isValid: boolean;
  message?: string;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ settings, onSave, onResetSetup }) => {
  const [formData, setFormData] = useState(settings || {});
  const [showApiKeys, setShowApiKeys] = useState({
    anthropic: false,
    gemini: false,
    removeBg: false
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const updateFormData = (section: string, field: string, value: any) => {
    setFormData((prev: any) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const toggleApiKeyVisibility = (apiKey: keyof typeof showApiKeys) => {
    setShowApiKeys(prev => ({
      ...prev,
      [apiKey]: !prev[apiKey]
    }));
  };

  const validateSettings = (): ValidationResult[] => {
    const results: ValidationResult[] = [];

    // Validate API keys
    const anthropicKey = formData.apiKeys?.anthropic || '';
    results.push({
      field: 'anthropic',
      isValid: anthropicKey.startsWith('sk-ant-'),
      message: anthropicKey ? (anthropicKey.startsWith('sk-ant-') ? 'Valid format' : 'Should start with sk-ant-') : 'Required for Claude analysis'
    });

    const geminiKey = formData.apiKeys?.gemini || '';
    results.push({
      field: 'gemini',
      isValid: geminiKey.length > 20,
      message: geminiKey ? (geminiKey.length > 20 ? 'Valid format' : 'Key appears too short') : 'Required for Gemini editing'
    });

    const removeBgKey = formData.apiKeys?.removeBg || '';
    results.push({
      field: 'removeBg',
      isValid: true, // Optional key
      message: removeBgKey ? 'Optional - enhances background removal' : 'Optional service'
    });

    // Validate processing settings
    const qualityThreshold = formData.processing?.qualityThreshold || 0;
    results.push({
      field: 'qualityThreshold',
      isValid: qualityThreshold >= 1 && qualityThreshold <= 10,
      message: qualityThreshold >= 1 && qualityThreshold <= 10 ? 'Valid range' : 'Should be between 1-10'
    });

    return results;
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage(null);

    const validation = validateSettings();
    setValidationResults(validation);

    // Check if required keys are valid
    const requiredKeysValid = validation
      .filter(result => ['anthropic', 'gemini'].includes(result.field))
      .every(result => result.isValid);

    if (!requiredKeysValid) {
      setSaveMessage('Please fix validation errors before saving');
      setIsSaving(false);
      return;
    }

    try {
      await onSave(formData);
      setSaveMessage('Settings saved successfully!');
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      setSaveMessage('Failed to save settings');
      console.error('Save error:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setFormData(settings);
    setSaveMessage('Settings reset to last saved values');
    setTimeout(() => setSaveMessage(null), 3000);
  };

  const getValidationIcon = (field: string) => {
    const result = validationResults.find(r => r.field === field);
    if (!result) return null;

    if (['removeBg'].includes(field)) {
      return <CheckCircle className="w-4 h-4 text-blue-400" />;
    }

    return result.isValid ? (
      <CheckCircle className="w-4 h-4 text-green-400" />
    ) : (
      <AlertTriangle className="w-4 h-4 text-red-400" />
    );
  };

  const getValidationMessage = (field: string) => {
    const result = validationResults.find(r => r.field === field);
    return result?.message || '';
  };

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-electron-text mb-2">Settings</h2>
          <p className="text-gray-400">
            Configure API keys and processing preferences for the agentic photo editor
          </p>
        </div>

        <div className="space-y-8">
          {/* API Keys Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-electron-surface rounded-lg p-6"
          >
            <div className="flex items-center space-x-2 mb-6">
              <Key className="w-5 h-5 text-electron-accent" />
              <h3 className="text-lg font-semibold text-electron-text">API Keys</h3>
            </div>

            <div className="space-y-4">
              {/* Anthropic API Key */}
              <div>
                <label className="block text-sm font-medium text-electron-text mb-2">
                  Anthropic API Key (Claude) *
                </label>
                <div className="relative">
                  <input
                    type={showApiKeys.anthropic ? 'text' : 'password'}
                    value={formData.apiKeys?.anthropic || ''}
                    onChange={(e) => updateFormData('apiKeys', 'anthropic', e.target.value)}
                    placeholder="sk-ant-..."
                    className="w-full bg-electron-bg border border-electron-border rounded-lg px-3 py-2 pr-20 text-electron-text placeholder-gray-500 focus:outline-none focus:border-electron-accent"
                  />
                  <div className="absolute right-2 top-2 flex items-center space-x-1">
                    {getValidationIcon('anthropic')}
                    <button
                      type="button"
                      onClick={() => toggleApiKeyVisibility('anthropic')}
                      className="text-gray-400 hover:text-electron-text p-1"
                    >
                      {showApiKeys.anthropic ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {getValidationMessage('anthropic')}
                </p>
              </div>

              {/* Gemini API Key */}
              <div>
                <label className="block text-sm font-medium text-electron-text mb-2">
                  Google Gemini API Key *
                </label>
                <div className="relative">
                  <input
                    type={showApiKeys.gemini ? 'text' : 'password'}
                    value={formData.apiKeys?.gemini || ''}
                    onChange={(e) => updateFormData('apiKeys', 'gemini', e.target.value)}
                    placeholder="Your Gemini API key..."
                    className="w-full bg-electron-bg border border-electron-border rounded-lg px-3 py-2 pr-20 text-electron-text placeholder-gray-500 focus:outline-none focus:border-electron-accent"
                  />
                  <div className="absolute right-2 top-2 flex items-center space-x-1">
                    {getValidationIcon('gemini')}
                    <button
                      type="button"
                      onClick={() => toggleApiKeyVisibility('gemini')}
                      className="text-gray-400 hover:text-electron-text p-1"
                    >
                      {showApiKeys.gemini ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {getValidationMessage('gemini')}
                </p>
              </div>

              {/* Remove.bg API Key */}
              <div>
                <label className="block text-sm font-medium text-electron-text mb-2">
                  Remove.bg API Key (Optional)
                </label>
                <div className="relative">
                  <input
                    type={showApiKeys.removeBg ? 'text' : 'password'}
                    value={formData.apiKeys?.removeBg || ''}
                    onChange={(e) => updateFormData('apiKeys', 'removeBg', e.target.value)}
                    placeholder="Your remove.bg API key..."
                    className="w-full bg-electron-bg border border-electron-border rounded-lg px-3 py-2 pr-20 text-electron-text placeholder-gray-500 focus:outline-none focus:border-electron-accent"
                  />
                  <div className="absolute right-2 top-2 flex items-center space-x-1">
                    {getValidationIcon('removeBg')}
                    <button
                      type="button"
                      onClick={() => toggleApiKeyVisibility('removeBg')}
                      className="text-gray-400 hover:text-electron-text p-1"
                    >
                      {showApiKeys.removeBg ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {getValidationMessage('removeBg')}
                </p>
              </div>
            </div>
          </motion.div>

          {/* Processing Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-electron-surface rounded-lg p-6"
          >
            <div className="flex items-center space-x-2 mb-6">
              <Zap className="w-5 h-5 text-agent-imagemagick" />
              <h3 className="text-lg font-semibold text-electron-text">Processing Settings</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-electron-text mb-2">
                  Quality Threshold
                </label>
                <div className="relative">
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={formData.processing?.qualityThreshold || 8}
                    onChange={(e) => updateFormData('processing', 'qualityThreshold', parseInt(e.target.value))}
                    className="w-full bg-electron-bg border border-electron-border rounded-lg px-3 py-2 text-electron-text focus:outline-none focus:border-electron-accent"
                  />
                  <div className="absolute right-2 top-2">
                    {getValidationIcon('qualityThreshold')}
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  Minimum quality score (1-10)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-electron-text mb-2">
                  Retry Attempts
                </label>
                <input
                  type="number"
                  min="0"
                  max="5"
                  value={formData.processing?.retryAttempts || 2}
                  onChange={(e) => updateFormData('processing', 'retryAttempts', parseInt(e.target.value))}
                  className="w-full bg-electron-bg border border-electron-border rounded-lg px-3 py-2 text-electron-text focus:outline-none focus:border-electron-accent"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Max retry attempts on failure
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-electron-text mb-2">
                  Max Concurrent
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.processing?.maxConcurrent || 3}
                  onChange={(e) => updateFormData('processing', 'maxConcurrent', parseInt(e.target.value))}
                  className="w-full bg-electron-bg border border-electron-border rounded-lg px-3 py-2 text-electron-text focus:outline-none focus:border-electron-accent"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Concurrent batch processing
                </p>
              </div>
            </div>
          </motion.div>

          {/* UI Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-electron-surface rounded-lg p-6"
          >
            <div className="flex items-center space-x-2 mb-6">
              <Monitor className="w-5 h-5 text-agent-background" />
              <h3 className="text-lg font-semibold text-electron-text">Interface Settings</h3>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-electron-text">Show Preview Images</p>
                  <p className="text-sm text-gray-400">Display before/after image previews</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.ui?.showPreview ?? true}
                    onChange={(e) => updateFormData('ui', 'showPreview', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-electron-accent"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-electron-text">Auto-save Settings</p>
                  <p className="text-sm text-gray-400">Automatically save settings changes</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.ui?.autoSave ?? true}
                    onChange={(e) => updateFormData('ui', 'autoSave', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-electron-accent"></div>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-electron-text mb-2">
                  Theme
                </label>
                <select
                  value={formData.ui?.theme || 'dark'}
                  onChange={(e) => updateFormData('ui', 'theme', e.target.value)}
                  className="w-full bg-electron-bg border border-electron-border rounded-lg px-3 py-2 text-electron-text focus:outline-none focus:border-electron-accent"
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light (Coming Soon)</option>
                  <option value="auto">Auto (Coming Soon)</option>
                </select>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Action buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-8 flex justify-between items-center bg-electron-surface rounded-lg p-4"
        >
          <div className="flex items-center space-x-4">
            <button
              onClick={handleReset}
              className="flex items-center space-x-2 text-gray-400 hover:text-electron-text transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset Changes</span>
            </button>
          </div>

          <div className="flex items-center space-x-4">
            {saveMessage && (
              <motion.p
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className={`text-sm ${
                  saveMessage.includes('success') 
                    ? 'text-green-400' 
                    : saveMessage.includes('error') || saveMessage.includes('fix')
                    ? 'text-red-400'
                    : 'text-yellow-400'
                }`}
              >
                {saveMessage}
              </motion.p>
            )}

            <button
              onClick={handleSave}
              disabled={isSaving}
              className="bg-electron-accent text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
            >
              <Save className="w-4 h-4" />
              <span>{isSaving ? 'Saving...' : 'Save Settings'}</span>
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default SettingsPanel;