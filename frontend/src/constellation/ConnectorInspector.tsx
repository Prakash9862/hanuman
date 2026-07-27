import { ArrowUpRight, Clock3, GitFork, X } from 'lucide-react'

import type { ConnectorHealth, ConstellationConnector } from './constellationModel'
import { connectorRole, healthLabel, relatedFlowCount } from './constellationModel'

type Props = {
  connector: ConstellationConnector
  health: ConnectorHealth
  checkedAt?: string
  onClose: () => void
  onOpen: (route?: string) => void
}

export function ConnectorInspector({ connector, health, checkedAt, onClose, onOpen }: Props) {
  const Icon = connector.icon
  const flowCount = relatedFlowCount(connector.id)

  return (
    <aside className={`connector-inspector connector-inspector--${connector.palette}`} aria-label={`Inspection de ${connector.label}`} aria-live="polite">
      <div className="connector-inspector__heading">
        <span className={`connector-inspector__emblem connector-inspector__emblem--${connector.palette}`}><Icon size={19} /></span>
        <div><p>Connecteur / inspection</p><h1>{connector.label}</h1></div>
        <button type="button" className="connector-inspector__close" onClick={onClose} aria-label="Fermer l’inspection"><X size={16} /></button>
      </div>
      <p className="connector-inspector__description">{connector.description}</p>
      <dl className="connector-inspector__facts">
        <div><dt>Rôle</dt><dd>{connectorRole(connector.kind)}</dd></div>
        <div><dt>État</dt><dd><i className={`health-indicator is-${health}`} />{healthLabel(health)}</dd></div>
        <div><dt><GitFork size={13} /> Flux liés</dt><dd>{flowCount}</dd></div>
        <div><dt><Clock3 size={13} /> Dernier contrôle</dt><dd>{checkedAt ? new Date(checkedAt).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : 'Non renseigné'}</dd></div>
      </dl>
      {connector.route ? (
        <button type="button" className="connector-inspector__action" onClick={() => onOpen(connector.route)}>
          Ouvrir l’espace associé <ArrowUpRight size={16} />
        </button>
      ) : <p className="connector-inspector__unavailable">Aucun espace dédié disponible.</p>}
    </aside>
  )
}
