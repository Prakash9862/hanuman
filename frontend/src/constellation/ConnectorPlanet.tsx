import type { CSSProperties, FocusEvent, MouseEvent } from 'react'

import type { ConnectorHealth, ConstellationConnector } from './constellationModel'
import { healthLabel } from './constellationModel'

type Props = {
  connector: ConstellationConnector
  health: ConnectorHealth
  selected: boolean
  muted: boolean
  onInspect: (id: string) => void
  onPreview: (id: string | null) => void
  onOpen: (route?: string) => void
}

export function ConnectorPlanet({
  connector,
  health,
  selected,
  muted,
  onInspect,
  onPreview,
  onOpen,
}: Props) {
  const className = [
    'connector-planet',
    `connector-planet--${connector.size}`,
    `connector-planet--${connector.palette}`,
    `connector-planet--${connector.family}`,
    `is-${health}`,
    selected ? 'is-selected' : '',
    muted ? 'is-muted' : '',
  ].filter(Boolean).join(' ')

  function preview() {
    onPreview(connector.id)
  }

  function stopPreview(event: MouseEvent<HTMLButtonElement> | FocusEvent<HTMLButtonElement>) {
    if (!event.currentTarget.matches(':hover, :focus-visible')) onPreview(null)
  }

  return (
    <button
      type="button"
      className={className}
      style={{ '--planet-x': `${connector.x}%`, '--planet-y': `${connector.y}%` } as CSSProperties}
      aria-label={`${connector.label}, ${connector.description}, ${healthLabel(health)}`}
      aria-pressed={selected}
      onClick={() => onInspect(connector.id)}
      onDoubleClick={() => onOpen(connector.route)}
      onMouseEnter={preview}
      onMouseLeave={stopPreview}
      onFocus={preview}
      onBlur={stopPreview}
    >
      <span className="connector-planet__halo" aria-hidden="true" />
      <span className="connector-planet__body" aria-hidden="true">
        <span className="connector-planet__surface" />
      </span>
      <span className="connector-planet__label">
        <b>{connector.label}</b>
        <i className={`connector-planet__status is-${health}`} aria-hidden="true" />
      </span>
    </button>
  )
}
