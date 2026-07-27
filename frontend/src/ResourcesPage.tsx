import {
  BookOpen,
  ExternalLink,
  MapPin,
  Music2,
  Pause,
  Play,
  RefreshCw,
  Search,
  Swords,
  Youtube,
} from 'lucide-react'
import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import {
  connectorDefinitions,
  connectorWorkspaces,
} from './models/connectors'
import type { ConnectorStatus, ConnectorWorkspaceId } from './models/connectors'

const API_BASE = 'http://127.0.0.1:8000'

type SearchResult = {
  title?: string
  description?: string
  url?: string
  thumbnail?: string
  channel?: string
  creators?: string[]
  dates?: string[]
}

type ProgramStatus = {
  id: string
  label: string
  ok: boolean
  installed: boolean
  path?: string | null
  version?: string | null
  message?: string
}

type SearchPayload = {
  ok?: boolean
  detail?: string
  message?: string
  results?: SearchResult[]
  next_page_token?: string | null
  total_results?: number | null
  fallback_url?: string | null
}

type AnalysisQueue = {
  total: number
  analysed: number
  pending: number
}

type AnalysisState = {
  status: string
  total: number
  completed: number
  failed: number
  remaining: number
  current?: string | null
  depth?: number | null
  batch_limit?: number | null
  started_at?: string | null
  updated_at?: string | null
  finished_at?: string | null
  errors?: Array<{ path: string; error: string }>
}

type AnalysisPayload = {
  ok?: boolean
  message?: string
  queue?: AnalysisQueue
  state?: AnalysisState
}

const statusLabels: Record<ConnectorStatus, string> = {
  available: 'Disponible',
  partial: 'À consolider',
  planned: 'Prévu',
}

