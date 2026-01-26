import React from 'react';

console.log('TestApp: Module loaded');

function TestApp() {
  console.log('TestApp: Rendering...');
  
  return (
    <div style={{
      backgroundColor: '#1a1a2e',
      color: '#00ff00',
      padding: '40px',
      fontFamily: 'Arial, sans-serif',
      minHeight: '100vh'
    }}>
      <h1>🚀 TRACE Dashboard - Test Page</h1>
      <p>If you can see this, React is working!</p>
      <div style={{
        backgroundColor: '#16213e',
        padding: '20px',
        marginTop: '20px',
        borderRadius: '8px'
      }}>
        <h2>Status:</h2>
        <ul>
          <li>✅ React rendering correctly</li>
          <li>✅ Vite dev server running</li>
          <li>✅ Frontend on port 3000</li>
          <li>⏳ Checking backend connection...</li>
        </ul>
      </div>
    </div>
  );
}

export default TestApp;
