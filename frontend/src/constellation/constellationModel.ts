import type { ConnectorDefinition } from '../models/connectors'
import { connectorDefinitions } from '../models/connectors'
import { flowDefinitions } from '../models/flows'

export type ConnectorHealth = 'healthy' | 'degraded' | 'down' | 'unknown'

export type ConstellationConnector = ConnectorDefinition & {
  x: number
  y: number
  size: 'dwarf' | 'small' | 'medium' | 'large' | 'giant'
  palette: string
  family: 'terrestrial' | 'gas' | 'ice' | 'oceanic' | 'crystalline' | 'desert' | 'metallic' | 'volcanic' | 'forest'
  healthEndpoint?: string
}

export type ConstellationRelation = {
  id: string
  flowId: string
  from: string
  to: string
  direction: 'forward' | 'bidirectional'
}

const visualMetadata: Record<string, Omit<ConstellationConnector, keyof ConnectorDefinition>> = {
  notion: { x: 72, y: 24, size: 'giant', palette: 'ivory', family: 'terrestrial', healthEndpoint: '/notion/ping' },
  obsidian: { x: 29, y: 32, size: 'large', palette: 'violet', family: 'crystalline', healthEndpoint: '/obsidian/ping' },
  anki: { x: 44, y: 48, size: 'medium', palette: 'amber', family: 'desert', healthEndpoint: '/resources/anki/status', },
  github: { x: 48, y: 11, size: 'small', palette: 'graphite', family: 'metallic', healthEndpoint: '/github/ping' },
  gmail: { x: 8, y: 20, size: 'medium', palette: 'coral', family: 'gas', healthEndpoint: '/gmail/status' },
  calendar: { x: 86, y: 45, size: 'large', palette: 'azure', family: 'ice', healthEndpoint: '/calendar/status' },
  wikipedia: { x: 91, y: 82, size: 'medium', palette: 'silver', family: 'terrestrial', healthEndpoint: '/wikipedia/ping' },
  chess: { x: 31, y: 81, size: 'giant', palette: 'umber', family: 'desert', healthEndpoint: '/chess/ping' },
  stockfish: { x: 7, y: 91, size: 'dwarf', palette: 'steel', family: 'metallic', healthEndpoint: '/resources/programs/stockfish/status' },
  openai: { x: 11, y: 56, size: 'large', palette: 'jade', family: 'oceanic', healthEndpoint: '/openai/ping' },
  youtube: { x: 93, y: 14, size: 'small', palette: 'red', family: 'volcanic', healthEndpoint: '/resources/youtube/status' },
  gallica: { x: 75, y: 89, size: 'large', palette: 'gold', family: 'gas', healthEndpoint: '/resources/gallica/status' },
  imslp: { x: 56, y: 93, size: 'dwarf', palette: 'rose', family: 'ice', healthEndpoint: '/resources/imslp/status' },
  maps: { x: 96, y: 61, size: 'dwarf', palette: 'green', family: 'forest', healthEndpoint: '/resources/maps/status' },
  scid: { x: 17, y: 73, size: 'small', palette: 'blue', family: 'oceanic', healthEndpoint: '/resources/programs/scid/status' },
  clock: { x: 62, y: 58, size: 'small', palette: 'rose', family: 'ice', healthEndpoint: '/resources/clock/status', },

  // scaffold:visual-metadata:start
  'devdocs': { x: 41, y: 39, size: 'small', palette: 'jade', family: 'metallic', healthEndpoint: '/resources/devdocs/status', },
  // scaffold:visual-metadata:end
}


export const constellationConnectors: readonly ConstellationConnector[] = connectorDefinitions
  .filter(({ id }) => visualMetadata[id])
  .map((connector) => ({ ...connector, ...visualMetadata[connector.id] }))

const relationPairs = flowDefinitions.flatMap((flow) => {
  const direction = flow.title.includes('↔') ? 'bidirectional' as const : 'forward' as const
  return flow.relations.map(([from, to]) => ({
    id: `${flow.id}-${from}-${to}`,
    flowId: flow.id,
    from,
    to,
    direction,
  }))
})

export const constellationRelations: readonly ConstellationRelation[] = relationPairs

export function relatedFlowCount(connectorId: string) {
  return flowDefinitions.filter((flow) => flow.connectorIds.includes(connectorId)).length
}

export function connectorRole(kind: ConnectorDefinition['kind']) {
  return kind === 'local' ? 'Programme local' : 'Service externe'
}

export function healthLabel(health: ConnectorHealth) {
  if (health === 'healthy') return 'Opérationnel'
  if (health === 'degraded') return 'État dégradé'
  if (health === 'down') return 'Indisponible'
  return 'État inconnu'
}
