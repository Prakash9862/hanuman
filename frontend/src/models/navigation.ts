import {
  Bot,
  GitFork,
  House,
  NotebookTabs,
  Plug,
  Settings,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export type NavigationItem = {
  label: string
  path: string
  end?: boolean
  icon: LucideIcon
}

export const navigationItems: readonly NavigationItem[] = [
  { label: 'Accueil', path: '/', end: true, icon: House },
  { label: 'Flux', path: '/flows', icon: GitFork },
  { label: 'Connecteurs', path: '/connectors', icon: Plug },
  { label: 'Journal de Vie', path: '/journal', icon: NotebookTabs },
  { label: 'Agents IA', path: '/agents', icon: Bot },
  { label: 'Paramètres', path: '/settings', icon: Settings },
]