import {
  Activity,
  ArrowRight,
  BarChart3,
  BookOpen,
  Boxes,
  CalendarDays,
  ChevronRight,
  CircleGauge,
  GitBranch,
  GitCompareArrows,
  HeartPulse,
  Library,
  Network,
  Sparkles,
  Swords,
  TerminalSquare,
} from 'lucide-react'
import { BrowserRouter, NavLink, Route, Routes, useNavigate } from 'react-router-dom'

import ChessObsidianPage from './ChessObsidianPage'
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
        <NavLink to="/" end><CircleGauge size={18} /> Vue d’ensemble</NavLink>
        <NavLink to="/orchestrations"><Boxes size={18} /> Orchestrations</NavLink>
        <NavLink to="/library"><Library size={18} /> Bibliothèque</NavLink>
        <NavLink to="/constellation"><Network size={18} /> Constellation</NavLink>
        <NavLink to="/health"><HeartPulse size={18} /> Santé</NavLink>
      </nav>
      <div className="sidebar__footer"><span className="engine-dot" /> Moteur connecté</div>
    </aside>
    <main className="app-content"><Routes>
      <Route path="/" element={<OverviewPage />} />
      <Route path="/orchestrations" element={<OrchestrationsPage />} />
      <Route path="/orchestrations/obsidian-notion" element={<ObsidianNotionPage />} />
      <Route path="/orchestrations/wikipedia-notion" element={<WikipediaNotionPage />} />
      <Route path="/orchestrations/chess-obsidian" element={<ChessObsidianPage />} />
      <Route path="/library" element={<PlaceholderPage title="Bibliothèque" text="La couche transversale des contenus de Hanuman." />} />
      <Route path="/constellation" element={<PlaceholderPage title="Constellation" text="La vue relationnelle de l’écosystème de connaissance." />} />
      <Route path="/health" element={<PlaceholderPage title="Santé du système" text="Diagnostic des connecteurs, services et outils locaux." />} />
    </Routes></main>
  </div>
}

function OverviewPage() {
  const navigate = useNavigate()
  return <div className="page overview-page">
    <header className="overview-hero"><div><p className="eyebrow">Centre de commandement</p><h1>Un seul espace pour faire travailler tes outils ensemble.</h1><p>Hanuman observe les systèmes, orchestre les échanges et garde une vue claire sur ce qui fonctionne, ce qui attend et ce qui mérite ton attention.</p></div><button className="primary-button" onClick={() => navigate('/orchestrations')}>Explorer les orchestrations <ArrowRight size={17} /></button></header>
    <section className="overview-grid">
      <article className="overview-card overview-card--health"><div className="card-heading"><HeartPulse size={18} /><span>Santé du système</span></div><strong>92%</strong><p>API, vault et Notion répondent. Deux services secondaires restent à vérifier.</p><div className="health-lines"><span><i className="health-ok" /> FastAPI</span><span><i className="health-ok" /> Vault Obsidian</span><span><i className="health-ok" /> Notion</span><span><i className="health-warn" /> PostgreSQL</span></div></article>
      <article className="overview-card overview-card--activity"><div className="card-heading"><Activity size={18} /><span>Activité récente</span></div><div className="activity-list"><span><b>Obsidian ↔ Notion</b><small>Inventaire disponible</small></span><span><b>Wikipédia → Notion</b><small>Espace de publication disponible</small></span><span><b>Chess.com → Obsidian</b><small>Import ECO disponible pour prakasch</small></span></div></article>
      <article className="overview-card overview-card--stats"><div className="card-heading"><BarChart3 size={18} /><span>Vue générale</span></div><div className="mini-stats"><span><strong>7</strong><small>orchestrations</small></span><span><strong>4</strong><small>connecteurs actifs</small></span><span><strong>149</strong><small>tests verts</small></span><span><strong>0</strong><small>incidents critiques</small></span></div></article>
      <article className="overview-card overview-card--logs"><div className="card-heading"><TerminalSquare size={18} /><span>Journal système</span></div><div className="log-lines"><code>scan.obsidian completed</code><code>notion.children fetched</code><code>wikipedia.publisher ready</code><code>chess.importer ready</code></div></article>
    </section>
    <section className="overview-section"><div className="section-heading"><div><p className="eyebrow">Espaces actifs</p><h2>Orchestrations</h2></div><button className="text-button" onClick={() => navigate('/orchestrations')}>Tout voir <ChevronRight size={16} /></button></div><div className="featured-orchestrations">{orchestrationCards.slice(0,3).map(({ title,description,path,tone,status,icon:Icon }) => <button key={title} className={`orchestration-card tone-${tone}`} onClick={() => navigate(path)}><span className="orchestration-card__icon"><Icon size={20} /></span><span className="orchestration-card__copy"><b>{title}</b><small>{description}</small></span><span className="orchestration-card__status">{status}</span><ChevronRight size={18} /></button>)}</div></section>
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
