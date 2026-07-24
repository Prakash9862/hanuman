import {
  ArrowDownLeft,
  ArrowUpRight,
  BarChart3,
  BookOpen,
  Boxes,
  ExternalLink,
  FileText,
  GitCompareArrows,
  RefreshCw,
  Search,
  Sparkles,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

type SyncStatus =
  | 'synced'
  | 'obsidian_only'
  | 'notion_only'
  | 'obsidian_newer'
  | 'notion_newer'
  | 'conflict'
  | 'unknown'

type Item = {
  id: string
  title: string
  status: SyncStatus
  obsidian?: {
    path: string
    title: string
    modified_at: string
    tags: string[]
    open_url: string
  } | null
  notion?: {
    page_id: string
    title: string
    modified_at?: string | null
    url: string
  } | null
}

type Stats = {
  vault_notes: number
  notion_pages: number
  linked: number
  synced: number
  obsidian_only: number
  notion_only: number
  obsidian_newer: number
  notion_newer: number
  conflicts: number
}

const emptyStats: Stats = {
  vault_notes: 0,
  notion_pages: 0,
  linked: 0,
  synced: 0,
  obsidian_only: 0,
  notion_only: 0,
  obsidian_newer: 0,
  notion_newer: 0,
  conflicts: 0,
}

const statusCopy: Record<SyncStatus, { label: string; hint: string }> = {
  synced: { label: 'Synchronisé', hint: 'Les deux versions sont alignées.' },
  obsidian_only: { label: 'Obsidian uniquement', hint: 'Cette note peut être publiée dans Notion.' },
  notion_only: { label: 'Notion uniquement', hint: 'Cette page peut rejoindre le vault.' },
  obsidian_newer: { label: 'Obsidian plus récent', hint: 'Une mise à jour attend côté Notion.' },
  notion_newer: { label: 'Notion plus récent', hint: 'Une mise à jour attend dans le vault.' },
  conflict: { label: 'Conflit', hint: 'Les deux côtés ont changé depuis le dernier échange.' },
  unknown: { label: 'État inconnu', hint: 'La liaison existe mais manque d’historique.' },
}

const filters: Array<{ value: 'all' | SyncStatus; label: string }> = [
  { value: 'all', label: 'Tout' },
  { value: 'synced', label: 'Synchronisés' },
  { value: 'obsidian_only', label: 'À publier' },
  { value: 'notion_only', label: 'À importer' },
  { value: 'conflict', label: 'Conflits' },
]

function formatDate(value?: string | null) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function App() {
  const [items, setItems] = useState<Item[]>([])
  const [stats, setStats] = useState<Stats>(emptyStats)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState<'all' | SyncStatus>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const suffix = query.trim() ? `?query=${encodeURIComponent(query.trim())}` : ''
      const [itemsResponse, statsResponse] = await Promise.all([
        fetch(`/orchestrations/obsidian-notion/items${suffix}`),
        fetch('/orchestrations/obsidian-notion/stats'),
      ])
      if (!itemsResponse.ok || !statsResponse.ok) {
        throw new Error('Le moteur Hanuman ne répond pas correctement.')
      }
      const itemData = (await itemsResponse.json()) as { items: Item[] }
      setItems(itemData.items)
      setStats((await statsResponse.json()) as Stats)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Impossible de charger les données.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const visibleItems = useMemo(
    () => items.filter((item) => status === 'all' || item.status === status),
    [items, status],
  )

  function submitSearch(event: React.FormEvent) {
    event.preventDefault()
    void load()
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand__mark"><Sparkles size={21} /></div>
          <div>
            <strong>Hanuman</strong>
            <span>Orchestration system</span>
          </div>
        </div>

        <nav className="nav">
          <button><BarChart3 size={18} /> Vue d’ensemble</button>
          <button className="nav__active"><Boxes size={18} /> Orchestrations</button>
          <button><BookOpen size={18} /> Bibliothèque</button>
        </nav>

        <div className="sidebar__footer">
          <span className="engine-dot" />
          Moteur connecté
        </div>
      </aside>

      <main>
        <header className="hero">
          <div>
            <p className="eyebrow">Orchestration active</p>
            <h1>Obsidian <span>↔</span> Notion</h1>
            <p>Un seul espace pour explorer, publier, importer et comprendre les échanges entre ton vault et ta page Notion dédiée.</p>
          </div>
          <button className="refresh-button" onClick={() => void load()} disabled={loading}>
            <RefreshCw size={17} className={loading ? 'spin' : ''} /> Actualiser
          </button>
        </header>

        <section className="stats-grid" aria-label="Statistiques">
          <article><span>Vault</span><strong>{stats.vault_notes}</strong><small>notes Markdown</small></article>
          <article><span>Notion</span><strong>{stats.notion_pages}</strong><small>pages dédiées</small></article>
          <article><span>Synchronisées</span><strong>{stats.synced}</strong><small>{stats.linked} liaisons</small></article>
          <article className={stats.conflicts ? 'stat-alert' : ''}><span>Conflits</span><strong>{stats.conflicts}</strong><small>à examiner</small></article>
        </section>

        <section className="workspace">
          <div className="workspace__toolbar">
            <form className="search-box" onSubmit={submitSearch}>
              <Search size={18} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Rechercher une note, un chemin ou un tag…"
                aria-label="Recherche"
              />
            </form>
            <div className="filters">
              {filters.map((filter) => (
                <button
                  key={filter.value}
                  className={status === filter.value ? 'filter-active' : ''}
                  onClick={() => setStatus(filter.value)}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="error-panel">
              <strong>Hanuman attend son moteur.</strong>
              <span>{error} Lance FastAPI sur le port 8000 puis actualise.</span>
            </div>
          )}

          {!error && !loading && visibleItems.length === 0 && (
            <div className="empty-panel">
              <GitCompareArrows size={28} />
              <strong>Aucun élément dans cette vue.</strong>
              <span>Modifie la recherche ou le filtre.</span>
            </div>
          )}

          <div className="items-list">
            {visibleItems.map((item) => (
              <article className="item-card" key={item.id}>
                <div className="item-card__identity">
                  <div className="file-icon"><FileText size={20} /></div>
                  <div>
                    <h2>{item.title}</h2>
                    <p>{item.obsidian?.path ?? 'Page Notion sans fichier local'}</p>
                    {!!item.obsidian?.tags.length && (
                      <div className="tags">{item.obsidian.tags.map((tag) => <span key={tag}>#{tag}</span>)}</div>
                    )}
                  </div>
                </div>

                <div className="resource-pair">
                  <div className={item.obsidian ? 'resource resource--ready' : 'resource'}>
                    <span>Obsidian</span>
                    <strong>{item.obsidian ? formatDate(item.obsidian.modified_at) : 'Absent'}</strong>
                  </div>
                  <GitCompareArrows size={17} />
                  <div className={item.notion ? 'resource resource--ready' : 'resource'}>
                    <span>Notion</span>
                    <strong>{item.notion ? formatDate(item.notion.modified_at) : 'Absent'}</strong>
                  </div>
                </div>

                <div className={`status status--${item.status}`}>
                  <span>{statusCopy[item.status].label}</span>
                  <small>{statusCopy[item.status].hint}</small>
                </div>

                <div className="actions">
                  {item.obsidian && (
                    <a href={item.obsidian.open_url}><ExternalLink size={15} /> Obsidian</a>
                  )}
                  {item.notion && (
                    <a href={item.notion.url} target="_blank" rel="noreferrer"><ExternalLink size={15} /> Notion</a>
                  )}
                  {item.status === 'obsidian_only' && <button><ArrowUpRight size={15} /> Publier</button>}
                  {item.status === 'notion_only' && <button><ArrowDownLeft size={15} /> Importer</button>}
                  {['conflict', 'obsidian_newer', 'notion_newer'].includes(item.status) && (
                    <button><GitCompareArrows size={15} /> Comparer</button>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
