import {
  BookOpen,
  CalendarDays,
  GitBranch,
  GitCompareArrows,
  Mail,
  Swords,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export type FlowTone = 'violet' | 'green' | 'graphite' | 'red'
export type FlowKind = 'flow' | 'read-only-space'

export type FlowDefinition = {
  id: string
  title: string
  description: string
  path: string
  tone: FlowTone
  status: string
  kind: FlowKind
  icon: LucideIcon
}

export const flowDefinitions: readonly FlowDefinition[] = [
  {
    id: 'obsidian-notion',
    title: 'Obsidian ↔ Notion',
    description: 'Explorer le vault, publier, importer, comparer et suivre les échanges.',
    path: '/flows/obsidian-notion',
    tone: 'violet',
    status: 'Opérationnel',
    kind: 'flow',
    icon: GitCompareArrows,
  },
  {
    id: 'wikipedia-notion',
    title: 'Wikipédia → Notion',
    description: 'Transformer une recherche encyclopédique en page Notion structurée.',
    path: '/flows/wikipedia-notion',
    tone: 'green',
    status: 'Opérationnel',
    kind: 'flow',
    icon: BookOpen,
  },
  {
    id: 'github-notion',
    title: 'GitHub → Notion',
    description: 'Faire remonter projets, issues et activité technique dans Notion.',
    path: '/flows',
    tone: 'graphite',
    status: 'À consolider',
    kind: 'flow',
    icon: GitBranch,
  },
  {
    id: 'chess-obsidian',
    title: 'Chess.com → Obsidian',
    description: 'Importer les parties de prakasch et les organiser par note et code ECO.',
    path: '/flows/chess-obsidian',
    tone: 'red',
    status: 'Opérationnel',
    kind: 'flow',
    icon: Swords,
  },
  {
    id: 'gmail',
    title: 'Gmail',
    description: 'Consulter la boîte de réception et repérer les messages importants.',
    path: '/flows/gmail',
    tone: 'graphite',
    status: 'Lecture seule',
    kind: 'read-only-space',
    icon: Mail,
  },
  {
    id: 'calendar',
    title: 'Google Calendar',
    description: 'Consulter les calendriers et afficher les prochains événements.',
    path: '/flows/calendar',
    tone: 'green',
    status: 'Lecture seule',
    kind: 'read-only-space',
    icon: CalendarDays,
  },
]
