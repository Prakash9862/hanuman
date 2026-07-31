import {
  Bot,
  HeartPulse,
  NotebookTabs,
  Sparkles,
} from 'lucide-react'
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
import GitHubProjectMemoryPage from './GitHubProjectMemoryPage'
import HanumanOSPage from './HanumanOSPage'
import { navigationItems } from './models/navigation'
import ObsidianNotionPage from './ObsidianNotionPage'
import PlaceholderPage from './PlaceholderPage'
import ResourcesPage from './ResourcesPage'
import SettingsPage from './SettingsPage'
import WikipediaNotionPage from './WikipediaNotionPage'

function SidebarHealthLink() {
  const navigate = useNavigate()

  return (
    <button
      className="sidebar-health"
      onClick={() => navigate('/settings/diagnostic')}
    >
      <span className="sidebar-health__eyebrow">
        <HeartPulse size={14} />
        Diagnostic
      </span>

      <strong>État d’Hanuman</strong>

      <span className="sidebar-health__action">
        Ouvrir le centre de contrôle
      </span>
    </button>
  )
}

function LegacyRedirect({ to }: { to: string }) {
  const { search } = useLocation()

  return <Navigate to={{ pathname: to, search }} replace />
}

function AppShell() {
  const location = useLocation()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/" className="brand">
          <div className="brand__mark">
            <Sparkles size={21} />
          </div>

          <div>
            <strong>Hanuman</strong>
            <span>Système de coordination</span>
          </div>
        </NavLink>

        <nav className="nav">
          {navigationItems.map(({ label, path, end, icon: Icon }) => (
            <NavLink key={path} to={path} end={end}>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        {location.pathname === '/' && <SidebarHealthLink />}

        <div className="sidebar__footer">
          <span className="engine-dot" />
          Moteur connecté
        </div>
      </aside>

      <main className="app-content">
        <Routes>
          <Route path="/" element={<HanumanOSPage />} />
          <Route path="/constellation" element={<Navigate to="/" replace />} />

          <Route path="/flows" element={<FlowsPage />} />
          <Route path="/flows/gmail" element={<GmailPage />} />
          <Route
            path="/flows/github-project-memory"
            element={<GitHubProjectMemoryPage />}
          />
          <Route path="/flows/calendar" element={<CalendarPage />} />
          <Route
            path="/flows/obsidian-notion"
            element={<ObsidianNotionPage />}
          />
          <Route
            path="/flows/wikipedia-notion"
            element={<WikipediaNotionPage />}
          />
          <Route
            path="/flows/chess-obsidian"
            element={<ChessObsidianPage />}
          />

          <Route path="/connectors" element={<ResourcesPage />} />

          <Route
            path="/journal"
            element={
              <PlaceholderPage
                eyebrow="Hanuman / Journal de Vie"
                title="Tes routines personnelles réunies en un seul espace."
                description="Le Journal de Vie accueillera les routines Quotidien, Cuisine, Typing, Sport et les analyses produites par Hanuman."
                note="La première routine, le bilan quotidien, sera construite prochainement."
                icon={NotebookTabs}
              />
            }
          />

          <Route
            path="/agents"
            element={
              <PlaceholderPage
                eyebrow="Hanuman / Agents IA"
                title="Un espace réservé aux futurs agents."
                description="Hanuman ne propose actuellement aucun agent autonome. Cette section documentera leurs capacités lorsqu’elles seront disponibles."
                note="Aucun agent autonome n’est actuellement disponible."
                icon={Bot}
              />
            }
          />

          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/settings/:section" element={<SettingsPage />} />

          <Route
            path="/orchestrations"
            element={<Navigate to="/flows" replace />}
          />
          <Route path="/orchestrations/gmail" element={<GmailPage />} />
          <Route
            path="/orchestrations/calendar"
            element={<CalendarPage />}
          />
          <Route
            path="/orchestrations/obsidian-notion"
            element={<ObsidianNotionPage />}
          />
          <Route
            path="/orchestrations/wikipedia-notion"
            element={<WikipediaNotionPage />}
          />
          <Route
            path="/orchestrations/chess-obsidian"
            element={<ChessObsidianPage />}
          />

          <Route
            path="/resources"
            element={<LegacyRedirect to="/connectors" />}
          />
          <Route
            path="/library"
            element={<LegacyRedirect to="/connectors" />}
          />
          <Route
            path="/health"
            element={<Navigate to="/settings/diagnostic" replace />}
          />
          <Route path="/data" element={<Navigate to="/journal" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}