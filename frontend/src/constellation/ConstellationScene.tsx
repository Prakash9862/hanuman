import { Minus, Plus, RotateCcw } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ConnectorInspector } from './ConnectorInspector'
import { ConnectorPlanet } from './ConnectorPlanet'
import { constellationConnectors, constellationRelations } from './constellationModel'
import { ConstellationRelations } from './ConstellationRelations'
import { HanumanCore } from './HanumanCore'
import { useConnectorHealth } from './useConnectorHealth'

type Viewport = { x: number; y: number; scale: number }
const initialViewport: Viewport = { x: 0, y: 0, scale: 1 }

export function ConstellationScene() {
  const navigate = useNavigate()
  const healthChecks = useConnectorHealth(constellationConnectors)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [previewedId, setPreviewedId] = useState<string | null>(null)
  const [viewport, setViewport] = useState(initialViewport)
  const dragStart = useRef<{ pointerX: number; pointerY: number; x: number; y: number } | null>(null)
  const activeId = previewedId ?? selectedId
  const inspectedConnector = useMemo(
    () => constellationConnectors.find(({ id }) => id === previewedId)
      ?? constellationConnectors.find(({ id }) => id === selectedId)
      ?? null,
    [previewedId, selectedId],
  )
  const relatedIds = useMemo(() => {
    if (!activeId) return new Set<string>()
    return new Set(constellationRelations.flatMap(({ from, to }) => (
      from === activeId || to === activeId ? [from, to] : []
    )))
  }, [activeId])

  function zoomBy(delta: number) {
    setViewport((current) => ({ ...current, scale: Math.min(1.35, Math.max(.72, current.scale + delta)) }))
  }

  function openRoute(route?: string) {
    if (route) navigate(route)
  }

  useEffect(() => {
    function closeInspection(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setSelectedId(null)
        setPreviewedId(null)
      }
    }
    window.addEventListener('keydown', closeInspection)
    return () => window.removeEventListener('keydown', closeInspection)
  }, [])

  return (
    <section className="constellation" aria-labelledby="constellation-title" aria-describedby="constellation-help">
      <header className="constellation__header">
        <div><p>Hanuman / Constellation</p><h1 id="constellation-title">Écosystème connecté</h1></div>
        <p className="constellation__legend"><span><i className="is-healthy" /> Opérationnel</span><span><i className="is-degraded" /> Dégradé</span><span><i className="is-down" /> Erreur</span><span><i className="is-unknown" /> Inconnu</span></p>
      </header>

      <div
        className={`constellation__viewport${dragStart.current ? ' is-dragging' : ''}`}
        aria-label="Carte interactive des connecteurs Hanuman"
        onWheel={(event) => { event.preventDefault(); zoomBy(event.deltaY > 0 ? -.08 : .08) }}
        onPointerDown={(event) => {
          if ((event.target as HTMLElement).closest('button')) return
          event.currentTarget.setPointerCapture(event.pointerId)
          dragStart.current = { pointerX: event.clientX, pointerY: event.clientY, x: viewport.x, y: viewport.y }
        }}
        onPointerMove={(event) => {
          if (!dragStart.current) return
          setViewport((current) => ({
            ...current,
            x: dragStart.current!.x + event.clientX - dragStart.current!.pointerX,
            y: dragStart.current!.y + event.clientY - dragStart.current!.pointerY,
          }))
        }}
        onPointerUp={() => { dragStart.current = null }}
        onPointerCancel={() => { dragStart.current = null }}
      >
        <div className="constellation__grid" aria-hidden="true" />
        <div className="constellation__world" style={{ transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.scale})` }}>
          <span className="constellation__orbit constellation__orbit--inner" aria-hidden="true" />
          <span className="constellation__orbit constellation__orbit--outer" aria-hidden="true" />
          <ConstellationRelations connectors={constellationConnectors} relations={constellationRelations} activeConnectorId={activeId} />
          <HanumanCore selected={selectedId === 'hanuman'} onSelect={() => setSelectedId('hanuman')} />
          {constellationConnectors.map((connector) => (
            <ConnectorPlanet
              key={connector.id}
              connector={connector}
              health={healthChecks[connector.id]?.state ?? 'unknown'}
              selected={selectedId === connector.id}
              muted={Boolean(activeId && activeId !== connector.id && !relatedIds.has(connector.id))}
              onInspect={setSelectedId}
              onPreview={setPreviewedId}
              onOpen={openRoute}
            />
          ))}
        </div>
      </div>

      <div className="constellation__controls" aria-label="Contrôles de la constellation">
        <button type="button" onClick={() => zoomBy(-.12)} aria-label="Dézoomer"><Minus size={16} /></button>
        <output aria-label="Niveau de zoom">{Math.round(viewport.scale * 100)}%</output>
        <button type="button" onClick={() => zoomBy(.12)} aria-label="Zoomer"><Plus size={16} /></button>
        <button type="button" onClick={() => setViewport(initialViewport)} aria-label="Recentrer"><RotateCcw size={15} /></button>
      </div>
      <p id="constellation-help" className="constellation__help">Survoler ou sélectionner pour révéler les flux · Double-cliquer ou utiliser la fiche pour ouvrir · Échap pour fermer</p>

      {selectedId === 'hanuman' && !inspectedConnector && (
        <aside className="connector-inspector connector-inspector--core" aria-label="Inspection de Hanuman">
          <div className="connector-inspector__heading"><div><p>Noyau / orchestration</p><h1>Hanuman</h1></div><button type="button" className="connector-inspector__close" onClick={() => setSelectedId(null)} aria-label="Fermer l’inspection">×</button></div>
          <p className="connector-inspector__description">Centre de coordination de l’écosystème. Hanuman n’est pas un connecteur.</p>
        </aside>
      )}
      {inspectedConnector && (
        <ConnectorInspector
          connector={inspectedConnector}
          health={healthChecks[inspectedConnector.id]?.state ?? 'unknown'}
          checkedAt={healthChecks[inspectedConnector.id]?.checkedAt}
          onClose={() => { setSelectedId(null); setPreviewedId(null) }}
          onOpen={openRoute}
        />
      )}
    </section>
  )
}
