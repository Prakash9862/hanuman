import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  GitBranch,
  LoaderCircle,
  Play,
  RefreshCw,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

type Counts = { created: number; updated: number; unchanged: number }
type Run = {
  run_id: string
  trigger: string
  status: 'succeeded' | 'failed' | 'skipped'
  result: { status: string; summary: string; verification_details: string[] }
  started_at: string
  finished_at: string
  duration_ms: number
  verification: 'passed' | 'failed' | 'not_applied'
  repository: Counts
  development_sessions: Counts
  commits: { added: number; already_present: number; ignored: number }
  failures: Array<{ code: string; category: string; message: string }>
  warnings: string[]
  fingerprint?: string | null
  idempotency_key?: string | null
}
type FlowInfo = {
  name: string
  description: string
  backend_state: string
  configuration: {
    repository: string; branch: string; max_commits: number
    session_window_hours: number; session_max_duration_hours: number
    notion_destination: string
  }
  automation: {
    workflow_installed: boolean; trigger: string; required_secrets: string[]
    secrets_status: string; actions_url: string
  }
}

async function payload<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({})) as T & { detail?: string }
  if (!response.ok) {
    const run = data as T & Partial<Run>
    throw Object.assign(new Error(data.detail || run.result?.summary || `Erreur HTTP ${response.status}`), { run })
  }
  return data
}

function formatDate(value?: string) {
  return value
    ? new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
    : 'Aucune'
}

function ResultCounts({ title, counts }: { title: string; counts: Counts }) {
  return <article className="memory-counts"><h3>{title}</h3><div>
    <span><b>{counts.created}</b> créé{counts.created > 1 ? 's' : ''}</span>
    <span><b>{counts.updated}</b> mis à jour</span>
    <span><b>{counts.unchanged}</b> inchangé{counts.unchanged > 1 ? 's' : ''}</span>
  </div></article>
}

function RunResult({ run }: { run: Run }) {
  return <section className={`memory-result memory-result--${run.status}`} aria-live="polite">
    <header>{run.status === 'succeeded' ? <CheckCircle2 /> : <AlertTriangle />}
      <div><h2>{run.status === 'succeeded' ? 'Synchronisation réussie' : 'Synchronisation échouée'}</h2><p>{run.result.summary}</p></div>
    </header>
    <div className="memory-result-grid">
      <ResultCounts title="Repository" counts={run.repository} />
      <ResultCounts title="Development Sessions" counts={run.development_sessions} />
      <article className="memory-counts"><h3>Commits</h3><div>
        <span><b>{run.commits.added}</b> ajoutés</span><span><b>{run.commits.already_present}</b> déjà présents</span><span><b>{run.commits.ignored}</b> ignorés</span>
      </div></article>
    </div>
    <div className="memory-verification"><b>Vérification</b><span>{run.verification === 'passed' ? 'Réussie' : run.verification === 'failed' ? 'Échouée' : 'Non appliquée'}</span></div>
    {run.failures.map((failure) => <div className="memory-error" key={`${failure.code}-${failure.message}`}><b>{failure.code}</b><span>{failure.message}</span></div>)}
    {run.warnings.length > 0 && <details><summary>{run.warnings.length} avertissement(s)</summary>{run.warnings.map((warning) => <p key={warning}>{warning}</p>)}</details>}
    <details><summary>Détails techniques du Run</summary><dl>
      <dt>Run ID</dt><dd>{run.run_id}</dd><dt>Empreinte</dt><dd>{run.fingerprint || '—'}</dd><dt>Clé d’idempotence</dt><dd>{run.idempotency_key || '—'}</dd>
    </dl></details>
  </section>
}

