import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

console.log('main.jsx: Starting React app initialization...');

const rootElement = document.getElementById('root');
console.log('main.jsx: Root element found:', rootElement);

if (!rootElement) {
  console.error('main.jsx: Root element not found!');
} else {
  try {
    const root = ReactDOM.createRoot(rootElement);
    console.log('main.jsx: React root created successfully');
    
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
    console.log('main.jsx: App rendered successfully');
  } catch (error) {
    console.error('main.jsx: Error during render:', error);
  }
}
