import {
  AlertTriangle,
  ArrowDownLeft,
  ArrowUpRight,
  CheckCircle2,
  ExternalLink,
  FileText,
  GitCompareArrows,
  Library,
  LoaderCircle,
  RefreshCw,
  Search,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

type SyncStatus = 'synced' | 'obsidian_only' | 'notion_only' | 'obsidian_newer' | 'notion_newer' | 'conflict' | 'unknown'
type Item = {
  id: string
  title: string
  status: SyncStatus
  obsidian?: { path: string; title: string; modified_at: string; tags: string[]; open_url: string } | null
  notion?: { page_id: string; title: string; modified_at?: string | null; url: string } | null
}
type Stats = {
  vault_notes: number; notion_pages: number; linked: number; synced: number; obsidian_only: number
  notion_only: number; obsidian_newer: number; notion_newer: number; conflicts: number
}
type PublishResponse = { ok: boolean; notion?: { id?: string; url?: string }; error?: string }
type PublishState = 'idle' | 'loading' | 'success' | 'error'

const emptyStats: Stats = { vault_notes: 0, notion_pages: 0, linked: 0, synced: 0, obsidian_only: 0, notion_only: 0, obsidian_newer: 0, notion_newer: 0, conflicts: 0 }
const statusCopy: Record<SyncStatus, { label: string; hint: string }> = {
  synced: { label: 'Synchronisé', hint: 'Les deux versions sont alignées.' },
  obsidian_only: { label: 'Obsidian uniquement', hint: 'Cette note peut être publiée dans Notion.' },
  notion_only: { label: 'Notion uniquement', hint: 'Cette page peut rejoindre le vault.' },
  obsidian_newer: { label: 'Obsidian plus récent', hint: 'Une mise à jour attend côté Notion.' },
  notion_newer: { label: 'Notion plus récent', hint: 'Une mise à jour attend dans le vault.' },
  conflict: { label: 'Conflit', hint: 'Les deux côtés ont changé depuis le dernier échange.' },
  unknown: { label: 'État inconnu', hint: 'La liaison existe mais manque d’historique.' },
}
function formatDate(value?: string | null) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export default function ObsidianNotionPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<Item[]>([])
  const [stats, setStats] = useState<Stats>(emptyStats)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState<'all' | SyncStatus>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [publishState, setPublishState] = useState<PublishState>('idle')
  const [publishMessage, setPublishMessage] = useState('')
  const [publishedUrl, setPublishedUrl] = useState<string | null>(null)

  async function load() {
    setLoading(true); setError(null)
    try {
      const suffix = query.trim() ? `?query=${encodeURIComponent(query.trim())}` : ''
      const [itemsResponse, statsResponse] = await Promise.all([
        fetch(`/api/orchestrations/obsidian-notion/items${suffix}`),
        fetch('/api/orchestrations/obsidian-notion/stats'),
      ])
      if (!itemsResponse.ok || !statsResponse.ok) throw new Error('Le moteur Hanuman ne répond pas correctement.')
      const itemData = (await itemsResponse.json()) as { items: Item[] }
      setItems(itemData.items)
      setStats((await statsResponse.json()) as Stats)
      setSelectedId((current) => current && itemData.items.some((item) => item.id === current) ? current : itemData.items[0]?.id ?? null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Impossible de charger les données.')
    } finally { setLoading(false) }
  }

  async function publishToNotion(item: Item) {
    if (!item.obsidian) return
    setPublishState('loading')
    setPublishMessage('Hanuman lit la note et construit la page Notion…')
    setPublishedUrl(null)
    try {
      const response = await fetch('/api/orchestrations/obsidian-to-notion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: item.obsidian.path }),
      })
      const data = (await response.json()) as PublishResponse
      if (!response.ok || !data.ok) throw new Error(data.error || `Erreur HTTP ${response.status}`)
      setPublishState('success')
      setPublishMessage('La note a été publiée dans Notion.')
      setPublishedUrl(data.notion?.url || null)
    } catch (caught) {
      setPublishState('error')
      setPublishMessage(caught instanceof Error ? caught.message : 'Échec de la publication vers Notion.')
    }
  }

  useEffect(() => { void load() }, [])
  useEffect(() => {
    setPublishState('idle'); setPublishMessage(''); setPublishedUrl(null)
  }, [selectedId])

  const visibleItems = useMemo(() => items.filter((item) => status === 'all' || item.status === status), [items, status])
  const selected = items.find((item) => item.id === selectedId) ?? null
  const folders = useMemo(() => {
    const counts = new Map<string, number>()
    items.forEach((item) => {
      const folder = item.obsidian?.path.includes('/') ? item.obsidian.path.split('/')[0] : 'Racine'
      counts.set(folder, (counts.get(folder) ?? 0) + 1)
    })
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10)
  }, [items])

  return <div className="page obsidian-space">
    <header className="obsidian-header"><div>
      <button className="breadcrumb-button" onClick={() => navigate('/orchestrations')}>← Orchestrations</button>
      <p className="eyebrow">Espace spécialisé</p><h1>Obsidian <span>↔</span> Notion</h1>
      <p>Explorer, publier, importer, comparer et suivre les échanges sans quitter Hanuman.</p>
    </div><button className="refresh-button" onClick={() => void load()} disabled={loading}><RefreshCw size={17} className={loading ? 'spin' : ''} /> Actualiser</button></header>

    <section className="compact-stats">
      <span><b>{stats.vault_notes}</b><small>notes du vault</small></span><span><b>{stats.notion_pages}</b><small>pages Notion</small></span>
      <span><b>{stats.linked}</b><small>liaisons</small></span><span><b>{stats.conflicts}</b><small>conflits</small></span><span><b>{stats.obsidian_only}</b><small>à publier</small></span>
    </section>

    <section className="orchestration-workbench">
      <aside className="vault-panel"><div className="panel-title"><span>Vault</span><small>{stats.vault_notes}</small></div>
        <form className="search-box" onSubmit={(event) => { event.preventDefault(); void load() }}><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Rechercher…" /></form>
        <div className="folder-list"><button className="folder-active"><Library size={15} /> Toutes les notes <small>{stats.vault_notes}</small></button>{folders.map(([folder, count]) => <button key={folder}><FileText size={15} /> {folder}<small>{count}</small></button>)}</div>
        <div className="panel-section-label">Filtres</div><div className="vertical-filters">{([['all','Tout'],['synced','Synchronisés'],['obsidian_only','À publier'],['notion_only','À importer'],['conflict','Conflits']] as Array<['all' | SyncStatus,string]>).map(([value,label]) => <button key={value} className={status === value ? 'filter-active' : ''} onClick={() => setStatus(value)}>{label}</button>)}</div>
      </aside>
      <div className="inventory-panel"><div className="panel-title"><span>Inventaire</span><small>{visibleItems.length} éléments</small></div>
        {error && <div className="error-panel"><b>Hanuman attend son moteur.</b><span>{error}</span></div>}
        {!error && !loading && visibleItems.length === 0 && <div className="empty-panel"><GitCompareArrows size={26} /><b>Aucun élément</b></div>}
        <div className="inventory-list">{visibleItems.map((item) => <button key={item.id} className={`inventory-row${selectedId === item.id ? ' inventory-row--selected' : ''}`} onClick={() => setSelectedId(item.id)}><span className="file-icon"><FileText size={17} /></span><span className="inventory-copy"><b>{item.title}</b><small>{item.obsidian?.path ?? 'Page Notion sans fichier local'}</small></span><span className={`status-dot status-dot--${item.status}`} /><span className="inventory-date">{formatDate(item.obsidian?.modified_at ?? item.notion?.modified_at)}</span></button>)}</div>
      </div>
      <aside className="detail-panel">{selected ? <>
        <div className="detail-heading"><span className="file-icon"><FileText size={18} /></span><div><h2>{selected.title}</h2><p>{selected.obsidian?.path ?? 'Page Notion'}</p></div></div>
        <div className={`detail-status status--${selected.status}`}><span>{statusCopy[selected.status].label}</span><small>{statusCopy[selected.status].hint}</small></div>
        <div className="detail-section"><h3>Présence</h3><div className="presence-grid"><span className={selected.obsidian ? 'presence-ok' : ''}>Obsidian<b>{selected.obsidian ? 'Disponible' : 'Absent'}</b></span><span className={selected.notion ? 'presence-ok' : ''}>Notion<b>{selected.notion ? 'Disponible' : 'Absent'}</b></span></div></div>
        <div className="detail-section"><h3>Dernière activité</h3><p>{formatDate(selected.obsidian?.modified_at ?? selected.notion?.modified_at)}</p></div>
        {!!selected.obsidian?.tags.length && <div className="detail-section"><h3>Tags</h3><div className="tags">{selected.obsidian.tags.map((tag) => <span key={tag}>#{tag}</span>)}</div></div>}
        <div className="detail-actions">
          {selected.obsidian && <a href={selected.obsidian.open_url}><ExternalLink size={15} /> Ouvrir dans Obsidian</a>}
          {selected.notion && <a href={selected.notion.url} target="_blank" rel="noreferrer"><ExternalLink size={15} /> Ouvrir dans Notion</a>}
          {selected.status === 'obsidian_only' && <button onClick={() => void publishToNotion(selected)} disabled={publishState === 'loading'}>{publishState === 'loading' ? <LoaderCircle size={15} className="spin" /> : <ArrowUpRight size={15} />} {publishState === 'loading' ? 'Publication…' : 'Publier vers Notion'}</button>}
          {selected.status === 'notion_only' && <button><ArrowDownLeft size={15} /> Importer dans le vault</button>}
          {['conflict','obsidian_newer','notion_newer'].includes(selected.status) && <button><GitCompareArrows size={15} /> Comparer les versions</button>}
        </div>
        {publishState !== 'idle' && <div className={`detail-status publish-feedback publish-feedback--${publishState}`}>
          <span>{publishState === 'loading' ? <LoaderCircle size={13} className="spin" /> : publishState === 'success' ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />} {publishState === 'loading' ? 'En cours' : publishState === 'success' ? 'Publié' : 'Erreur'}</span>
          <small>{publishMessage}</small>
          {publishedUrl && <a href={publishedUrl} target="_blank" rel="noreferrer"><ExternalLink size={14} /> Ouvrir la page créée</a>}
        </div>}
        <div className="detail-section detail-future"><h3>Historique & diff</h3><p>Le panneau est réservé dès maintenant pour l’historique des échanges, le diff et la résolution des conflits.</p></div>
      </> : <div className="empty-detail">Sélectionne un élément.</div>}</aside>
    </section>
  </div>
}
