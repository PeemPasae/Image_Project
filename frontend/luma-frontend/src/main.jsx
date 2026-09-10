import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/theme.css'
import './styles/layout.css'
import './styles/pages.css'

import { ToastProvider } from './context/ToastContext'
import ToastContainer from './components/Toast'

import { ThemeProvider } from './context/ThemeContext'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ToastProvider>
      <App />
      <ToastContainer />
    </ToastProvider>
  </React.StrictMode>,

  //   <ThemeProvider>
  //     <App />
  //   </ThemeProvider>
  // </React.StrictMode>,
)