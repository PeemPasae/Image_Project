import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/theme.css'
import './styles/layout.css'
import './styles/pages.css'
import './styles/template-soft.css'

import { ThemeProvider } from './context/ThemeContext'
import { LayoutProvider } from './context/LayoutContext'
import { ToastProvider } from './context/ToastContext'
import ToastContainer from './components/Toast'
import ErrorBoundary from './components/ErrorBoundary'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
    <ThemeProvider>
      <LayoutProvider>
        <ToastProvider>
          <App />
          <ToastContainer />
        </ToastProvider>
      </LayoutProvider>
    </ThemeProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)