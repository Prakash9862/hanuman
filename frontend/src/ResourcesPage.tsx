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
type CatalogFilter = 'all' | 'external' | 'local' | 'available' | 'partial'

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

type ClockSnapshot = {
  ok: boolean
  timezone: string
  local_datetime: string
  utc_datetime: string
  unix_timestamp: number
  date: string
  time: string
  weekday: number
  weekday_name: string
  iso_week: number
  period: 'night' | 'morning' | 'afternoon' | 'evening'
}

type DevdocsDocumentation = {
  slug: string
  name: string
  version?: string | null
  release?: string | null
  updated_at?: string | null
  icon?: string | null
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

type GoogleContact = {
  resource_name: string
  name: string
  given_name?: string | null
  family_name?: string | null
  emails: string[]
  phones: string[]
  organizations: string[]
  photo_url?: string | null
}

type ContactsPayload = {
  ok?: boolean
  count?: number
  contacts?: GoogleContact[]
  next_page_token?: string | null
  total_items?: number | null
  detail?: string
  message?: string
}

const statusLabels: Record<ConnectorStatus, string> = {
  available: 'Disponible',
  partial: 'À consolider',
  planned: 'Prévu',
}

export default function ResourcesPage() {
  const [searchParams] = useSearchParams()
  const initialSource = searchParams.get('source') as ConnectorWorkspaceId | null
  const [active, setActive] = useState<ConnectorWorkspaceId>(
    connectorWorkspaces.some((workspace) => workspace.id === initialSource) && initialSource ? initialSource : 'gallica',
  )
  const [catalogQuery, setCatalogQuery] = useState('')
  const [catalogFilter, setCatalogFilter] = useState<CatalogFilter>('all')
  const [query, setQuery] = useState('')
  const [lastQuery, setLastQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [programs, setPrograms] = useState<ProgramStatus[]>([])
  const [clockSnapshot, setClockSnapshot] = useState<ClockSnapshot | null>(null)
  const [clockTimezone, setClockTimezone] = useState('Europe/Paris')
  const [clockTimezones, setClockTimezones] = useState<string[]>([])
  const [clockLoading, setClockLoading] = useState(false)
  const [devdocsDocumentations, setDevdocsDocumentations] = useState<
    DevdocsDocumentation[]
  >([])
  const [devdocsLoading, setDevdocsLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [fallbackUrl, setFallbackUrl] = useState<string | null>(null)
  const [nextPageToken, setNextPageToken] = useState<string | null>(null)
  const [totalResults, setTotalResults] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [contacts, setContacts] = useState<GoogleContact[]>([])
  const [contactsLoading, setContactsLoading] = useState(false)
  const [contactsLoadingMore, setContactsLoadingMore] = useState(false)
  const [contactsNextPageToken, setContactsNextPageToken] = useState<string | null>(null)
  const [contactsTotalItems, setContactsTotalItems] = useState<number | null>(null)
  const [analysisQueue, setAnalysisQueue] = useState<AnalysisQueue>({ total: 0, analysed: 0, pending: 0 })
  const [analysisState, setAnalysisState] = useState<AnalysisState>({ status: 'idle', total: 0, completed: 0, failed: 0, remaining: 0 })
  const [analysisBusy, setAnalysisBusy] = useState(false)
  const [knowledgeBusy, setKnowledgeBusy] = useState(false)

  const current = useMemo(
    () => connectorWorkspaces.find((workspace) => workspace.id === active) ?? connectorWorkspaces[0],
    [active],
  )
  const workspaceOpen = connectorWorkspaces.some((workspace) => workspace.id === initialSource)
  const visibleConnectors = useMemo(() => {
    const normalizedQuery = catalogQuery.trim().toLocaleLowerCase('fr')
    return connectorDefinitions.filter(({ label, description, kind, status }) => {
      const matchesQuery = !normalizedQuery || `${label} ${description}`.toLocaleLowerCase('fr').includes(normalizedQuery)
      const matchesFilter = catalogFilter === 'all'
        || catalogFilter === kind
        || catalogFilter === status
      return matchesQuery && matchesFilter
    })
  }, [catalogFilter, catalogQuery])
  const analysisRunning = ['running', 'stopping'].includes(analysisState.status)
  const batchProgress = analysisState.total > 0 ? Math.round((analysisState.completed / analysisState.total) * 100) : 0
  const libraryProgress = analysisQueue.total > 0 ? Math.round((analysisQueue.analysed / analysisQueue.total) * 100) : 0

  useEffect(() => {
    if (initialSource && connectorWorkspaces.some((workspace) => workspace.id === initialSource)) {
      setActive(initialSource)
      setQuery('')
      setLastQuery('')
      setResults([])
      setMessage(null)
      setFallbackUrl(null)
      setNextPageToken(null)
      setTotalResults(null)
    }
  }, [initialSource])

  async function loadDevdocsDocumentations() {
  setDevdocsLoading(true)
  setMessage(null)

  try {
    const response = await fetch(
      `${API_BASE}/resources/devdocs/documentations`,
    )

    const payload = (await response.json()) as {
      detail?: string
      documentations?: DevdocsDocumentation[]
    }

    if (!response.ok) {
      throw new Error(
        payload.detail ?? 'Impossible de charger les documentations DevDocs',
      )
    }

    setDevdocsDocumentations(payload.documentations ?? [])
  } catch (error) {
    setDevdocsDocumentations([])
    setMessage(
      error instanceof Error
        ? error.message
        : 'Impossible de joindre DevDocs',
    )
  } finally {
    setDevdocsLoading(false)
  }
}

  async function refreshClock(timezone = clockTimezone) {
    setClockLoading(true)
    setMessage(null)

    try {
      const response = await fetch(
        `${API_BASE}/resources/clock/now?timezone=${encodeURIComponent(timezone)}`,
      )
      const payload = await response.json() as ClockSnapshot & { detail?: string }

      if (!response.ok) {
        throw new Error(payload.detail ?? 'Horloge indisponible')
      }

      setClockSnapshot(payload)
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Impossible de lire le référentiel temporel',
      )
    } finally {
      setClockLoading(false)
    }
  }

  async function loadClockTimezones() {
    try {
      const response = await fetch(
        `${API_BASE}/resources/clock/timezones?limit=500`,
      )
      const payload = await response.json() as {
        timezones?: string[]
      }

      if (response.ok) {
        setClockTimezones(payload.timezones ?? [])
      }
    } catch {
      setClockTimezones([])
    }
  }

  async function copyClockValue(value: string | number, label: string) {
    try {
      await navigator.clipboard.writeText(String(value))
      setMessage(`${label} copié`)
    } catch {
      setMessage(`Impossible de copier ${label.toLocaleLowerCase('fr')}`)
    }
  }

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
    if (active !== 'devdocs') return

  void loadDevdocsDocumentations()
  }, [active])

  useEffect(() => {
  if (active === 'contacts' && workspaceOpen) {
    void loadContacts()
  }
}, [active, workspaceOpen])

  useEffect(() => {
    if (active !== 'clock') return

    void refreshClock(clockTimezone)
    void loadClockTimezones()

    const timer = window.setInterval(
      () => void refreshClock(clockTimezone),
      30_000,
    )

    return () => window.clearInterval(timer)
  }, [active, clockTimezone])

  useEffect(() => {
    if (active !== 'chess') return
    void refreshChessStatus()
    const timer = window.setInterval(() => void refreshChessStatus(), analysisRunning ? 2000 : 8000)
    return () => window.clearInterval(timer)
  }, [active, analysisRunning])

  async function fetchSearch(
  source: 'youtube' | 'gallica' | 'imslp' | 'anki'| 'devdocs',
  normalized: string,
  pageToken?: string,
): Promise<SearchPayload> {

  if (source === 'anki') {
    const response = await fetch(`${API_BASE}/resources/anki/status`)
    return (await response.json()) as SearchPayload
  }

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

  async function loadContacts(
  pageToken: string | null = null,
  append = false,
) {
  if (append) {
    setContactsLoadingMore(true)
  } else {
    setContactsLoading(true)
    setContacts([])
    setMessage(null)
  }

  try {
    const params = new URLSearchParams({
      page_size: '50',
    })

    if (pageToken) {
      params.set('page_token', pageToken)
    }

    const response = await fetch(
      `${API_BASE}/resources/contacts?${params.toString()}`,
    )

    const payload = await response.json() as ContactsPayload

    if (!response.ok) {
      throw new Error(
        payload.detail
        ?? payload.message
        ?? 'Google Contacts indisponible',
      )
    }

    const loadedContacts = payload.contacts ?? []

    setContacts((currentContacts) => (
      append
        ? [...currentContacts, ...loadedContacts]
        : loadedContacts
    ))

    setContactsNextPageToken(payload.next_page_token ?? null)
    setContactsTotalItems(payload.total_items ?? null)
  } catch (error) {
    setMessage(
      error instanceof Error
        ? error.message
        : 'Impossible de charger Google Contacts',
    )
  } finally {
    setContactsLoading(false)
    setContactsLoadingMore(false)
  }
}

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const normalized = query.trim()
    if (!normalized || active === 'chess' || active === 'clock') return
    setMessage(null)
    setFallbackUrl(null)
    setResults([])
    setNextPageToken(null)
    setTotalResults(null)
    setLastQuery(normalized)
    try {
    if (active === 'contacts') {
    setContactsLoading(true)
    setContacts([])
    setContactsNextPageToken(null)

    const response = await fetch(
      `${API_BASE}/resources/contacts/search?q=${encodeURIComponent(normalized)}&limit=100`,
    )

    const payload = await response.json() as ContactsPayload

    if (!response.ok) {
      throw new Error(
        payload.detail
        ?? payload.message
        ?? 'Recherche Google Contacts indisponible',
      )
    }

    setContacts(payload.contacts ?? [])
    setContactsTotalItems(payload.count ?? 0)
    return
  }
    if (active === 'devdocs') {
    setLoading(true)

    const response = await fetch(
      `${API_BASE}/resources/devdocs/search?q=${encodeURIComponent(normalized)}`,
    )

    const payload = (await response.json()) as {
      detail?: string
      url?: string
    }

    if (!response.ok || !payload.url) {
      throw new Error(payload.detail ?? 'Recherche DevDocs indisponible')
    }

    window.open(payload.url, '_blank', 'noopener,noreferrer')
    setMessage(`Recherche « ${normalized} » ouverte dans DevDocs`)
    return
  }
      if (active === 'maps') {
        const response = await fetch(`${API_BASE}/resources/maps/directions?location=${encodeURIComponent(normalized)}`)
        const payload = await response.json()
        if (!response.ok || !payload.url) throw new Error(payload.detail ?? 'Google Maps indisponible')
        window.open(payload.url, '_blank', 'noopener,noreferrer')
        return
      }
      setLoading(true)
      if (active === 'anki') {
        const response = await fetch(`${API_BASE}/resources/anki/decks`)
        const payload = await response.json()

        if (!response.ok) {
          throw new Error(payload.detail ?? 'Anki indisponible')
        }

        setResults(
          (payload.decks ?? []).map((deck: string) => ({
            title: deck,
            description: 'Paquet Anki',
          })),
        )

        setMessage(
          payload.count
            ? `${payload.count} paquet(s) trouvé(s)`
            : 'Aucun paquet',
        )

        return
      }
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
      setContactsLoading(false)  
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

      <div className="connectors-catalog-heading">
        <div><h2>Catalogue des connecteurs</h2><p>Retrouve les services externes et programmes locaux, puis ouvre leur espace lorsqu’il existe.</p></div>
        <label className="connectors-catalog-search">
          <Search size={17} />
          <span className="sr-only">Rechercher un connecteur</span>
          <input value={catalogQuery} onChange={(event) => setCatalogQuery(event.target.value)} placeholder="Rechercher un connecteur…" />
        </label>
      </div>
      <div className="connectors-filters" aria-label="Filtrer les connecteurs">
        {([
          ['all', 'Tous'],
          ['external', 'Services externes'],
          ['local', 'Programmes locaux'],
          ['available', 'Disponibles'],
          ['partial', 'À consolider'],
        ] as const).map(([value, label]) => (
          <button key={value} type="button" className={catalogFilter === value ? 'is-active' : ''} onClick={() => setCatalogFilter(value)}>{label}</button>
        ))}
      </div>
      <section className="connectors-catalog" aria-label="Catalogue des connecteurs">
        {visibleConnectors.map(({ id, label, description, kind, status, route, icon: Icon }) => (
          <article key={id} className="connector-card">
            <span className="connector-card__icon"><Icon size={19} /></span>
            <div><b>{label}</b><p>{description}</p></div>
            <span className={`connector-card__status connector-card__status--${status}`}>{statusLabels[status]}</span>
            <small>{kind === 'local' ? 'Programme local' : 'Système externe'}</small>
            {route && <Link to={route}>Ouvrir l’espace <ExternalLink size={13} /></Link>}
          </article>
        ))}
        {visibleConnectors.length === 0 && <p className="connectors-catalog-empty">Aucun connecteur ne correspond à cette recherche.</p>}
      </section>

      {workspaceOpen && (
      <section className="resources-shell" aria-label={`Espace ${current.label}`}>
        <div className="resources-console">
          <div className="resources-console__heading">
            <span className="resources-console__icon"><ActiveIcon size={23} /></span>
            <div><p>{current.eyebrow}</p><h2>{current.label}</h2></div>
            <Link className="resources-console__close" to="/connectors">Retour au catalogue</Link>
          </div>

          {active !== 'chess' && active !== 'clock' && (
            <form className="resources-search" onSubmit={handleSubmit}>
              <Search size={19} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={current.placeholder} autoFocus />
              <button
                type="submit"
                disabled={loading || contactsLoading}
              >
                {loading || contactsLoading
                  ? 'Recherche…'
                  : active === 'maps'
                    ? 'Itinéraire'
                    : 'Rechercher'}
              </button>
            </form>
          )}

          {message && <div className="resources-message"><span>{message}</span>{fallbackUrl && <a href={fallbackUrl} target="_blank" rel="noreferrer">Ouvrir la recherche dans Gallica <ExternalLink size={14} /></a>}</div>}
          
          {active === 'devdocs' && (
  <section
    style={{
      display: 'grid',
      gap: 18,
      marginTop: 22,
    }}
  >
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 16,
        flexWrap: 'wrap',
        padding: 18,
        border: '1px solid var(--border, #d7d1c5)',
        borderRadius: 16,
      }}
    >
      <div>
        <p className="eyebrow">Documentation technique</p>
        <h3 style={{ margin: 0 }}>DevDocs connecté</h3>
        <p style={{ marginBottom: 0, opacity: 0.72 }}>
          Recherche rapide et accès au catalogue des documentations.
        </p>
      </div>

      <a
        href="https://devdocs.io/"
        target="_blank"
        rel="noreferrer"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        Ouvrir DevDocs
        <ExternalLink size={15} />
      </a>
    </div>

    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 12,
        flexWrap: 'wrap',
      }}
    >
      <div>
        <p className="eyebrow">Catalogue disponible</p>
        <h3 style={{ margin: 0 }}>
          {devdocsLoading
            ? 'Chargement…'
            : `${devdocsDocumentations.length} documentations`}
        </h3>
      </div>

      <button
        type="button"
        onClick={() => void loadDevdocsDocumentations()}
        disabled={devdocsLoading}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <RefreshCw
          size={15}
          className={devdocsLoading ? 'spin' : ''}
        />
        Actualiser
      </button>
    </div>

    {!devdocsLoading && devdocsDocumentations.length > 0 && (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 10,
          maxHeight: 420,
          overflowY: 'auto',
        }}
      >
        {devdocsDocumentations.map((documentation) => (
          <a
            key={documentation.slug}
            href={`https://devdocs.io/${documentation.slug}/`}
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 10,
              padding: 14,
              border: '1px solid var(--border, #d7d1c5)',
              borderRadius: 12,
              textDecoration: 'none',
            }}
          >
            <div>
              <b>{documentation.name}</b>

              {(documentation.version || documentation.release) && (
                <small
                  style={{
                    display: 'block',
                    marginTop: 4,
                    opacity: 0.7,
                  }}
                >
                  {documentation.version ?? documentation.release}
                </small>
              )}
            </div>

            <ExternalLink size={14} />
          </a>
        ))}
      </div>
    )}
  </section>
)}          

          {active === 'contacts' && (
  <section
    style={{
      display: 'grid',
      gap: 18,
      marginTop: 22,
    }}
  >
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 16,
        flexWrap: 'wrap',
        padding: 18,
        border: '1px solid var(--border, #d7d1c5)',
        borderRadius: 16,
      }}
    >
      <div>
        <p className="eyebrow">Google People API</p>

        <h3 style={{ margin: 0 }}>
          Google Contacts connecté
        </h3>

        <p
          style={{
            marginBottom: 0,
            opacity: 0.72,
          }}
        >
          {contactsTotalItems !== null
            ? `${contactsTotalItems} contacts dans le carnet Google`
            : 'Consultation du carnet d’adresses Google'}
        </p>
      </div>

      <button
        type="button"
        onClick={() => void loadContacts()}
        disabled={contactsLoading}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <RefreshCw
          size={15}
          className={contactsLoading ? 'spin' : ''}
        />

        Actualiser
      </button>
    </div>

    {contactsLoading && contacts.length === 0 && (
      <div className="resources-message">
        Chargement des contacts…
      </div>
    )}

    {!contactsLoading && contacts.length === 0 && !message && (
      <div className="resources-message">
        Aucun contact trouvé.
      </div>
    )}

    {contacts.length > 0 && (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: 12,
        }}
      >
        {contacts.map((contact) => (
          <article
            key={contact.resource_name}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 14,
              padding: 16,
              border: '1px solid var(--border, #d7d1c5)',
              borderRadius: 14,
              minWidth: 0,
            }}
          >
            {contact.photo_url ? (
              <img
                src={contact.photo_url}
                alt=""
                referrerPolicy="no-referrer"
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  objectFit: 'cover',
                  flexShrink: 0,
                }}
              />
            ) : (
              <div
                aria-hidden="true"
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  display: 'grid',
                  placeItems: 'center',
                  flexShrink: 0,
                  border: '1px solid var(--border, #d7d1c5)',
                  fontWeight: 700,
                }}
              >
                {contact.name.slice(0, 1).toUpperCase()}
              </div>
            )}

            <div
              style={{
                display: 'grid',
                gap: 7,
                minWidth: 0,
              }}
            >
              <strong>{contact.name}</strong>

              {contact.organizations.map((organization) => (
                <small
                  key={organization}
                  style={{ opacity: 0.72 }}
                >
                  {organization}
                </small>
              ))}

              {contact.emails.map((email) => (
                <a
                  key={email}
                  href={`mailto:${email}`}
                  style={{
                    overflowWrap: 'anywhere',
                  }}
                >
                  {email}
                </a>
              ))}

              {contact.phones.map((phone) => (
                <a
                  key={phone}
                  href={`tel:${phone.replace(/\s/g, '')}`}
                >
                  {phone}
                </a>
              ))}
            </div>
          </article>
        ))}
      </div>
    )}

    {contactsNextPageToken && (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <button
          type="button"
          disabled={contactsLoadingMore}
          onClick={() => void loadContacts(
            contactsNextPageToken,
            true,
          )}
        >
          {contactsLoadingMore
            ? 'Chargement…'
            : 'Charger davantage'}
        </button>
      </div>
    )}
  </section>
)}

          {active === 'clock' && (
            <section
              style={{
                display: 'grid',
                gap: 20,
                marginTop: 22,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: 16,
                  flexWrap: 'wrap',
                }}
              >
                <div>
                  <p className="eyebrow">Temps de référence</p>
                  <h3 style={{ margin: 0 }}>
                    {clockSnapshot?.time ?? '—'}
                  </h3>
                  <p style={{ marginBottom: 0, opacity: 0.72 }}>
                    {clockSnapshot?.date ?? 'Chargement…'}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => void refreshClock()}
                  disabled={clockLoading}
                  style={{
                    display: 'inline-flex',
                    gap: 8,
                    alignItems: 'center',
                  }}
                >
                  <RefreshCw
                    size={15}
                    className={clockLoading ? 'spin' : ''}
                  />
                  {clockLoading ? 'Actualisation…' : 'Actualiser'}
                </button>
              </div>

              <label
                style={{
                  display: 'grid',
                  gap: 8,
                  maxWidth: 440,
                }}
              >
                <span>Fuseau horaire actif</span>
                <select
                  value={clockTimezone}
                  onChange={(event) => setClockTimezone(event.target.value)}
                  style={{
                    width: '100%',
                    padding: '11px 13px',
                    borderRadius: 10,
                  }}
                >
                  {!clockTimezones.includes(clockTimezone) && (
                    <option value={clockTimezone}>{clockTimezone}</option>
                  )}
                  {clockTimezones.map((timezone) => (
                    <option key={timezone} value={timezone}>
                      {timezone}
                    </option>
                  ))}
                </select>
              </label>

              {clockSnapshot && (
                <>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns:
                        'repeat(auto-fit, minmax(180px, 1fr))',
                      gap: 12,
                    }}
                  >
                    <article>
                      <small>Heure locale</small>
                      <strong
                        style={{
                          display: 'block',
                          marginTop: 7,
                          fontSize: 24,
                        }}
                      >
                        {clockSnapshot.time}
                      </strong>
                    </article>

                    <article>
                      <small>Date locale</small>
                      <strong
                        style={{
                          display: 'block',
                          marginTop: 7,
                          fontSize: 19,
                        }}
                      >
                        {clockSnapshot.date}
                      </strong>
                    </article>

                    <article>
                      <small>Fuseau</small>
                      <strong
                        style={{
                          display: 'block',
                          marginTop: 7,
                          fontSize: 17,
                        }}
                      >
                        {clockSnapshot.timezone}
                      </strong>
                    </article>

                    <article>
                      <small>Semaine ISO</small>
                      <strong
                        style={{
                          display: 'block',
                          marginTop: 7,
                          fontSize: 24,
                        }}
                      >
                        {clockSnapshot.iso_week}
                      </strong>
                    </article>

                    <article>
                      <small>Jour ISO</small>
                      <strong
                        style={{
                          display: 'block',
                          marginTop: 7,
                          fontSize: 24,
                        }}
                      >
                        {clockSnapshot.weekday}
                      </strong>
                    </article>

                    <article>
                      <small>Période</small>
                      <strong
                        style={{
                          display: 'block',
                          marginTop: 7,
                          fontSize: 19,
                        }}
                      >
                        {{
                          night: 'Nuit',
                          morning: 'Matin',
                          afternoon: 'Après-midi',
                          evening: 'Soirée',
                        }[clockSnapshot.period]}
                      </strong>
                    </article>
                  </div>

                  <div
                    style={{
                      display: 'grid',
                      gap: 12,
                      padding: 18,
                      border:
                        '1px solid var(--border, #d7d1c5)',
                      borderRadius: 16,
                    }}
                  >
                    <div>
                      <small>Date et heure ISO 8601</small>
                      <code
                        style={{
                          display: 'block',
                          marginTop: 7,
                          overflowWrap: 'anywhere',
                        }}
                      >
                        {clockSnapshot.local_datetime}
                      </code>
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        void copyClockValue(
                          clockSnapshot.local_datetime,
                          'Date ISO 8601',
                        )
                      }
                    >
                      Copier ISO 8601
                    </button>

                    <div>
                      <small>UTC</small>
                      <code
                        style={{
                          display: 'block',
                          marginTop: 7,
                          overflowWrap: 'anywhere',
                        }}
                      >
                        {clockSnapshot.utc_datetime}
                      </code>
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        void copyClockValue(
                          clockSnapshot.utc_datetime,
                          'Date UTC',
                        )
                      }
                    >
                      Copier UTC
                    </button>

                    <div>
                      <small>Timestamp Unix</small>
                      <code
                        style={{
                          display: 'block',
                          marginTop: 7,
                        }}
                      >
                        {clockSnapshot.unix_timestamp}
                      </code>
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        void copyClockValue(
                          clockSnapshot.unix_timestamp,
                          'Timestamp Unix',
                        )
                      }
                    >
                      Copier le timestamp
                    </button>
                  </div>

                  <div
                    style={{
                      padding: 18,
                      border:
                        '1px solid var(--border, #d7d1c5)',
                      borderRadius: 16,
                    }}
                  >
                    <p className="eyebrow">Suivi temporel Hanuman</p>
                    <h3 style={{ marginTop: 0 }}>
                      Référentiel transversal
                    </h3>
                    <p style={{ marginBottom: 0, opacity: 0.75 }}>
                      Cette horloge servira à horodater les connecteurs,
                      les exécutions de flux, les routines et les événements
                      du Journal de Vie.
                    </p>
                  </div>
                </>
              )}
            </section>
          )}

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

          {active !== 'chess' &&
            active !== 'clock' &&
            active !== 'devdocs' &&
            active !== 'contacts' &&
            !message &&
            !loading &&
            results.length === 0 && (
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
      )}
    </div>
  )
}
