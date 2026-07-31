import {
  Bot,
  Cable,
  CircleHelp,
  Eye,
  GitBranch,
  LoaderCircle,
  NotebookTabs,
  RefreshCw,
  Settings2,
  Stethoscope,
  TriangleAlert,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Navigate, NavLink, useParams } from 'react-router-dom'

const API = 'http://127.0.0.1:8000'

type SettingsSectionId =
  | 'general'
  | 'connectors'
  | 'flows'
  | 'journal'
  | 'appearance'
  | 'ai'
  | 'diagnostic'
  | 'about'

type SettingsSectionDefinition = {
  id: SettingsSectionId
  label: string
  icon: typeof Settings2
}

type GeneralSettings = {
  environment?: string
  debug?: boolean
  log_level?: string
  directories?: Record<string, string>
}

type ConnectorSettings = {
  id: string
  label: string
  configured: boolean
  status?: string
  capabilities?: string[]
}

type FlowSettings = {
  id: string
  label: string
  enabled?: boolean
  status?: string
  last_run_at?: string | null
  last_error?: string | null
}

type JournalSettings = {
  registered: boolean
  status?: string
  routines_count: number
  last_analysis_at?: string | null
}

type AppearanceSettings = {
  theme?: string
  language?: string
  animations?: boolean
}

type AISettings = {
  provider?: string
  model?: string
  configured?: boolean
}

type DiagnosticItem = {
  id: string
  label: string
  kind: string
  status: string
  latency_ms?: number | null
  message?: string | null
  checked_at?: string | null
}

type AboutSettings = {
  name?: string
  version?: string
  environment?: string
  build?: string
  license?: string
}

type HanumanSettings = {
  general: GeneralSettings
  connectors: ConnectorSettings[]
  flows: FlowSettings[]
  journal: JournalSettings
  appearance: AppearanceSettings
  ai: AISettings
  diagnostic: DiagnosticItem[]
  about: AboutSettings
}

const sections: SettingsSectionDefinition[] = [
  { id: 'general', label: 'Général', icon: Settings2 },
  { id: 'connectors', label: 'Connecteurs', icon: Cable },
  { id: 'flows', label: 'Flux', icon: GitBranch },
  { id: 'journal', label: 'Journal de Vie', icon: NotebookTabs },
  { id: 'appearance', label: 'Apparence', icon: Eye },
  { id: 'ai', label: 'IA', icon: Bot },
  { id: 'diagnostic', label: 'Diagnostic', icon: Stethoscope },
  { id: 'about', label: 'À propos', icon: CircleHelp },
]

function EmptyState({ message }: { message: string }) {
  return (
    <div className="settings-empty">
      <p>{message}</p>
    </div>
  )
}

