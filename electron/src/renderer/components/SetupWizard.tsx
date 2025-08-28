import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, Check, ExternalLink, Key, Sparkles, Coffee, AlertCircle, CheckCircle } from 'lucide-react';
import { useForm } from 'react-hook-form';

interface SetupWizardProps {
  onComplete: () => void;
}

interface APIKeys {
  anthropicKey: string;
  geminiKey: string;
  removeBgKey: string;
}

interface StepProps {
  onNext: () => void;
  onPrev: () => void;
  isFirst: boolean;
  isLast: boolean;
}

const SetupWizard: React.FC<SetupWizardProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [apiKeys, setApiKeys] = useState<APIKeys>({
    anthropicKey: '',
    geminiKey: '',
    removeBgKey: ''
  });
  const [validationState, setValidationState] = useState<{[key: string]: 'idle' | 'validating' | 'valid' | 'invalid'}>({});

  const steps = [
    { title: 'Welcome', component: WelcomeStep },
    { title: 'API Configuration', component: APIStep },
    { title: 'Complete', component: CompleteStep }
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    // Save API keys to electron store
    await window.electronAPI.saveSettings({
      anthropicApiKey: apiKeys.anthropicKey,
      geminiApiKey: apiKeys.geminiKey,
      removeBgApiKey: apiKeys.removeBgKey,
      setupComplete: true
    });
    onComplete();
  };

  const validateAPIKey = async (provider: string, key: string) => {
    if (!key.trim()) return 'invalid';
    
    setValidationState(prev => ({ ...prev, [provider]: 'validating' }));
    
    try {
      const result = await window.electronAPI.validateAPIKey(provider, key);
      const isValid = result.valid;
      setValidationState(prev => ({ ...prev, [provider]: isValid ? 'valid' : 'invalid' }));
      return isValid ? 'valid' : 'invalid';
    } catch (error) {
      setValidationState(prev => ({ ...prev, [provider]: 'invalid' }));
      return 'invalid';
    }
  };

  const CurrentStepComponent = steps[currentStep].component;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl shadow-xl max-w-2xl w-full overflow-hidden"
      >
        {/* Progress Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Coffee className="w-8 h-8" />
              <div>
                <h1 className="text-2xl font-bold">LangGraph Photo Editor</h1>
                <p className="text-blue-100">AI-powered photo enhancement</p>
              </div>
            </div>
            <div className="text-sm">
              Step {currentStep + 1} of {steps.length}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-blue-500/20 rounded-full h-2">
            <motion.div
              className="h-2 bg-white rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Step Content */}
        <div className="p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {currentStep === 0 && (
                <WelcomeStep
                  onNext={handleNext}
                  onPrev={handlePrev}
                  isFirst={true}
                  isLast={false}
                />
              )}
              {currentStep === 1 && (
                <APIStep
                  onNext={handleNext}
                  onPrev={handlePrev}
                  isFirst={false}
                  isLast={false}
                  apiKeys={apiKeys}
                  setApiKeys={setApiKeys}
                  validateAPIKey={validateAPIKey}
                  validationState={validationState}
                />
              )}
              {currentStep === 2 && (
                <CompleteStep
                  onNext={handleNext}
                  onPrev={handlePrev}
                  isFirst={false}
                  isLast={true}
                  onComplete={handleComplete}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
};

// Welcome Step Component
const WelcomeStep: React.FC<StepProps> = ({ onNext, isFirst, isLast }) => {
  return (
    <div className="text-center">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2 }}
        className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-6"
      >
        <Sparkles className="w-10 h-10 text-white" />
      </motion.div>
      
      <h2 className="text-3xl font-bold text-gray-800 mb-4">Welcome to AI Photo Enhancement</h2>
      <div className="space-y-4 text-gray-600 mb-8 max-w-lg mx-auto">
        <p className="text-lg">
          Transform your product photos with our advanced AI pipeline featuring:
        </p>
        
        <div className="grid grid-cols-1 gap-4 text-left">
          <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-white font-bold text-sm">1</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Claude Sonnet 4 Analysis</h3>
              <p className="text-sm text-gray-600">Intelligent image analysis and enhancement strategy</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3 p-4 bg-indigo-50 rounded-lg">
            <div className="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-white font-bold text-sm">2</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Gemini 2.5 Flash Editing</h3>
              <p className="text-sm text-gray-600">Advanced AI image editing with natural language</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3 p-4 bg-purple-50 rounded-lg">
            <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-white font-bold text-sm">3</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Professional Background Removal</h3>
              <p className="text-sm text-gray-600">Clean, professional product photography</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="flex justify-end">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onNext}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2 hover:bg-blue-700 transition-colors"
        >
          Get Started <ChevronRight className="w-5 h-5" />
        </motion.button>
      </div>
    </div>
  );
};

// API Configuration Step Component
interface APIStepProps extends StepProps {
  apiKeys: APIKeys;
  setApiKeys: (keys: APIKeys) => void;
  validateAPIKey: (provider: string, key: string) => Promise<string>;
  validationState: {[key: string]: 'idle' | 'validating' | 'valid' | 'invalid'};
}

