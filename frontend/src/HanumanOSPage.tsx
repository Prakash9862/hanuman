import {
  BookOpen,
  BrainCircuit,
  CalendarDays,
  ChevronRight,
  Github,
  Mail,
  Minus,
  Network,
  NotebookPen,
  Plus,
  RotateCcw,
  Swords,
  X,
} from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

type NodeStatus = 'active' | 'partial' | 'planned' | 'core'
type NodeId = 'hanuman' | 'obsidian' | 'notion' | 'github' | 'calendar' | 'wikipedia' | 'chess' | 'gmail' | 'openai'

type Node = {
  id: NodeId
  label: string
  subtitle: string
  x: number
  y: number
  status: NodeStatus
  icon: typeof Network
  route?: string
}

type Viewport = { x: number; y: number; scale: number }

const nodes: Node[] = [
  { id: 'hanuman', label: 'Hanuman', subtitle: 'Centre de gravité', x: 50, y: 50, status: 'core', icon: BrainCircuit },
  { id: 'obsidian', label: 'Obsidian', subtitle: 'Mémoire locale', x: 21, y: 35, status: 'active', icon: NotebookPen, route: '/orchestrations/obsidian-notion' },
  { id: 'notion', label: 'Notion', subtitle: 'Organisation', x: 79, y: 35, status: 'active', icon: Network, route: '/orchestrations/obsidian-notion' },
  { id: 'github', label: 'GitHub', subtitle: 'Développement', x: 50, y: 14, status: 'partial', icon: Github, route: '/orchestrations' },
  { id: 'calendar', label: 'Calendar', subtitle: 'Planification', x: 84, y: 68, status: 'partial', icon: CalendarDays },
  { id: 'wikipedia', label: 'Wikipédia', subtitle: 'Documentation', x: 66, y: 86, status: 'active', icon: BookOpen, route: '/orchestrations/wikipedia-notion' },
  { id: 'chess', label: 'Chess.com', subtitle: 'Parties et analyses', x: 34, y: 86, status: 'active', icon: Swords, route: '/orchestrations/chess-obsidian' },
  { id: 'openai', label: 'OpenAI', subtitle: 'Raisonnement', x: 16, y: 68, status: 'partial', icon: BrainCircuit },
  { id: 'gmail', label: 'Gmail', subtitle: 'Lecture seule', x: 8, y: 18, status: 'partial', icon: Mail, route: '/orchestrations/gmail' },
]

const links: Array<[NodeId, NodeId, Exclude<NodeStatus, 'core'>]> = [
  ['hanuman', 'obsidian', 'active'],
  ['hanuman', 'notion', 'active'],
  ['hanuman', 'github', 'partial'],
  ['hanuman', 'calendar', 'partial'],
  ['hanuman', 'wikipedia', 'active'],
  ['hanuman', 'chess', 'active'],
  ['hanuman', 'openai', 'partial'],
  ['hanuman', 'gmail', 'partial'],
  ['obsidian', 'notion', 'active'],
  ['wikipedia', 'notion', 'active'],
  ['chess', 'obsidian', 'active'],
]

function statusLabel(status: NodeStatus) {
  if (status === 'active') return 'Opérationnel'
  if (status === 'partial') return 'À consolider'
  if (status === 'planned') return 'Non connecté'
  return 'Cœur du système'
}

const initialViewport: Viewport = { x: 0, y: 0, scale: 1 }

