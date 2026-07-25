import {
  Activity,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Clock3,
  Download,
  Filter,
  Gauge,
  ListChecks,
  Pause,
  Play,
  RefreshCw,
  Search,
  ServerCog,
  TerminalSquare,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { CSSProperties } from 'react'

type ServiceState = 'healthy' | 'degraded' | 'down'
type Period = '1h' | '24h' | '7d' | '30d'
type Metric = 'score' | 'latency' | 'errors'

type ServiceCheck = {
  id: string
  label: string
  endpoint: string
  state: ServiceState
  latency: number | null
  checkedAt: string
  message: string
}

type HistoryPoint = {
  timestamp: string
  score: number
  latency: number
  errors: number
}

type LogEntry = {
  timestamp: string
  level: 'INFO' | 'WARN' | 'ERROR'
  source: string
  message: string
}

type FollowUp = {
  id: string
  priority: 'Haute' | 'Moyenne' | 'Basse'
  subject: string
  state: 'À faire' | 'En cours' | 'Terminé'
  next: string
}

const API = 'http://127.0.0.1:8000'

const definitions = [
  { id: 'backend', label: 'Backend FastAPI', endpoint: '/status' },
  { id: 'calendar', label: 'Google Calendar', endpoint: '/calendar/status' },
  { id: 'gmail', label: 'Gmail', endpoint: '/gmail/status' },
  { id: 'github', label: 'GitHub', endpoint: '/github/ping' },
  { id: 'notion', label: 'Notion', endpoint: '/notion/ping' },
  { id: 'obsidian', label: 'Obsidian', endpoint: '/obsidian/ping' },
  { id: 'openai', label: 'OpenAI', endpoint: '/openai/ping' },
  { id: 'wikipedia', label: 'Wikipédia', endpoint: '/wikipedia/ping' },
  { id: 'chess', label: 'Chess.com', endpoint: '/chess/ping' },
]

const initialFollowUp: FollowUp[] = [
  { id: 'calendar-refresh', priority: 'Haute', subject: 'Refresh token Calendar', state: 'À faire', next: 'Automatiser le renouvellement OAuth' },
  { id: 'gmail-oauth', priority: 'Haute', subject: 'Connexion Gmail', state: 'En cours', next: 'Valider la lecture réelle de la boîte' },
  { id: 'coverage', priority: 'Moyenne', subject: 'Couverture des tests', state: 'À faire', next: 'Passer de 86 % à 90 %' },
  { id: 'health-storage', priority: 'Basse', subject: 'Historique persistant', state: 'À faire', next: 'Déplacer localStorage vers le backend' },
]

const periodDuration: Record<Period, number> = {
  '1h': 60 * 60 * 1000,
  '24h': 24 * 60 * 60 * 1000,
  '7d': 7 * 24 * 60 * 60 * 1000,
  '30d': 30 * 24 * 60 * 60 * 1000,
}

function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) as T : fallback
  } catch {
    return fallback
  }
}

function stateLabel(state: ServiceState) {
  if (state === 'healthy') return 'Opérationnel'
  if (state === 'degraded') return 'Dégradé'
  return 'Indisponible'
}

function metricLabel(metric: Metric) {
  if (metric === 'score') return 'Score global'
  if (metric === 'latency') return 'Latence moyenne'
  return 'Anomalies détectées'
}

function metricUnit(metric: Metric) {
  if (metric === 'score') return '/100'
  if (metric === 'latency') return 'ms'
  return 'alertes'
}

