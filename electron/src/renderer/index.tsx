import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Declare the global electronAPI
declare global {
  interface Window {
    electronAPI: import('../main/preload').ElectronAPI;
  }
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);