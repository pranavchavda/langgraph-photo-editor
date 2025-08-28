# Agentic Photo Editor Desktop App

A powerful Electron desktop application for the LangGraph Agentic Photo Editor with Gemini 2.5 Flash integration.

## Features

- **5-Agent Processing Pipeline**: Analysis (Claude) → Background Removal → Gemini Editing → ImageMagick → Quality Control
- **Drag & Drop Interface**: Easy file selection and batch processing
- **Real-time Progress Tracking**: Visual progress for each agent in the pipeline
- **Settings Management**: Secure API key storage and processing preferences
- **Cross-platform**: Windows, macOS, and Linux support
- **Native Integration**: File system access and OS-level features

## Prerequisites

Before running the desktop app, ensure you have:

1. **Python 3.8+** installed and available in PATH
2. **The main photo editor script** (`photo_editor.py`) in the parent directory
3. **API Keys** for Claude (Anthropic) and Gemini
4. **ImageMagick** installed system-wide

## Installation

1. Navigate to the electron directory:
```bash
cd electron
```

2. Install dependencies:
```bash
npm install
```

## Development

1. Start the development server:
```bash
npm run dev
```
This will start both the main process and renderer in watch mode.

2. In another terminal, start Electron:
```bash
npm start
```

The app will hot-reload when you make changes to the code.

## Building for Production

1. Build the application:
```bash
npm run build
```

2. Package for distribution:
```bash
npm run dist
```

This will create platform-specific installers in the `build/` directory.

## Project Structure

```
electron/
├── src/
│   ├── main/              # Electron main process
│   │   ├── main.ts       # Main application logic
│   │   └── preload.ts    # Secure IPC bridge
│   └── renderer/         # React frontend
│       ├── components/   # UI components
│       ├── App.tsx      # Main app component
│       └── index.tsx    # React entry point
├── package.json         # Dependencies and scripts
├── webpack.*.config.js  # Build configuration
└── tailwind.config.js   # UI styling
```

## Key Components

### Main Process (`src/main/main.ts`)
- Window management and app lifecycle
- File system operations (open/save dialogs)
- Python subprocess management
- Settings persistence
- IPC communication with renderer

### Renderer Components
- **FileManager**: Drag-drop file selection and batch operations
- **ProcessingPanel**: Real-time progress visualization for the 5-agent pipeline
- **SettingsPanel**: API key configuration and processing preferences
- **SystemStatus**: System diagnostics and troubleshooting
- **AgentProgressCard**: Individual agent status visualization

### Agent Pipeline Integration
The desktop app interfaces with your existing Python workflow:

1. **File Selection**: Users drag/drop or select images
2. **Processing Launch**: Electron spawns `photo_editor.py` as child process
3. **Progress Streaming**: JSON progress updates via stdout parsing
4. **Real-time UI**: Live updates to agent status cards
5. **Completion Handling**: Results display and file system integration

## Configuration

The app stores settings in `~/.agentic-photo-editor/settings.json`:

```json
{
  "apiKeys": {
    "anthropic": "sk-ant-...",
    "gemini": "your-gemini-key",
    "removeBg": "optional-removebg-key"
  },
  "processing": {
    "qualityThreshold": 8,
    "retryAttempts": 2,
    "maxConcurrent": 3
  },
  "ui": {
    "theme": "dark",
    "showPreview": true,
    "autoSave": true
  }
}
```

## Troubleshooting

### Python Script Not Found
- Ensure `photo_editor.py` exists in the parent directory
- Check the System Status panel for the expected path
- Verify file permissions

### Processing Failures
- Check API key configuration in Settings
- Verify Python dependencies are installed
- Review processing logs in the console

### Build Issues
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Ensure all peer dependencies are satisfied
- Check TypeScript compilation: `npx tsc --noEmit`

## Architecture Notes

### Security
- Context isolation enabled in renderer process
- API keys stored securely in OS user directory
- No node integration in renderer for security

### Performance
- Concurrent batch processing with configurable limits
- Efficient progress streaming without blocking UI
- Lazy loading and component optimization

### Cross-platform Compatibility
- Native file dialogs and system integration
- Platform-specific build configurations
- Responsive UI that adapts to different screen sizes

## Future Enhancements

- Before/after image comparison view
- Batch processing queue management
- Processing history and analytics
- Custom agent parameter tuning
- Plugin system for additional image effects
- Cloud sync for settings and presets