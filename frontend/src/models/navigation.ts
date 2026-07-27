import {
  Bot,
  Database,
  GitFork,
  HeartPulse,
  House,
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
  { label: 'Données', path: '/data', icon: Database },
  { label: 'Santé', path: '/health', icon: HeartPulse },
  { label: 'Agents IA', path: '/agents', icon: Bot },
  { label: 'Paramètres', path: '/settings', icon: Settings },
]