export default function GitHubProjectMemoryPage() {
  const navigate = useNavigate()
  const [info, setInfo] = useState<FlowInfo | null>(null)
  const [runs, setRuns] = useState<Run[]>([])
  const [selected, setSelected] = useState<Run | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const [flowResponse, runsResponse] = await Promise.all([
        fetch('/api/flows/github-project-memory'),
        fetch('/api/flows/github-project-memory/runs'),
      ])
      const [flow, history] = await Promise.all([
        payload<FlowInfo>(flowResponse),
        payload<{ runs: Run[] }>(runsResponse),
      ])
      setInfo(flow); setRuns(history.runs)
      setSelected((current) => current ?? history.runs[0] ?? null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'API Hanuman inaccessible.')
    } finally { setLoading(false) }
  }, [])

  const runNow = async () => {
    if (running) return
    setRunning(true); setError(null)
    try {
      const response = await fetch('/api/flows/github-project-memory/runs', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
      })
      const run = await payload<Run>(response)
      setSelected(run); setRuns((current) => [run, ...current.filter((item) => item.run_id !== run.run_id)])
    } catch (caught) {
      const failedRun = (caught as { run?: Partial<Run> }).run
      if (failedRun?.run_id) setSelected(failedRun as Run)
      setError(caught instanceof Error ? caught.message : 'Échec inattendu du Flow.')
      await load()
    } finally { setRunning(false) }
  }

  useEffect(() => { void load() }, [load])
  const lastSuccess = runs.find((run) => run.status === 'succeeded')

  return <div className="page memory-page">
    <header className="memory-header"><div>
      <button className="breadcrumb-button" onClick={() => navigate('/flows')}>← Flux</button>
      <p className="eyebrow">Hanuman / Flux / GitHub → Notion</p>
      <h1>GitHub Activity → Notion Project Memory</h1>
      <p>{info?.description || 'Activité GitHub transformée en mémoire projet Notion.'}</p>
      <div className="memory-badges"><span>GitHub</span><b>→</b><span>Notion</span><i>{info?.backend_state === 'available' ? 'Disponible' : 'État inconnu'}</i></div>
    </div><div className="memory-actions">
      <button className="refresh-button" onClick={() => void load()} disabled={loading || running}><RefreshCw className={loading ? 'spin' : ''} size={17} /> Actualiser</button>
      <button className="primary-button" onClick={() => void runNow()} disabled={running || !info}><span>{running ? <LoaderCircle className="spin" size={17} /> : <Play size={17} />}</span>{running ? 'Synchronisation…' : 'Lancer maintenant'}</button>
    </div></header>

    {error && <div className="memory-error memory-error--page" role="alert"><AlertTriangle /><div><b>Le Flow n’a pas abouti.</b><span>{error}</span></div></div>}
    {selected && <RunResult run={selected} />}

    <div className="memory-layout">
      <section className="memory-panel"><h2>Configuration</h2>{info ? <dl>
        <dt>Repository</dt><dd>{info.configuration.repository}</dd><dt>Branche</dt><dd>{info.configuration.branch}</dd>
        <dt>Commits maximum</dt><dd>{info.configuration.max_commits}</dd><dt>Fenêtre d’inactivité</dt><dd>{info.configuration.session_window_hours} h</dd>
        <dt>Durée maximale d’une session</dt><dd>{info.configuration.session_max_duration_hours} h</dd><dt>Destination Notion</dt><dd>{info.configuration.notion_destination}</dd>
        <dt>Déclenchements</dt><dd>Manuel{info.automation.workflow_installed ? ' · GitHub Actions' : ''}</dd>
      </dl> : <p>Chargement de la configuration…</p>}</section>
      <section className="memory-panel"><h2>Automatisation</h2>{info && <>
        <p className={info.automation.workflow_installed ? 'memory-state memory-state--ok' : 'memory-state'}>{info.automation.workflow_installed ? 'Workflow installé' : 'Automatisation non configurée'}</p>
        <dl><dt>Déclencheur</dt><dd>{info.automation.trigger}</dd><dt>Secrets requis</dt><dd>{info.automation.required_secrets.join(', ')}</dd><dt>Secrets GitHub</dt><dd>État inconnu — leurs valeurs ne sont pas lisibles</dd><dt>Dernière exécution Hanuman connue</dt><dd>{formatDate(runs[0]?.started_at)}</dd></dl>
        <a className="memory-link" href={info.automation.actions_url} target="_blank" rel="noreferrer">Ouvrir GitHub Actions <ExternalLink size={15} /></a>
      </>}</section>
    </div>

    <section className="memory-panel memory-runs"><div className="memory-panel-heading"><div><h2>Dernières exécutions</h2><p>Dernière tentative : {formatDate(runs[0]?.started_at)} · Dernier succès : {formatDate(lastSuccess?.finished_at)}</p></div><GitBranch /></div>
      {!loading && runs.length === 0 && <p className="memory-empty">Aucun Run enregistré par ce backend.</p>}
      <div className="memory-run-list">{runs.map((run) => <button key={run.run_id} onClick={() => setSelected(run)} className={selected?.run_id === run.run_id ? 'is-selected' : ''}>
        <span><i className={`run-dot run-dot--${run.status}`} /><b>{formatDate(run.started_at)}</b><small>{run.trigger}</small></span>
        <span><b>{run.status === 'succeeded' ? 'Réussi' : run.status === 'failed' ? 'Échoué' : 'Inchangé'}</b><small>{Math.round(run.duration_ms)} ms · vérification {run.verification}</small></span>
      </button>)}</div>
    </section>
  </div>
}
