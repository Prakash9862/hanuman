import {
  BookOpen,
  BrainCircuit,
  CalendarDays,
  ChevronRight,
  Github,
  Mail,
  Network,
  NotebookPen,
  Swords,
} from 'lucide-react'
import { useMemo, useState } from 'react'
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

const nodes: Node[] = [
  { id: 'hanuman', label: 'Hanuman', subtitle: 'Centre de gravité', x: 50, y: 50, status: 'core', icon: BrainCircuit },
  { id: 'obsidian', label: 'Obsidian', subtitle: 'Mémoire locale', x: 21, y: 35, status: 'active', icon: NotebookPen, route: '/orchestrations/obsidian-notion' },
  { id: 'notion', label: 'Notion', subtitle: 'Organisation', x: 79, y: 35, status: 'active', icon: Network, route: '/orchestrations/obsidian-notion' },
  { id: 'github', label: 'GitHub', subtitle: 'Développement', x: 50, y: 14, status: 'partial', icon: Github, route: '/orchestrations' },
  { id: 'calendar', label: 'Calendar', subtitle: 'Planification', x: 84, y: 68, status: 'partial', icon: CalendarDays },
  { id: 'wikipedia', label: 'Wikipédia', subtitle: 'Documentation', x: 66, y: 86, status: 'active', icon: BookOpen, route: '/orchestrations/wikipedia-notion' },
  { id: 'chess', label: 'Chess.com', subtitle: 'Parties et analyses', x: 34, y: 86, status: 'active', icon: Swords, route: '/orchestrations/chess-obsidian' },
  { id: 'openai', label: 'OpenAI', subtitle: 'Raisonnement', x: 16, y: 68, status: 'partial', icon: BrainCircuit },
  { id: 'gmail', label: 'Gmail', subtitle: 'À connecter', x: 8, y: 18, status: 'planned', icon: Mail },
]

const links: Array<[NodeId, NodeId, Exclude<NodeStatus, 'core'>]> = [
  ['hanuman', 'obsidian', 'active'],
  ['hanuman', 'notion', 'active'],
  ['hanuman', 'github', 'partial'],
  ['hanuman', 'calendar', 'partial'],
  ['hanuman', 'wikipedia', 'active'],
  ['hanuman', 'chess', 'active'],
  ['hanuman', 'openai', 'partial'],
  ['hanuman', 'gmail', 'planned'],
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

export default function HanumanOSPage() {
  const navigate = useNavigate()
  const [selectedId, setSelectedId] = useState<NodeId>('hanuman')
  const selected = useMemo(() => nodes.find((node) => node.id === selectedId) ?? nodes[0], [selectedId])

  return <section className="hanuman-os">
    <div className="hanuman-os__atmosphere" />
    <header className="hanuman-os__topline">
      <div><span className="hanuman-os__sigil">✦</span><b>HANUMAN</b><small>Celui qui relie les mondes</small></div>
      <span className="hanuman-os__health"><i /> Système opérationnel</span>
    </header>

    <div className="hanuman-os__map" aria-label="Constellation Hanuman">
      <div className="hanuman-os__stars" />
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
        className={`hanuman-os__node hanuman-os__node--${status} ${selectedId === id ? 'is-selected' : ''}`}
        style={{ left: `${x}%`, top: `${y}%` }}
        onClick={() => setSelectedId(id)}
        onDoubleClick={() => route && navigate(route)}
      >
        <span className="hanuman-os__orb"><Icon size={id === 'hanuman' ? 30 : 20} /></span>
        <span><b>{label}</b><small>{subtitle}</small></span>
      </button>)}
    </div>

    <aside className="hanuman-os__inspector">
      <p>CONSTELLATION / NŒUD</p>
      <h1>{selected.label}</h1>
      <span className={`hanuman-os__status hanuman-os__status--${selected.status}`}>{statusLabel(selected.status)}</span>
      <div className="hanuman-os__meta"><Network size={15} /> {links.filter(([from, to]) => from === selected.id || to === selected.id).length} connexions visibles</div>
      <p className="hanuman-os__description">{selected.subtitle}. Hanuman conserve cet outil à sa juste place et orchestre ses échanges avec le reste de l’écosystème.</p>
      {selected.route ? <button onClick={() => navigate(selected.route)}>Entrer dans l’espace <ChevronRight size={17} /></button> : <small>Cette étoile sera activée lorsqu’une orchestration stable lui sera associée.</small>}
    </aside>

    <footer className="hanuman-os__dock">
      <span>1 clic : inspecter</span><i /> <span>Double-clic : ouvrir</span><i /> <span>3 flux opérationnels</span>
    </footer>
  </section>
}
