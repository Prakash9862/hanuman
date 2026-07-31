import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'
import './styles.css'
import './wikipedia.css'
import './hanuman-os.css'
import './gmail.css'
import './resources.css'
import './project-memory.css'
import './settings.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
