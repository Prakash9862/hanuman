import type { ConnectorDefinition } from '../models/connectors'
import { connectorDefinitions } from '../models/connectors'
import { flowDefinitions } from '../models/flows'

export type ConnectorHealth = 'healthy' | 'degraded' | 'down' | 'unknown'

export type ConstellationConnector = ConnectorDefinition & {
  x: number
  y: number
  size: 'small' | 'medium' | 'large'
  palette: string
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
  notion: { x: 74, y: 27, size: 'large', palette: 'ivory', healthEndpoint: '/notion/ping' },
  obsidian: { x: 27, y: 30, size: 'large', palette: 'violet', healthEndpoint: '/obsidian/ping' },
  github: { x: 51, y: 13, size: 'medium', palette: 'graphite', healthEndpoint: '/github/ping' },
  gmail: { x: 10, y: 17, size: 'medium', palette: 'coral', healthEndpoint: '/gmail/status' },
  calendar: { x: 88, y: 49, size: 'medium', palette: 'azure', healthEndpoint: '/calendar/status' },
  wikipedia: { x: 89, y: 79, size: 'medium', palette: 'silver', healthEndpoint: '/wikipedia/ping' },
  chess: { x: 29, y: 79, size: 'large', palette: 'umber', healthEndpoint: '/chess/ping' },
  stockfish: { x: 10, y: 87, size: 'small', palette: 'steel', healthEndpoint: '/resources/programs/stockfish/status' },
  openai: { x: 12, y: 53, size: 'medium', palette: 'jade', healthEndpoint: '/openai/ping' },
  youtube: { x: 91, y: 17, size: 'medium', palette: 'red', healthEndpoint: '/resources/youtube/status' },
  gallica: { x: 73, y: 86, size: 'medium', palette: 'gold', healthEndpoint: '/resources/gallica/status' },
  imslp: { x: 54, y: 88, size: 'small', palette: 'rose', healthEndpoint: '/resources/imslp/status' },
  maps: { x: 94, y: 63, size: 'small', palette: 'green', healthEndpoint: '/resources/maps/status' },
  scid: { x: 17, y: 72, size: 'small', palette: 'blue', healthEndpoint: '/resources/programs/scid/status' },
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