const APIStep: React.FC<APIStepProps> = ({ 
  onNext, 
  onPrev, 
  isFirst, 
  isLast, 
  apiKeys, 
  setApiKeys, 
  validateAPIKey, 
  validationState 
}) => {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<APIKeys>({
    defaultValues: apiKeys
  });

  const watchedValues = watch();

  useEffect(() => {
    setApiKeys(watchedValues);
  }, [watchedValues, setApiKeys]);

  const handleKeyBlur = async (provider: string, key: string) => {
    if (key.trim()) {
      await validateAPIKey(provider, key);
    }
  };

  const canProceed = () => {
    return apiKeys.anthropicKey.trim() && 
           apiKeys.geminiKey.trim() &&
           validationState.anthropic === 'valid' &&
           validationState.gemini === 'valid';
  };

  const getValidationIcon = (provider: string) => {
    const state = validationState[provider];
    switch (state) {
      case 'validating':
        return <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />;
      case 'valid':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'invalid':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div>
      <div className="text-center mb-8">
        <Key className="w-12 h-12 text-blue-600 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Configure API Keys</h2>
        <p className="text-gray-600">
          To use our AI-powered photo enhancement, you'll need API keys from our service providers.
        </p>
      </div>

      <form className="space-y-6">
        {/* Claude API Key */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-gray-700">
              Claude API Key <span className="text-red-500">*</span>
            </label>
            <a
              href="https://console.anthropic.com/settings/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              Get API Key <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          <div className="relative">
            <input
              {...register('anthropicKey', { 
                required: 'Claude API key is required',
                pattern: {
                  value: /^sk-ant-/,
                  message: 'Invalid Claude API key format'
                }
              })}
              type="password"
              placeholder="sk-ant-..."
              onBlur={(e) => handleKeyBlur('anthropic', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-12"
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              {getValidationIcon('anthropic')}
            </div>
          </div>
          {errors.anthropicKey && (
            <p className="text-sm text-red-600">{errors.anthropicKey.message}</p>
          )}
          {validationState.anthropic === 'invalid' && (
            <p className="text-sm text-red-600">Invalid API key. Please check and try again.</p>
          )}
        </div>

        {/* Gemini API Key */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-gray-700">
              Gemini API Key <span className="text-red-500">*</span>
            </label>
            <a
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              Get API Key <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          <div className="relative">
            <input
              {...register('geminiKey', { 
                required: 'Gemini API key is required'
              })}
              type="password"
              placeholder="Your Gemini API key..."
              onBlur={(e) => handleKeyBlur('gemini', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-12"
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              {getValidationIcon('gemini')}
            </div>
          </div>
          {errors.geminiKey && (
            <p className="text-sm text-red-600">{errors.geminiKey.message}</p>
          )}
          {validationState.gemini === 'invalid' && (
            <p className="text-sm text-red-600">Invalid API key. Please check and try again.</p>
          )}
        </div>

        {/* Remove.bg API Key (Optional) */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-gray-700">
              Remove.bg API Key <span className="text-gray-400">(Optional)</span>
            </label>
            <a
              href="https://www.remove.bg/api"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              Get API Key <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          <div className="relative">
            <input
              {...register('removeBgKey')}
              type="password"
              placeholder="For professional background removal..."
              onBlur={(e) => e.target.value && handleKeyBlur('removebg', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-12"
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              {getValidationIcon('removebg')}
            </div>
          </div>
          <p className="text-xs text-gray-500">
            Optional: Enables high-quality background removal for product photos
          </p>
        </div>
      </form>

      <div className="flex justify-between mt-8">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onPrev}
          className="flex items-center gap-2 px-6 py-3 text-gray-600 hover:text-gray-700 transition-colors"
        >
          <ChevronLeft className="w-5 h-5" /> Back
        </motion.button>
        
        <motion.button
          whileHover={{ scale: canProceed() ? 1.02 : 1 }}
          whileTap={{ scale: canProceed() ? 0.98 : 1 }}
          onClick={canProceed() ? onNext : undefined}
          disabled={!canProceed()}
          className={`px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-colors ${
            canProceed()
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          Continue <ChevronRight className="w-5 h-5" />
        </motion.button>
      </div>
    </div>
  );
};

// Complete Step Component
interface CompleteStepProps extends StepProps {
  onComplete: () => void;
}

const CompleteStep: React.FC<CompleteStepProps> = ({ onPrev, onComplete }) => {
  return (
    <div className="text-center">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2 }}
        className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6"
      >
        <Check className="w-10 h-10 text-white" />
      </motion.div>
      
      <h2 className="text-3xl font-bold text-gray-800 mb-4">Setup Complete!</h2>
      <div className="space-y-4 text-gray-600 mb-8 max-w-lg mx-auto">
        <p className="text-lg">
          Your LangGraph Photo Editor is now ready to use.
        </p>
        
        <div className="bg-blue-50 p-6 rounded-lg text-left">
          <h3 className="font-semibold text-gray-800 mb-2">What you can do now:</h3>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Drag and drop images to enhance them with AI</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Process multiple images in batches</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Watch real-time progress of the 5-agent pipeline</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Customize processing settings in the settings panel</span>
            </li>
          </ul>
        </div>
      </div>
      
      <div className="flex justify-between">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onPrev}
          className="flex items-center gap-2 px-6 py-3 text-gray-600 hover:text-gray-700 transition-colors"
        >
          <ChevronLeft className="w-5 h-5" /> Back
        </motion.button>
        
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onComplete}
          className="bg-green-600 text-white px-8 py-3 rounded-lg font-medium flex items-center gap-2 hover:bg-green-700 transition-colors"
        >
          Start Using App <Sparkles className="w-5 h-5" />
        </motion.button>
      </div>
    </div>
  );
};

export default SetupWizard;