import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/theme.css'
import './styles/layout.css'
import './styles/pages.css'

import { ThemeProvider } from './context/ThemeContext'
import { ToastProvider } from './context/ToastContext'
import ToastContainer from './components/Toast'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <App />
        <ToastContainer />
      </ToastProvider>
    </ThemeProvider>
  </React.StrictMode>,
)