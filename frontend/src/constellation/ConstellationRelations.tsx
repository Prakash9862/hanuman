import { useId } from 'react'

import type { ConstellationConnector, ConstellationRelation } from './constellationModel'

type Props = {
  connectors: readonly ConstellationConnector[]
  relations: readonly ConstellationRelation[]
  activeConnectorId: string | null
}

export function ConstellationRelations({ connectors, relations, activeConnectorId }: Props) {
  const markerId = useId().replace(/:/g, '')
  const connectorById = new Map(connectors.map((connector) => [connector.id, connector]))

  return (
    <svg className="constellation-relations" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <marker id={`${markerId}-end`} viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M0 0 8 4 0 8Z" />
        </marker>
      </defs>
      {relations.map((relation) => {
        const from = connectorById.get(relation.from)
        const to = connectorById.get(relation.to)
        if (!from || !to) return null
        const active = activeConnectorId === relation.from || activeConnectorId === relation.to
        return (
          <line
            key={relation.id}
            x1={from.x}
            y1={from.y}
            x2={to.x}
            y2={to.y}
            className={`constellation-relation${active ? ' is-active' : ''}`}
            markerEnd={active ? `url(#${markerId}-end)` : undefined}
            markerStart={active && relation.direction === 'bidirectional' ? `url(#${markerId}-end)` : undefined}
            vectorEffect="non-scaling-stroke"
          />
        )
      })}
    </svg>
  )
}