export default function HanumanOSPage() {
  const navigate = useNavigate()
  const [selectedId, setSelectedId] = useState<NodeId | null>(null)
  const [viewport, setViewport] = useState<Viewport>(initialViewport)
  const dragStart = useRef<{ pointerX: number; pointerY: number; x: number; y: number } | null>(null)
  const selected = useMemo(() => nodes.find((node) => node.id === selectedId) ?? null, [selectedId])

  function openRoute(route?: string) {
    if (route) navigate(route)
  }

  function zoomBy(delta: number) {
    setViewport((current) => ({ ...current, scale: Math.min(1.6, Math.max(.72, current.scale + delta)) }))
  }

  return <section className="hanuman-os">
    <div className="hanuman-os__atmosphere" />
    <header className="hanuman-os__topline">
      <div><span className="hanuman-os__sigil">✦</span><b>HANUMAN</b><small>Celui qui relie les mondes</small></div>
      <span className="hanuman-os__health"><i /> Système opérationnel</span>
    </header>

    <div
      className={`hanuman-os__map${dragStart.current ? ' is-dragging' : ''}`}
      aria-label="Constellation Hanuman"
      onWheel={(event) => { event.preventDefault(); zoomBy(event.deltaY > 0 ? -.08 : .08) }}
      onPointerDown={(event) => {
        if ((event.target as HTMLElement).closest('button')) return
        event.currentTarget.setPointerCapture(event.pointerId)
        dragStart.current = { pointerX: event.clientX, pointerY: event.clientY, x: viewport.x, y: viewport.y }
      }}
      onPointerMove={(event) => {
        const start = dragStart.current
        if (!start) return
        setViewport((current) => ({ ...current, x: start.x + event.clientX - start.pointerX, y: start.y + event.clientY - start.pointerY }))
      }}
      onPointerUp={() => { dragStart.current = null }}
      onPointerCancel={() => { dragStart.current = null }}
    >
      <div className="hanuman-os__stars" />
      <div className="hanuman-os__world" style={{ transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.scale})` }}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          {links.map(([fromId, toId, status]) => {
            const from = nodes.find((node) => node.id === fromId)!
            const to = nodes.find((node) => node.id === toId)!
            const selectedLink = selectedId === fromId || selectedId === toId
            return <line key={`${fromId}-${toId}`} x1={from.x} y1={from.y} x2={to.x} y2={to.y} className={`hanuman-os__link hanuman-os__link--${status} ${selectedLink ? 'is-selected' : ''}`} vectorEffect="non-scaling-stroke" />
          })}
        </svg>

        {nodes.map(({ id, label, subtitle, x, y, status, icon: Icon, route }) => <button
          key={id}
          className={`hanuman-os__node hanuman-os__node--${id} hanuman-os__node--${status} ${selectedId === id ? 'is-selected' : ''}`}
          style={{ left: `${x}%`, top: `${y}%` }}
          onClick={() => setSelectedId(id)}
          onDoubleClick={() => openRoute(route)}
        >
          <span className="hanuman-os__orb"><Icon size={id === 'hanuman' ? 22 : 15} /></span>
          <span className="hanuman-os__label"><b>{label}</b><small>{subtitle}</small></span>
        </button>)}
      </div>
    </div>

    <div className="hanuman-os__zoom" aria-label="Contrôles de la constellation">
      <button onClick={() => zoomBy(-.12)} aria-label="Dézoomer"><Minus size={15} /></button>
      <span>{Math.round(viewport.scale * 100)}%</span>
      <button onClick={() => zoomBy(.12)} aria-label="Zoomer"><Plus size={15} /></button>
      <button onClick={() => setViewport(initialViewport)} aria-label="Recentrer"><RotateCcw size={14} /></button>
    </div>

    {selected && <aside className="hanuman-os__inspector">
      <button className="hanuman-os__inspector-close" onClick={() => setSelectedId(null)} aria-label="Fermer l’inspecteur"><X size={15} /></button>
      <p>CONSTELLATION / NŒUD</p>
      <h1>{selected.label}</h1>
      <span className={`hanuman-os__status hanuman-os__status--${selected.status}`}>{statusLabel(selected.status)}</span>
      <div className="hanuman-os__meta"><Network size={14} /> {links.filter(([from, to]) => from === selected.id || to === selected.id).length} connexions</div>
      <p className="hanuman-os__description">{selected.subtitle}. Hanuman orchestre ses échanges avec le reste de l’écosystème.</p>
      {selected.route ? <button className="hanuman-os__inspector-action" onClick={() => openRoute(selected.route)}>Entrer dans l’espace <ChevronRight size={16} /></button> : <small>Aucune orchestration dédiée stabilisée.</small>}
    </aside>}

    <footer className="hanuman-os__dock">
      <span>Glisser : déplacer</span><i /> <span>Molette : zoomer</span><i /> <span>Double-clic : ouvrir</span>
    </footer>
  </section>
}
