import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { DialogProvider } from './components/layout/DialogProvider'
import { I18nProvider } from './i18n/I18nProvider'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <I18nProvider><DialogProvider><App /></DialogProvider></I18nProvider>
  </StrictMode>,
)