function GeneralSection({ data }: { data: GeneralSettings }) {
  const directories = Object.entries(data.directories ?? {})

  return (
    <section className="settings-section">
      <header>
        <p className="eyebrow">Paramètres</p>
        <h2>Général</h2>
        <p>Configuration globale réellement exposée par Hanuman.</p>
      </header>

      <dl className="settings-facts">
        <div>
          <dt>Environnement</dt>
          <dd>{data.environment ?? 'Non renseigné'}</dd>
        </div>

        <div>
          <dt>Mode debug</dt>
          <dd>
            {data.debug === undefined
              ? 'Non renseigné'
              : data.debug
                ? 'Activé'
                : 'Désactivé'}
          </dd>
        </div>

        <div>
          <dt>Niveau de logs</dt>
          <dd>{data.log_level ?? 'Non renseigné'}</dd>
        </div>
      </dl>

      <h3>Répertoires</h3>

      {directories.length ? (
        <dl className="settings-facts">
          {directories.map(([name, path]) => (
            <div key={name}>
              <dt>{name}</dt>
              <dd>{path}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <EmptyState message="Aucun répertoire n’est exposé par le backend." />
      )}
    </section>
  )
}

function ConnectorsSection({ data }: { data: ConnectorSettings[] }) {
  return (
    <section className="settings-section">
      <header>
        <p className="eyebrow">Paramètres</p>
        <h2>Connecteurs</h2>
        <p>Connecteurs enregistrés dans Hanuman.</p>
      </header>

      {data.length ? (
        <div className="settings-list">
          {data.map((connector) => (
            <article key={connector.id} className="settings-list__item">
              <div>
                <strong>{connector.label}</strong>
                <span>{connector.id}</span>
              </div>

              <div>
                <span>
                  {connector.configured ? 'Configuré' : 'Non configuré'}
                </span>
                <span>{connector.status ?? 'État inconnu'}</span>
              </div>

              {connector.capabilities?.length ? (
                <small>{connector.capabilities.join(' · ')}</small>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <EmptyState message="Aucun connecteur n’est enregistré." />
      )}
    </section>
  )
}

function FlowsSection({ data }: { data: FlowSettings[] }) {
  return (
    <section className="settings-section">
      <header>
        <p className="eyebrow">Paramètres</p>
        <h2>Flux</h2>
        <p>Flux d’orchestration enregistrés dans Hanuman.</p>
      </header>

      {data.length ? (
        <div className="settings-list">
          {data.map((flow) => (
            <article key={flow.id} className="settings-list__item">
              <div>
                <strong>{flow.label}</strong>
                <span>{flow.id}</span>
              </div>

              <div>
                <span>
                  {flow.enabled === undefined
                    ? 'Activation inconnue'
                    : flow.enabled
                      ? 'Activé'
                      : 'Désactivé'}
                </span>
                <span>{flow.status ?? 'État inconnu'}</span>
              </div>

              <small>
                Dernière exécution :{' '}
                {flow.last_run_at
                  ? new Date(flow.last_run_at).toLocaleString('fr-FR')
                  : 'Jamais'}
              </small>

              {flow.last_error ? (
                <small className="settings-error-text">{flow.last_error}</small>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <EmptyState message="Aucun flux n’est enregistré." />
      )}
    </section>
  )
}

function JournalSection({ data }: { data: JournalSettings }) {
  return (
    <section className="settings-section">
      <header>
        <p className="eyebrow">Paramètres</p>
        <h2>Journal de Vie</h2>
        <p>État réel du domaine Journal de Vie dans Hanuman.</p>
      </header>

      <dl className="settings-facts">
        <div>
          <dt>Enregistré</dt>
          <dd>{data.registered ? 'Oui' : 'Non'}</dd>
        </div>

        <div>
          <dt>État</dt>
          <dd>{data.status ?? 'Non renseigné'}</dd>
        </div>

        <div>
          <dt>Routines</dt>
          <dd>{data.routines_count}</dd>
        </div>

        <div>
          <dt>Dernière analyse</dt>
          <dd>
            {data.last_analysis_at
              ? new Date(data.last_analysis_at).toLocaleString('fr-FR')
              : 'Jamais'}
          </dd>
        </div>
      </dl>
    </section>
  )
}

function AppearanceSection({ data }: { data: AppearanceSettings }) {
  return (
    <section className="settings-section">
      <header>
        <p className="eyebrow">Paramètres</p>
        <h2>Apparence</h2>
        <p>Préférences visuelles actuellement connues par Hanuman.</p>
      </header>

      <dl className="settings-facts">
        <div>
          <dt>Thème</dt>
          <dd>{data.theme ?? 'Non renseigné'}</dd>
        </div>

        <div>
          <dt>Langue</dt>
          <dd>{data.language ?? 'Non renseignée'}</dd>
        </div>

        <div>
          <dt>Animations</dt>
          <dd>
            {data.animations === undefined
              ? 'Non renseigné'
              : data.animations
                ? 'Activées'
                : 'Désactivées'}
          </dd>
        </div>
      </dl>
    </section>
  )
}

function AISection({ data }: { data: AISettings }) {
  return (
    <section className="settings-section">
      <header>
        <p className="eyebrow">Paramètres</p>
        <h2>IA</h2>
        <p>Configuration IA réellement exposée par Hanuman.</p>
      </header>

      <dl className="settings-facts">
        <div>
          <dt>Configurée</dt>
          <dd>
            {data.configured === undefined
              ? 'Non renseigné'
              : data.configured
                ? 'Oui'
                : 'Non'}
          </dd>
        </div>

        <div>
          <dt>Fournisseur</dt>
          <dd>{data.provider ?? 'Non renseigné'}</dd>
        </div>

        <div>
          <dt>Modèle</dt>
          <dd>{data.model ?? 'Non renseigné'}</dd>
        </div>
      </dl>
    </section>
  )
}

function DiagnosticSection({ data }: { data: DiagnosticItem[] }) {
  return (
    <section className="settings-section">
      <header>
        <p className="eyebrow">Paramètres</p>
        <h2>Diagnostic</h2>
        <p>
          Contrôles produits par le backend, sans liste codée en dur dans
          React.
        </p>
      </header>

      {data.length ? (
        <div className="settings-list">
          {data.map((item) => (
            <article key={`${item.kind}-${item.id}`} className="settings-list__item">
              <div>
                <strong>{item.label}</strong>
                <span>{item.kind}</span>
              </div>

              <div>
                <span>{item.status}</span>
                <span>
                  {item.latency_ms === null ||
                  item.latency_ms === undefined
                    ? '—'
                    : `${item.latency_ms} ms`}
                </span>
              </div>

              {item.message ? <small>{item.message}</small> : null}

              <small>
                Dernier contrôle :{' '}
                {item.checked_at
                  ? new Date(item.checked_at).toLocaleString('fr-FR')
                  : 'Jamais'}
              </small>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState message="Aucun contrôle de diagnostic n’est disponible." />
      )}
    </section>
  )
}

function AboutSection({ data }: { data: AboutSettings }) {
  return (
    <section className="settings-section">
      <header>
        <p className="eyebrow">Paramètres</p>
        <h2>À propos</h2>
        <p>Informations techniques exposées par Hanuman.</p>
      </header>

      <dl className="settings-facts">
        <div>
          <dt>Nom</dt>
          <dd>{data.name ?? 'Hanuman'}</dd>
        </div>

        <div>
          <dt>Version</dt>
          <dd>{data.version ?? 'Non renseignée'}</dd>
        </div>

        <div>
          <dt>Environnement</dt>
          <dd>{data.environment ?? 'Non renseigné'}</dd>
        </div>

        <div>
          <dt>Build</dt>
          <dd>{data.build ?? 'Non renseigné'}</dd>
        </div>

        <div>
          <dt>Licence</dt>
          <dd>{data.license ?? 'Non renseignée'}</dd>
        </div>
      </dl>
    </section>
  )
}

function SettingsContent({
  section,
  data,
}: {
  section: SettingsSectionId
  data: HanumanSettings
}) {
  switch (section) {
    case 'general':
      return <GeneralSection data={data.general} />
    case 'connectors':
      return <ConnectorsSection data={data.connectors} />
    case 'flows':
      return <FlowsSection data={data.flows} />
    case 'journal':
      return <JournalSection data={data.journal} />
    case 'appearance':
      return <AppearanceSection data={data.appearance} />
    case 'ai':
      return <AISection data={data.ai} />
    case 'diagnostic':
      return <DiagnosticSection data={data.diagnostic} />
    case 'about':
      return <AboutSection data={data.about} />
  }
}

function isSettingsSection(value: string | undefined): value is SettingsSectionId {
  return sections.some((section) => section.id === value)
}

export default function SettingsPage() {
  const { section } = useParams()
  const [data, setData] = useState<HanumanSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const activeSection = isSettingsSection(section) ? section : 'general'

  async function loadSettings() {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API}/settings`)

      if (!response.ok) {
        throw new Error(`Réponse HTTP ${response.status}`)
      }

      const payload = (await response.json()) as HanumanSettings
      setData(payload)
    } catch (loadError) {
      setData(null)
      setError(
        loadError instanceof Error
          ? loadError.message
          : 'Impossible de charger les paramètres.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadSettings()
  }, [])

  if (section !== undefined && !isSettingsSection(section)) {
    return <Navigate to="/settings/general" replace />
  }

  if (section === undefined) {
    return <Navigate to="/settings/general" replace />
  }

  return (
    <div className="settings-page">
      <aside className="settings-navigation">
        <header>
          <p className="eyebrow">Hanuman</p>
          <h1>Paramètres</h1>
          <p>Configuration, contrôle et observabilité du système.</p>
        </header>

        <nav aria-label="Sections des paramètres">
          {sections.map(({ id, label, icon: Icon }) => (
            <NavLink
              key={id}
              to={`/settings/${id}`}
              className={({ isActive }) =>
                `settings-navigation__item${isActive ? ' active' : ''}`
              }
            >
              <Icon size={18} />
              <strong>{label}</strong>
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="settings-content">
        {loading ? (
          <div className="settings-system-state">
            <LoaderCircle className="spin" size={22} />
            <div>
              <strong>Lecture d’Hanuman</strong>
              <span>Chargement des paramètres réels…</span>
            </div>
          </div>
        ) : null}

        {!loading && error ? (
          <div className="settings-system-state settings-system-state--error">
            <TriangleAlert size={22} />

            <div>
              <strong>Données indisponibles</strong>
              <span>
                Le backend n’expose pas encore correctement `GET /settings` :
                {' '}
                {error}
              </span>
            </div>

            <button type="button" onClick={() => void loadSettings()}>
              <RefreshCw size={16} />
              Réessayer
            </button>
          </div>
        ) : null}

        {!loading && !error && data ? (
          <SettingsContent section={activeSection} data={data} />
        ) : null}
      </main>
    </div>
  )
}