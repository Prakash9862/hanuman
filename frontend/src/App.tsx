import {
  ArrowRight,
  BookOpen,
  Boxes,
  CalendarDays,
  GitBranch,
  GitCompareArrows,
  HeartPulse,
  Library,
  Sparkles,
  Swords,
} from 'lucide-react'
import { BrowserRouter, NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom'

import ChessObsidianPage from './ChessObsidianPage'
import HanumanOSPage from './HanumanOSPage'
import ObsidianNotionPage from './ObsidianNotionPage'
import WikipediaNotionPage from './WikipediaNotionPage'

const orchestrationCards = [
  {
    title: 'Obsidian ↔ Notion',
    description: 'Explorer le vault, publier, importer, comparer et suivre les échanges.',
    path: '/orchestrations/obsidian-notion',
    tone: 'violet',
    status: 'Opérationnelle',
    icon: GitCompareArrows,
  },
  {
    title: 'Wikipédia → Notion',
    description: 'Transformer une recherche encyclopédique en page Notion structurée.',
    path: '/orchestrations/wikipedia-notion',
    tone: 'green',
    status: 'Opérationnelle',
    icon: BookOpen,
  },
  {
    title: 'Chess.com → Obsidian',
    description: 'Importer les parties de prakasch et les organiser par note et code ECO.',
    path: '/orchestrations/chess-obsidian',
    tone: 'red',
    status: 'Opérationnelle',
    icon: Swords,
  },
  {
    title: 'GitHub → Notion',
    description: 'Faire remonter projets, issues et activité technique dans Notion.',
    path: '/orchestrations',
    tone: 'graphite',
    status: 'À consolider',
    icon: GitBranch,
  },
]

function AppShell() {
  return <div className="app-shell">
    <aside className="sidebar">
      <NavLink to="/" className="brand"><div className="brand__mark"><Sparkles size={21} /></div><div><strong>Hanuman</strong><span>Orchestration system</span></div></NavLink>
      <nav className="nav">
        <NavLink to="/" end><Sparkles size={18} /> Hanuman</NavLink>
        <NavLink to="/orchestrations"><Boxes size={18} /> Orchestrations</NavLink>
        <NavLink to="/library"><Library size={18} /> Bibliothèque</NavLink>
        <NavLink to="/health"><HeartPulse size={18} /> Santé</NavLink>
      </nav>
      <div className="sidebar__footer"><span className="engine-dot" /> Moteur connecté</div>
    </aside>
    <main className="app-content"><Routes>
      <Route path="/" element={<HanumanOSPage />} />
      <Route path="/constellation" element={<Navigate to="/" replace />} />
      <Route path="/orchestrations" element={<OrchestrationsPage />} />
      <Route path="/orchestrations/obsidian-notion" element={<ObsidianNotionPage />} />
      <Route path="/orchestrations/wikipedia-notion" element={<WikipediaNotionPage />} />
      <Route path="/orchestrations/chess-obsidian" element={<ChessObsidianPage />} />
      <Route path="/library" element={<PlaceholderPage title="Bibliothèque" text="La couche transversale des contenus de Hanuman." />} />
      <Route path="/health" element={<PlaceholderPage title="Santé du système" text="Diagnostic des connecteurs, services et outils locaux." />} />
    </Routes></main>
  </div>
}

function OrchestrationsPage() {
  const navigate = useNavigate()
  return <div className="page"><header className="page-header"><div><p className="eyebrow">Hanuman / Orchestrations</p><h1>Les espaces où les outils coopèrent.</h1><p>Chaque orchestration possède sa propre logique et son ambiance, mais reste intégrée au même système Hanuman.</p></div></header><section className="catalog-grid">{orchestrationCards.map(({ title,description,path,tone,status,icon:Icon }) => <button key={title} className={`catalog-card tone-${tone}`} onClick={() => navigate(path)}><span className="catalog-card__top"><span className="orchestration-card__icon"><Icon size={21} /></span><span className="catalog-status">{status}</span></span><b>{title}</b><p>{description}</p><span className="catalog-card__footer">Entrer dans l’espace <ArrowRight size={16} /></span></button>)}</section></div>
}

function PlaceholderPage({ title, text }: { title: string; text: string }) {
  return <div className="page"><header className="page-header"><div><p className="eyebrow">Hanuman</p><h1>{title}</h1><p>{text}</p></div></header><div className="placeholder-panel"><CalendarDays size={28} /><b>Espace réservé</b><span>La structure existe déjà pour permettre une construction progressive sans refonte.</span></div></div>
}

export default function App() {
  return <BrowserRouter><AppShell /></BrowserRouter>
}