export default function ResourcesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialSource = searchParams.get('source') as ConnectorWorkspaceId | null
  const [active, setActive] = useState<ConnectorWorkspaceId>(
    connectorWorkspaces.some((workspace) => workspace.id === initialSource) && initialSource ? initialSource : 'gallica',
  )
  const [query, setQuery] = useState('')
  const [lastQuery, setLastQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [programs, setPrograms] = useState<ProgramStatus[]>([])
  const [message, setMessage] = useState<string | null>(null)
  const [fallbackUrl, setFallbackUrl] = useState<string | null>(null)
  const [nextPageToken, setNextPageToken] = useState<string | null>(null)
  const [totalResults, setTotalResults] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [analysisQueue, setAnalysisQueue] = useState<AnalysisQueue>({ total: 0, analysed: 0, pending: 0 })
  const [analysisState, setAnalysisState] = useState<AnalysisState>({ status: 'idle', total: 0, completed: 0, failed: 0, remaining: 0 })
  const [analysisBusy, setAnalysisBusy] = useState(false)
  const [knowledgeBusy, setKnowledgeBusy] = useState(false)

  const current = useMemo(
    () => connectorWorkspaces.find((workspace) => workspace.id === active) ?? connectorWorkspaces[0],
    [active],
  )
  const analysisRunning = ['running', 'stopping'].includes(analysisState.status)
  const batchProgress = analysisState.total > 0 ? Math.round((analysisState.completed / analysisState.total) * 100) : 0
  const libraryProgress = analysisQueue.total > 0 ? Math.round((analysisQueue.analysed / analysisQueue.total) * 100) : 0

  async function refreshChessStatus() {
    try {
      const [programResponse, analysisResponse] = await Promise.all([
        fetch(`${API_BASE}/resources/programs/status`),
        fetch(`${API_BASE}/resources/chess/analysis/status`),
      ])
      const programPayload = await programResponse.json()
      const analysisPayload = await analysisResponse.json() as AnalysisPayload
      setPrograms(programPayload.programs ?? [])
      setAnalysisQueue(analysisPayload.queue ?? { total: 0, analysed: 0, pending: 0 })
      setAnalysisState(analysisPayload.state ?? { status: 'idle', total: 0, completed: 0, failed: 0, remaining: 0 })
    } catch {
      setMessage('Impossible de lire l’état de l’environnement d’analyse')
    }
  }

  useEffect(() => {
    if (active !== 'chess') return
    void refreshChessStatus()
    const timer = window.setInterval(() => void refreshChessStatus(), analysisRunning ? 2000 : 8000)
    return () => window.clearInterval(timer)
  }, [active, analysisRunning])

  function selectSource(source: ConnectorWorkspaceId) {
    setActive(source)
    setSearchParams({ source })
    setQuery('')
    setLastQuery('')
    setResults([])
    setMessage(null)
    setFallbackUrl(null)
    setNextPageToken(null)
    setTotalResults(null)
  }

  async function fetchSearch(source: 'youtube' | 'gallica' | 'imslp', normalized: string, pageToken?: string): Promise<SearchPayload> {
    const params = new URLSearchParams({
      q: normalized,
      max_results: source === 'youtube' ? '25' : source === 'imslp' ? '20' : '12',
    })
    if (pageToken) params.set('page_token', pageToken)
    const response = await fetch(`${API_BASE}/resources/${source}/search?${params.toString()}`)
    const payload = await response.json() as SearchPayload
    if (!response.ok) throw new Error(payload.detail ?? `${current.label} indisponible`)
    return payload
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const normalized = query.trim()
    if (!normalized || active === 'chess') return
    setMessage(null)
    setFallbackUrl(null)
    setResults([])
    setNextPageToken(null)
    setTotalResults(null)
    setLastQuery(normalized)
    try {
      if (active === 'maps') {
        const response = await fetch(`${API_BASE}/resources/maps/directions?location=${encodeURIComponent(normalized)}`)
        const payload = await response.json()
        if (!response.ok || !payload.url) throw new Error(payload.detail ?? 'Google Maps indisponible')
        window.open(payload.url, '_blank', 'noopener,noreferrer')
        return
      }
      setLoading(true)
      const payload = await fetchSearch(active, normalized)
      const nextResults = payload.results ?? []
      setResults(nextResults)
      setNextPageToken(payload.next_page_token ?? null)
      setTotalResults(payload.total_results ?? null)
      setFallbackUrl(payload.fallback_url ?? null)
      if (payload.ok === false) setMessage(payload.message ?? `${current.label} est temporairement indisponible`)
      else if (!nextResults.length) setMessage(`Aucun résultat trouvé dans ${current.label}`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `Impossible de joindre ${current.label}`)
    } finally {
      setLoading(false)
    }
  }

  async function loadMoreYoutube() {
    if (active !== 'youtube' || !nextPageToken || !lastQuery || loadingMore) return
    setLoadingMore(true)
    setMessage(null)
    try {
      const payload = await fetchSearch('youtube', lastQuery, nextPageToken)
      setResults((currentResults) => [...currentResults, ...(payload.results ?? [])])
      setNextPageToken(payload.next_page_token ?? null)
      setTotalResults(payload.total_results ?? totalResults)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Impossible de charger la suite')
    } finally {
      setLoadingMore(false)
    }
  }

  async function startAnalysis(limit: number, depth: number) {
    setAnalysisBusy(true)
    setMessage(null)
    try {
      const response = await fetch(`${API_BASE}/resources/chess/analysis/start?limit=${limit}&depth=${depth}`, { method: 'POST' })
      const payload = await response.json() as AnalysisPayload
      setMessage(payload.message ?? null)
      await refreshChessStatus()
    } catch {
      setMessage('Impossible de démarrer Stockfish')
    } finally {
      setAnalysisBusy(false)
    }
  }

  async function stopAnalysis() {
    setAnalysisBusy(true)
    try {
      const response = await fetch(`${API_BASE}/resources/chess/analysis/stop`, { method: 'POST' })
      const payload = await response.json() as AnalysisPayload
      setMessage(payload.message ?? null)
      await refreshChessStatus()
    } finally {
      setAnalysisBusy(false)
    }
  }

  async function refreshChessKnowledge() {
    setKnowledgeBusy(true)
    setMessage(null)
    try {
      const response = await fetch(`${API_BASE}/resources/chess/knowledge/refresh`, { method: 'POST' })
      const payload = await response.json() as AnalysisPayload
      if (!response.ok) throw new Error((payload as SearchPayload).detail ?? 'Actualisation Chess impossible')
      setMessage(payload.message ?? 'Connaissances Chess actualisées')
      await refreshChessStatus()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Actualisation Chess impossible')
    } finally {
      setKnowledgeBusy(false)
    }
  }

  const ActiveIcon = current.icon

  return (
    <div className="resources-page">
      <header className="resources-hero">
        <div><p className="eyebrow">Hanuman / Connecteurs</p><h1>Les systèmes reliés à Hanuman.</h1><p>Services externes et programmes locaux utilisés par les flux, la recherche et les bibliothèques.</p></div>
      </header>

      <section className="connectors-catalog" aria-label="Catalogue des connecteurs">
        {connectorDefinitions.map(({ id, label, description, kind, status, route, icon: Icon }) => (
          <article key={id} className="connector-card">
            <span className="connector-card__icon"><Icon size={19} /></span>
            <div><b>{label}</b><p>{description}</p></div>
            <span className={`connector-card__status connector-card__status--${status}`}>{statusLabels[status]}</span>
            <small>{kind === 'local' ? 'Programme local' : 'Système externe'}</small>
            {route && <Link to={route}>Ouvrir <ExternalLink size={13} /></Link>}
          </article>
        ))}
      </section>

      <div className="section-heading connectors-workspaces-heading">
        <div><p className="eyebrow">Espaces existants</p><h2>Recherche et programmes</h2></div>
      </div>
      <section className="resources-shell">
        <nav className="resources-tabs" aria-label="Connecteurs avec espace dédié">
          {connectorWorkspaces.map(({ id, label, eyebrow, icon: Icon }) => (
            <button key={id} type="button" className={active === id ? 'is-active' : ''} onClick={() => selectSource(id)}>
              <Icon size={18} /><span><b>{label}</b><small>{eyebrow}</small></span>
            </button>
          ))}
        </nav>

        <div className="resources-console">
          <div className="resources-console__heading"><span className="resources-console__icon"><ActiveIcon size={23} /></span><div><p>{current.eyebrow}</p><h2>{current.label}</h2></div></div>

          {active !== 'chess' && (
            <form className="resources-search" onSubmit={handleSubmit}>
              <Search size={19} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={current.placeholder} autoFocus />
              <button type="submit" disabled={loading}>{loading ? 'Recherche…' : active === 'maps' ? 'Itinéraire' : 'Rechercher'}</button>
            </form>
          )}

          {message && <div className="resources-message"><span>{message}</span>{fallbackUrl && <a href={fallbackUrl} target="_blank" rel="noreferrer">Ouvrir la recherche dans Gallica <ExternalLink size={14} /></a>}</div>}

          {active === 'chess' && (
            <>
              <div className="resource-programs">
                {programs.map((program) => (
                  <article key={program.id} className={program.ok ? 'is-ok' : 'is-missing'}>
                    <span className="resource-programs__dot" />
                    <div><b>{program.label}</b><small>{program.version || program.message || 'État inconnu'}</small><code>{program.path || 'Non installé'}</code></div>
                  </article>
                ))}
                <article className="is-ok"><span className="resource-programs__dot" /><div><b>Chess.com</b><small>Parties et PGN</small><code>Connecteur distant</code></div></article>
                <article className="is-ok"><span className="resource-programs__dot" /><div><b>Obsidian</b><small>Notes d’analyse</small><code>Destination locale</code></div></article>
              </div>

              <section style={{ marginTop: 24, padding: 22, border: '1px solid var(--border, #d7d1c5)', borderRadius: 18 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                  <div><p className="eyebrow">File d’analyse</p><h3 style={{ margin: 0 }}>Stockfish en arrière-plan</h3></div>
                  <button type="button" onClick={() => void refreshChessStatus()} disabled={analysisBusy} style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}><RefreshCw size={15} /> Actualiser</button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12, marginTop: 18 }}>
                  <article><small>Bibliothèque</small><strong style={{ display: 'block', fontSize: 24 }}>{analysisQueue.analysed} / {analysisQueue.total}</strong></article>
                  <article><small>À analyser</small><strong style={{ display: 'block', fontSize: 24 }}>{analysisQueue.pending}</strong></article>
                  <article><small>État</small><strong style={{ display: 'block', fontSize: 18 }}>{analysisState.status}</strong></article>
                  <article><small>Échecs du lot</small><strong style={{ display: 'block', fontSize: 24 }}>{analysisState.failed}</strong></article>
                </div>

                <div style={{ marginTop: 18 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}><small>Progression bibliothèque</small><small>{libraryProgress} %</small></div>
                  <progress value={analysisQueue.analysed} max={Math.max(analysisQueue.total, 1)} style={{ width: '100%', height: 14 }} />
                </div>

                {analysisState.total > 0 && (
                  <div style={{ marginTop: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}><small>Lot actuel : {analysisState.completed} / {analysisState.total}</small><small>{batchProgress} %</small></div>
                    <progress value={analysisState.completed} max={Math.max(analysisState.total, 1)} style={{ width: '100%', height: 14 }} />
                    {analysisState.current && <code style={{ display: 'block', marginTop: 8, overflowWrap: 'anywhere' }}>{analysisState.current}</code>}
                  </div>
                )}

                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 20 }}>
                  {!analysisRunning ? (
                    <>
                      <button type="button" onClick={() => void startAnalysis(10, 12)} disabled={analysisBusy || analysisQueue.pending === 0}><Play size={15} /> 10 parties · rapide</button>
                      <button type="button" onClick={() => void startAnalysis(50, 14)} disabled={analysisBusy || analysisQueue.pending === 0}><Play size={15} /> 50 parties · standard</button>
                      <button type="button" onClick={() => void startAnalysis(1000, 16)} disabled={analysisBusy || analysisQueue.pending === 0}><Play size={15} /> Tout analyser</button>
                    </>
                  ) : (
                    <button type="button" onClick={() => void stopAnalysis()} disabled={analysisBusy}><Pause size={15} /> Arrêter après la position en cours</button>
                  )}
                </div>
                <div style={{ marginTop: 18, paddingTop: 18, borderTop: '1px solid var(--border, #d7d1c5)' }}>
                  <button type="button" onClick={() => void refreshChessKnowledge()} disabled={knowledgeBusy || analysisRunning}>
                    <RefreshCw size={15} className={knowledgeBusy ? 'spin' : ''} /> {knowledgeBusy ? 'Actualisation…' : 'Actualiser les connaissances Chess'}
                  </button>
                  <p style={{ marginBottom: 0, opacity: 0.72 }}>Relit les analyses persistées et reconstruit les vues Obsidian, sans Chess.com ni Stockfish.</p>
                </div>
                <p style={{ marginBottom: 0, opacity: 0.72 }}>Les parties déjà analysées sont ignorées. Une interruption ne détruit rien : le prochain lot reprend sur les notes restantes.</p>
              </section>
            </>
          )}

          {active !== 'chess' && !message && !loading && results.length === 0 && (
            <div className="resources-empty"><ActiveIcon size={28} /><b>{active === 'maps' ? 'Prépare un trajet' : `Recherche dans ${current.label}`}</b><span>{current.placeholder}</span></div>
          )}

          {results.length > 0 && (
            <>
              <div className="resources-results-meta"><span>{results.length} résultat{results.length > 1 ? 's' : ''} affiché{results.length > 1 ? 's' : ''}</span>{totalResults !== null && <small>sur environ {totalResults.toLocaleString('fr-FR')}</small>}</div>
              <div className="resource-results">
                {results.map((item, index) => (
                  <a key={`${item.url}-${index}`} href={item.url} target="_blank" rel="noreferrer">
                    {item.thumbnail && <img src={item.thumbnail} alt="" />}
                    <div><b>{item.title ?? 'Résultat'}</b><span>{item.channel ?? item.creators?.join(', ') ?? item.description ?? item.dates?.join(', ') ?? ''}</span></div>
                    <ExternalLink size={16} />
                  </a>
                ))}
              </div>
              {active === 'youtube' && nextPageToken && <button className="resources-load-more" type="button" onClick={() => void loadMoreYoutube()} disabled={loadingMore}>{loadingMore ? 'Chargement…' : 'Charger 25 résultats de plus'}</button>}
            </>
          )}
        </div>
      </section>
    </div>
  )
}