function HealthChart({ history, metric, period }: { history: HistoryPoint[]; metric: Metric; period: Period }) {
  const cutoff = Date.now() - periodDuration[period]
  const filtered = history.filter((point) => new Date(point.timestamp).getTime() >= cutoff).slice(-48)
  const source = filtered.length ? filtered : history.slice(-12)
  const values = source.map((point) => point[metric])

  if (!values.length) {
    return <div className="health-empty">Le premier contrôle alimentera ce graphe.</div>
  }

  const max = metric === 'score' ? 100 : Math.max(...values, 1)
  const min = metric === 'score' || metric === 'errors' ? 0 : Math.min(...values)
  const span = Math.max(1, max - min)
  const coordinates = values.map((value, index) => {
    const x = values.length === 1 ? 50 : 4 + (index / (values.length - 1)) * 92
    const y = 88 - ((value - min) / span) * 72
    return { x, y, value }
  })
  const points = coordinates.map(({ x, y }) => `${x},${y}`).join(' ')
  const latest = values.at(-1) ?? 0

  return (
    <div className="health-chart-wrap">
      <div className="health-chart-value"><strong>{latest}</strong><span>{metricUnit(metric)}</span></div>
      <svg className={`health-chart health-chart--${metric}`} viewBox="0 0 100 100" preserveAspectRatio="none" aria-label={metricLabel(metric)}>
        <line x1="4" y1="88" x2="96" y2="88" />
        <line x1="4" y1="52" x2="96" y2="52" />
        <line x1="4" y1="16" x2="96" y2="16" />
        <polygon points={`4,88 ${points} 96,88`} />
        <polyline points={points} />
        {coordinates.map(({ x, y, value }, index) => <circle key={`${x}-${index}`} cx={x} cy={y} r="1.25"><title>{value} {metricUnit(metric)}</title></circle>)}
      </svg>
      <div className="health-chart-axis"><span>{source[0] ? new Date(source[0].timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '—'}</span><span>Maintenant</span></div>
    </div>
  )
}

export default function HealthPage() {
  const [checks, setChecks] = useState<ServiceCheck[]>([])
  const [history, setHistory] = useState<HistoryPoint[]>(() => readStored('hanuman-health-history', []))
  const [logs, setLogs] = useState<LogEntry[]>(() => readStored('hanuman-health-logs', []))
  const [followUp, setFollowUp] = useState<FollowUp[]>(() => readStored('hanuman-health-follow-up', initialFollowUp))
  const [period, setPeriod] = useState<Period>('24h')
  const [serviceFilter, setServiceFilter] = useState('all')
  const [logLevel, setLogLevel] = useState('all')
  const [logSearch, setLogSearch] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [liveLogs, setLiveLogs] = useState(true)

  async function runChecks() {
    setLoading(true)
    const nextLogs: LogEntry[] = []
    const results = await Promise.all(definitions.map(async (definition): Promise<ServiceCheck> => {
      const started = performance.now()
      try {
        const response = await fetch(`${API}${definition.endpoint}`)
        const latency = Math.round(performance.now() - started)
        const payload = await response.json().catch(() => ({})) as { ok?: boolean; error?: string }
        const state: ServiceState = response.ok && payload.ok !== false ? 'healthy' : response.status < 500 ? 'degraded' : 'down'
        const message = payload.error || (state === 'healthy' ? 'Contrôle réussi' : `Réponse HTTP ${response.status}`)
        nextLogs.push({ timestamp: new Date().toISOString(), level: state === 'healthy' ? 'INFO' : 'WARN', source: definition.id, message: `${message} · ${latency} ms` })
        return { ...definition, state, latency, checkedAt: new Date().toISOString(), message }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Erreur réseau'
        nextLogs.push({ timestamp: new Date().toISOString(), level: 'ERROR', source: definition.id, message })
        return { ...definition, state: 'down', latency: null, checkedAt: new Date().toISOString(), message }
      }
    }))

    const healthyCount = results.filter((item) => item.state === 'healthy').length
    const scoreValue = Math.round((healthyCount / results.length) * 100)
    const latencies = results.flatMap((item) => item.latency === null ? [] : [item.latency])
    const latencyValue = latencies.length ? Math.round(latencies.reduce((sum, value) => sum + value, 0) / latencies.length) : 0
    const point = { timestamp: new Date().toISOString(), score: scoreValue, latency: latencyValue, errors: results.length - healthyCount }
    const nextHistory = [...history, point].slice(-720)
    const mergedLogs = [...nextLogs.reverse(), ...logs].slice(0, 500)

    setChecks(results)
    setHistory(nextHistory)
    setLogs(mergedLogs)
    localStorage.setItem('hanuman-health-history', JSON.stringify(nextHistory))
    localStorage.setItem('hanuman-health-logs', JSON.stringify(mergedLogs))
    setLoading(false)
  }

  useEffect(() => { void runChecks() }, [])
  useEffect(() => {
    if (!liveLogs) return
    const timer = window.setInterval(() => { void runChecks() }, 60000)
    return () => window.clearInterval(timer)
  }, [liveLogs, history, logs])

  const visibleChecks = useMemo(
    () => serviceFilter === 'all' ? checks : checks.filter((check) => check.id === serviceFilter),
    [checks, serviceFilter],
  )
  const visibleLogs = useMemo(
    () => logs.filter((entry) => (logLevel === 'all' || entry.level === logLevel) && `${entry.source} ${entry.message}`.toLowerCase().includes(logSearch.toLowerCase())),
    [logs, logLevel, logSearch],
  )

  const healthy = checks.filter((item) => item.state === 'healthy').length
  const warnings = checks.filter((item) => item.state === 'degraded').length
  const down = checks.filter((item) => item.state === 'down').length
  const score = checks.length ? Math.round((healthy / checks.length) * 100) : 0
  const latencyValues = checks.flatMap((item) => item.latency === null ? [] : [item.latency])
  const averageLatency = Math.round(latencyValues.reduce((sum, value) => sum + value, 0) / Math.max(1, latencyValues.length))
  const globalState = down ? 'Dégradé' : warnings ? 'À surveiller' : 'Opérationnel'
  const completedTasks = followUp.filter((item) => item.state === 'Terminé').length

  function updateFollowUp(id: string, state: FollowUp['state']) {
    const next = followUp.map((item) => item.id === id ? { ...item, state } : item)
    setFollowUp(next)
    localStorage.setItem('hanuman-health-follow-up', JSON.stringify(next))
  }

  function exportLogs() {
    const blob = new Blob([visibleLogs.map((entry) => `[${entry.timestamp}] ${entry.level} ${entry.source} ${entry.message}`).join('\n')], { type: 'text/plain' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `hanuman-logs-${new Date().toISOString().slice(0, 10)}.txt`
    link.click()
    URL.revokeObjectURL(link.href)
  }

  return (
    <div className="health-page">
      <header className="health-hero">
        <div>
          <p className="eyebrow">Hanuman / Santé du système</p>
          <h1>Le centre d’observation.</h1>
          <p>État des connecteurs, performance, activité récente, journaux techniques et trajectoire de maintenance.</p>
        </div>
        <button className="health-refresh" onClick={() => void runChecks()} disabled={loading}><RefreshCw size={17} className={loading ? 'spin' : ''} /> Contrôler maintenant</button>
      </header>

      <section className="health-summary">
        <article className="health-score">
          <div className="health-score__ring" style={{ '--score': `${score * 3.6}deg` } as CSSProperties}><span>{score}</span><small>/100</small></div>
          <div><span className={`health-pill health-pill--${down ? 'down' : warnings ? 'degraded' : 'healthy'}`}>{globalState}</span><h2>Hanuman {globalState.toLowerCase()}</h2><p>{healthy} services opérationnels, {warnings} avertissement{warnings > 1 ? 's' : ''}, {down} panne{down > 1 ? 's' : ''}.</p></div>
        </article>
        <article><ServerCog size={20} /><strong>{healthy}/{checks.length || definitions.length}</strong><span>Connecteurs actifs</span></article>
        <article><Gauge size={20} /><strong>{averageLatency} ms</strong><span>Latence moyenne</span></article>
        <article><AlertTriangle size={20} /><strong>{warnings + down}</strong><span>Anomalies actuelles</span></article>
        <article><Clock3 size={20} /><strong>{checks[0] ? new Date(checks[0].checkedAt).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '—'}</strong><span>Dernier contrôle</span></article>
      </section>

      <section className="health-panel health-analytics">
        <div className="health-panel__heading">
          <div><span>Historique</span><h2>Santé et performance</h2></div>
          <div className="health-segmented">{(['1h', '24h', '7d', '30d'] as Period[]).map((item) => <button key={item} className={period === item ? 'active' : ''} onClick={() => setPeriod(item)}>{item}</button>)}</div>
        </div>
        <div className="health-chart-grid">
          {(['score', 'latency', 'errors'] as Metric[]).map((metric) => <article key={metric}><div><b>{metricLabel(metric)}</b><span>Fenêtre {period}</span></div><HealthChart history={history} metric={metric} period={period} /></article>)}
          <article className="health-distribution">
            <div><b>Répartition actuelle</b><span>{checks.length || definitions.length} services</span></div>
            <div className="health-distribution__content">
              <div className="health-distribution__ring" style={{ '--healthy': `${checks.length ? (healthy / checks.length) * 360 : 0}deg`, '--warning': `${checks.length ? ((healthy + warnings) / checks.length) * 360 : 0}deg` } as CSSProperties}><span>{healthy}</span><small>actifs</small></div>
              <div className="health-distribution__legend"><span><i className="health-dot health-dot--healthy" />Opérationnels <b>{healthy}</b></span><span><i className="health-dot health-dot--degraded" />Dégradés <b>{warnings}</b></span><span><i className="health-dot health-dot--down" />Indisponibles <b>{down}</b></span></div>
            </div>
          </article>
        </div>
      </section>

      <section className="health-panel">
        <div className="health-panel__heading"><div><span>Infrastructure</span><h2>Connecteurs et services</h2></div><label className="health-select"><Filter size={14} /><select value={serviceFilter} onChange={(event) => setServiceFilter(event.target.value)}><option value="all">Tous les services</option>{definitions.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label></div>
        <div className="health-service-table">
          <div className="health-service-row health-service-row--head"><span>Service</span><span>État</span><span>Latence</span><span>Dernier contrôle</span><span /></div>
          {visibleChecks.map((check) => <div key={check.id} className="health-service-wrap"><button className="health-service-row" onClick={() => setExpanded(expanded === check.id ? null : check.id)}><span><i className={`health-dot health-dot--${check.state}`} />{check.label}</span><span>{stateLabel(check.state)}</span><span>{check.latency === null ? '—' : `${check.latency} ms`}</span><span>{new Date(check.checkedAt).toLocaleTimeString('fr-FR')}</span><span>{expanded === check.id ? <ChevronUp size={15} /> : <ChevronDown size={15} />}</span></button>{expanded === check.id && <div className="health-service-detail"><code>GET {check.endpoint}</code><p>{check.message}</p><button onClick={() => void runChecks()}><RefreshCw size={14} /> Retester</button></div>}</div>)}
        </div>
      </section>

      <section className="health-two-columns">
        <article className="health-panel"><div className="health-panel__heading"><div><span>Activité</span><h2>Historique récent</h2></div><Activity size={19} /></div><div className="health-timeline">{logs.slice(0, 8).map((entry, index) => <div key={`${entry.timestamp}-${index}`}><i className={`health-dot health-dot--${entry.level === 'INFO' ? 'healthy' : entry.level === 'WARN' ? 'degraded' : 'down'}`} /><time>{new Date(entry.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</time><p><b>{entry.source}</b>{entry.message}</p></div>)}</div></article>
        <article className="health-panel"><div className="health-panel__heading"><div><span>Plan d’action</span><h2>Suivi de la suite</h2></div><span className="health-progress-label">{completedTasks}/{followUp.length} terminés</span></div><div className="health-follow-up">{followUp.map((item) => <div key={item.id}><span className={`health-priority health-priority--${item.priority.toLowerCase()}`}>{item.priority}</span><p><b>{item.subject}</b><small>{item.next}</small></p><select value={item.state} onChange={(event) => updateFollowUp(item.id, event.target.value as FollowUp['state'])}><option>À faire</option><option>En cours</option><option>Terminé</option></select></div>)}</div></article>
      </section>

      <section className="health-panel health-logs">
        <div className="health-panel__heading"><div><span>Observabilité</span><h2>Explorateur de logs</h2></div><div className="health-log-actions"><button onClick={() => setLiveLogs(!liveLogs)}>{liveLogs ? <Pause size={14} /> : <Play size={14} />}{liveLogs ? 'Pause' : 'Reprendre'}</button><button onClick={exportLogs}><Download size={14} /> Exporter</button></div></div>
        <div className="health-log-filters"><label><Search size={14} /><input value={logSearch} onChange={(event) => setLogSearch(event.target.value)} placeholder="Rechercher dans les logs" /></label><select value={logLevel} onChange={(event) => setLogLevel(event.target.value)}><option value="all">Tous les niveaux</option><option>INFO</option><option>WARN</option><option>ERROR</option></select></div>
        <div className="health-console">{visibleLogs.slice(0, 100).map((entry, index) => <div key={`${entry.timestamp}-${index}`}><time>{new Date(entry.timestamp).toLocaleString('fr-FR')}</time><span className={`health-level health-level--${entry.level.toLowerCase()}`}>{entry.level}</span><b>{entry.source}</b><code>{entry.message}</code></div>)}{!visibleLogs.length && <p>Aucun journal ne correspond aux filtres.</p>}</div>
        <div className="health-console__footer"><TerminalSquare size={14} /> {visibleLogs.length} entrées · actualisation automatique {liveLogs ? 'active' : 'en pause'}</div>
      </section>
    </div>
  )
}
