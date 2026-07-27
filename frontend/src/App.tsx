import {
  ChevronRight,
  HeartPulse,
  Sparkles,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import {
  BrowserRouter,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from 'react-router-dom'

import CalendarPage from './CalendarPage'
import ChessObsidianPage from './ChessObsidianPage'
import FlowsPage from './FlowsPage'
import GmailPage from './GmailPage'
import HanumanOSPage from './HanumanOSPage'
import HealthPage from './HealthPage'
import { navigationItems } from './models/navigation'
import ObsidianNotionPage from './ObsidianNotionPage'
import ResourcesPage from './ResourcesPage'
import WikipediaNotionPage from './WikipediaNotionPage'

const healthEndpoints = [
  '/status',
  '/calendar/status',
  '/gmail/status',
  '/github/ping',
  '/notion/ping',
  '/obsidian/ping',
  '/openai/ping',
  '/wikipedia/ping',
  '/chess/ping',
]

function SidebarHealth() {
  const navigate = useNavigate()
  const [healthy, setHealthy] = useState(0)
  const [checkedAt, setCheckedAt] = useState<string | null>(null)

  useEffect(() => {
    void Promise.all(
      healthEndpoints.map(async (endpoint) => {
        try {
          const response = await fetch(`http://127.0.0.1:8000${endpoint}`)
          const payload = (await response.json().catch(() => ({}))) as { ok?: boolean }
          return response.ok && payload.ok !== false
        } catch {
          return false
        }
      }),
    ).then((results) => {
      setHealthy(results.filter(Boolean).length)
      setCheckedAt(new Date().toISOString())
    })
  }, [])

  const alerts = healthEndpoints.length - healthy

  return (
    <button className="sidebar-health" onClick={() => navigate('/health')}>
      <span className="sidebar-health__eyebrow">
        <HeartPulse size={14} /> Santé du système
      </span>
      <strong>{alerts ? 'À surveiller' : 'Opérationnel'}</strong>
      <span className="sidebar-health__meter">
        <i style={{ width: `${Math.round((healthy / healthEndpoints.length) * 100)}%` }} />
      </span>
      <span className="sidebar-health__meta">
        <b>{healthy}/{healthEndpoints.length}</b> services actifs
        <small>{checkedAt ? `Contrôle ${new Date(checkedAt).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}` : 'Contrôle en cours'}</small>
      </span>
      <span className="sidebar-health__action">Voir le diagnostic <ChevronRight size={14} /></span>
    </button>
  )
}

function AppShell() {
  const location = useLocation()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/" className="brand">
          <div className="brand__mark"><Sparkles size={21} /></div>
          <div><strong>Hanuman</strong><span>Système de coordination</span></div>
        </NavLink>
        <nav className="nav">
          {navigationItems.map(({ label, path, end, icon: Icon }) => (
            <NavLink key={path} to={path} end={end}><Icon size={18} /> {label}</NavLink>
          ))}
        </nav>
        {location.pathname === '/' && <SidebarHealth />}
        <div className="sidebar__footer"><span className="engine-dot" /> Moteur connecté</div>
      </aside>
      <main className="app-content">
        <Routes>
          <Route path="/" element={<HanumanOSPage />} />
          <Route path="/constellation" element={<Navigate to="/" replace />} />
          <Route path="/flows" element={<FlowsPage />} />
          <Route path="/flows/gmail" element={<GmailPage />} />
          <Route path="/flows/calendar" element={<CalendarPage />} />
          <Route path="/flows/obsidian-notion" element={<ObsidianNotionPage />} />
          <Route path="/flows/wikipedia-notion" element={<WikipediaNotionPage />} />
          <Route path="/flows/chess-obsidian" element={<ChessObsidianPage />} />
          <Route path="/connectors" element={<ResourcesPage />} />
          <Route path="/health" element={<HealthPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return <BrowserRouter><AppShell /></BrowserRouter>
}
