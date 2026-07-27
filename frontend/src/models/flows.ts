import {
  BookOpen,
  GitBranch,
  GitCompareArrows,
  Swords,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export type FlowTone = 'violet' | 'green' | 'graphite' | 'red'
export type FlowDefinition = {
  id: string
  title: string
  description: string
  path: string
  connectorIds: readonly string[]
  relations: ReadonlyArray<readonly [string, string]>
  tone: FlowTone
  status: string
  icon: LucideIcon
}

export const flowDefinitions: readonly FlowDefinition[] = [
  {
    id: 'obsidian-notion',
    title: 'Obsidian ↔ Notion',
    description: 'Explorer le vault, publier, importer, comparer et suivre les échanges.',
    path: '/flows/obsidian-notion',
    connectorIds: ['obsidian', 'notion'],
    relations: [['obsidian', 'notion']],
    tone: 'violet',
    status: 'Opérationnel',
    icon: GitCompareArrows,
  },
  {
    id: 'wikipedia-notion',
    title: 'Wikipédia → Notion',
    description: 'Transformer une recherche encyclopédique en page Notion structurée.',
    path: '/flows/wikipedia-notion',
    connectorIds: ['wikipedia', 'notion'],
    relations: [['wikipedia', 'notion']],
    tone: 'green',
    status: 'Opérationnel',
    icon: BookOpen,
  },
  {
    id: 'github-notion',
    title: 'GitHub → Notion',
    description: 'Faire remonter projets, issues et activité technique dans Notion.',
    path: '/flows/github-project-memory',
    connectorIds: ['github', 'notion'],
    relations: [['github', 'notion']],
    tone: 'graphite',
    status: 'Disponible',
    icon: GitBranch,
  },
  {
    id: 'chess-obsidian',
    title: 'Chess.com → Stockfish → Obsidian / SCID',
    description: 'Importer les parties, les analyser avec Stockfish et les organiser dans Obsidian et SCID.',
    path: '/flows/chess-obsidian',
    connectorIds: ['chess', 'stockfish', 'obsidian', 'scid'],
    relations: [['chess', 'stockfish'], ['stockfish', 'obsidian'], ['stockfish', 'scid']],
    tone: 'red',
    status: 'Opérationnel',
    icon: Swords,
  },
]
