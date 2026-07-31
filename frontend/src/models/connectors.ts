import {
  BookOpen,
  BrainCircuit,
  CalendarDays,
  Clock3,
  ContactRound,
  Cpu,
  Database,
  Github,
  Keyboard,
  Layers3,
  Mail,
  MapPin,
  Music2,
  Network,
  NotebookPen,
  Swords,
  Youtube,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export type ConnectorStatus = 'available' | 'partial' | 'planned'
export type ConnectorKind = 'external' | 'local'

export type ConnectorDefinition = {
  id: string
  label: string
  description: string
  kind: ConnectorKind
  status: ConnectorStatus
  route?: string
  icon: LucideIcon
}

export const connectorDefinitions: readonly ConnectorDefinition[] = [
  { id: 'notion', label: 'Notion', description: 'Organisation et destination de contenus.', kind: 'external', status: 'available', route: '/flows/obsidian-notion', icon: Network },
  { id: 'obsidian', label: 'Obsidian', description: 'Mémoire et bibliothèques locales.', kind: 'local', status: 'available', route: '/flows/obsidian-notion', icon: NotebookPen },
  { id: 'anki', label: 'Anki', description: 'Paquets, notes et cartes de révision.', kind: 'local', status: 'available', route: '/connectors?source=anki', icon: Layers3, },
  { id: 'github', label: 'GitHub', description: 'Projets et activité technique.', kind: 'external', status: 'partial', route: '/flows', icon: Github },
  { id: 'gmail', label: 'Gmail', description: 'Consultation de la messagerie.', kind: 'external', status: 'partial', route: '/flows/gmail', icon: Mail },
  { id: 'calendar', label: 'Google Calendar', description: 'Consultation des calendriers.', kind: 'external', status: 'available', route: '/flows/calendar', icon: CalendarDays },
  { id: 'wikipedia', label: 'Wikipédia', description: 'Recherche encyclopédique.', kind: 'external', status: 'available', route: '/flows/wikipedia-notion', icon: BookOpen },
  { id: 'chess', label: 'Chess.com', description: 'Parties et données échiquéennes.', kind: 'external', status: 'available', route: '/flows/chess-obsidian', icon: Swords },
  { id: 'stockfish', label: 'Stockfish', description: 'Moteur local d’analyse tactique.', kind: 'local', status: 'available', route: '/connectors?source=chess', icon: Cpu },
  { id: 'openai', label: 'OpenAI', description: 'Capacités de raisonnement assisté.', kind: 'external', status: 'partial', icon: BrainCircuit },
  { id: 'youtube', label: 'YouTube', description: 'Recherche vidéo et veille.', kind: 'external', status: 'partial', route: '/connectors?source=youtube', icon: Youtube },
  { id: 'gallica', label: 'Gallica', description: 'Patrimoine et sources de la BnF.', kind: 'external', status: 'available', route: '/connectors?source=gallica', icon: BookOpen },
  { id: 'imslp', label: 'IMSLP', description: 'Recherche de partitions.', kind: 'external', status: 'available', route: '/connectors?source=imslp', icon: Music2 },
  { id: 'maps', label: 'Google Maps', description: 'Trajets et rendez-vous.', kind: 'external', status: 'available', route: '/connectors?source=maps', icon: MapPin },
  { id: 'scid', label: 'SCID', description: 'Base locale de parties.', kind: 'local', status: 'available', route: '/connectors?source=chess', icon: Database },
  { id: 'clock', label: 'Horloge', description: 'Référentiel temporel d’Hanuman.', kind: 'local', status: 'available',
    route: '/connectors?source=clock', icon: Clock3, },

  // scaffold:connector-definitions:start
  { id: 'devdocs', label: 'DevDocs', description: 'Recherche et consultation de documentation technique.', kind: 'external', status: 'planned', route: '/connectors?source=devdocs', icon: BookOpen, },

  { id: 'contacts', label: 'Google Contacts', description: 'Consultation et recherche dans les contacts Google.', kind: 'external', status: 'available', route: '/connectors?source=contacts', icon: ContactRound, },

  { id: 'monkeytype', label: 'Monkeytype', description: 'Suivi des performances de frappe et des sessions d’entraînement.', kind: 'external', status: 'planned', route: '/connectors?source=monkeytype', icon: Keyboard, },
  // scaffold:connector-definitions:end
]

export type ConnectorWorkspaceId = 'youtube' | 'gallica' | 'imslp' | 'maps' | 'chess' | 'anki' | 'clock' | 'devdocs' | 'contacts'

export type ConnectorWorkspace = {
  id: ConnectorWorkspaceId
  label: string
  eyebrow: string
  placeholder: string
  icon: LucideIcon
}

export const connectorWorkspaces: readonly ConnectorWorkspace[] = [
  { id: 'youtube', label: 'YouTube', eyebrow: 'Vidéo et veille', placeholder: 'Rechercher une vidéo, une chaîne, un sujet…', icon: Youtube },
  { id: 'gallica', label: 'Gallica', eyebrow: 'Patrimoine et sources', placeholder: 'Rechercher une œuvre, un compositeur, un manuscrit…', icon: BookOpen },
  { id: 'imslp', label: 'IMSLP', eyebrow: 'Partitions', placeholder: 'Rechercher une œuvre ou un compositeur…', icon: Music2 },
  { id: 'maps', label: 'Google Maps', eyebrow: 'Trajets et rendez-vous', placeholder: 'Saisir une adresse ou un lieu…', icon: MapPin },
  { id: 'chess', label: 'Échecs', eyebrow: 'Moteurs et bases', placeholder: '', icon: Swords },
    {
    id: 'clock',
    label: 'Horloge',
    eyebrow: 'Référentiel temporel',
    placeholder: '',
    icon: Clock3,
  },
  {
    id: 'anki',
    label: 'Anki',
    eyebrow: 'Mémorisation et révision',
    placeholder: 'Rechercher un paquet ou une carte…',
    icon: Layers3,
  },
  {
  id: 'devdocs',
  label: 'DevDocs',
  eyebrow: 'Documentation technique',
  placeholder: 'Rechercher une API, une classe, une méthode…',
  icon: BookOpen,
  },
  {
  id: 'contacts',
  label: 'Google Contacts',
  eyebrow: 'Carnet d’adresses',
  placeholder: 'Rechercher un nom, un téléphone, un e-mail…',
  icon: ContactRound,
  },
]
