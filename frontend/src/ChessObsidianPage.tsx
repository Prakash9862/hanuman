import { useState } from 'react'
import { Archive, CheckCircle2, ExternalLink, FolderOpen, RefreshCw, Swords } from 'lucide-react'

import './chess.css'

type SyncReport = {
  status: string
  username: string
  destination: string
  games_received: number
  games_created: number
  games_skipped: number
  openings_updated: number
}

export default function ChessObsidianPage() {
  const [limit, setLimit] = useState(200)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [report, setReport] = useState<SyncReport | null>(null)

  async function synchronize() {
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`/api/chess/sync?limit=${limit}`, { method: 'POST' })
      if (!response.ok) throw new Error(`Erreur API ${response.status}`)
      setReport(await response.json())
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Synchronisation impossible')
    } finally {
      setLoading(false)
    }
  }

  return <div className="page chess-page">
    <header className="chess-hero">
      <div>
        <p className="eyebrow">Hanuman / Chess.com → Obsidian</p>
        <h1>Transforme tes parties en mémoire de travail.</h1>
        <p>Hanuman importe les parties de <strong>prakasch</strong>, crée une note par partie et maintient des index propres par code ECO.</p>
      </div>
      <Swords size={46} />
    </header>

    <section className="chess-grid">
      <article className="chess-panel">
        <span className="chess-panel__icon"><ExternalLink size={20} /></span>
        <small>Compte source</small>
        <h2>Chess.com</h2>
        <strong>prakasch</strong>
        <a href="https://www.chess.com/member/prakasch" target="_blank" rel="noreferrer">Ouvrir le profil <ExternalLink size={14} /></a>
      </article>

      <article className="chess-panel">
        <span className="chess-panel__icon"><FolderOpen size={20} /></span>
        <small>Destination</small>
        <h2>Vault Obsidian</h2>
        <code>/home/vince/Prakash/projets/Obsidian_Priv-/Echecs</code>
      </article>
    </section>

    <section className="chess-sync-card">
      <div>
        <p className="eyebrow">Synchronisation</p>
        <h2>Importer les dernières parties</h2>
        <p>Les parties déjà présentes sont ignorées. Les tableaux d’ouverture et le Dashboard sont actualisés.</p>
      </div>
      <label>Nombre maximum
        <select value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
          <option value={25}>25 parties</option>
          <option value={50}>50 parties</option>
          <option value={100}>100 parties</option>
          <option value={200}>200 parties</option>
          <option value={500}>500 parties</option>
        </select>
      </label>
      <button className="chess-action" onClick={synchronize} disabled={loading}>
        <RefreshCw size={17} className={loading ? 'spin' : ''} />
        {loading ? 'Synchronisation…' : 'Synchroniser maintenant'}
      </button>
    </section>

    {error && <div className="chess-message chess-message--error">{error}</div>}

    {report && <section className="chess-report">
      <div className="chess-report__title"><CheckCircle2 size={22} /><div><small>Dernière synchronisation</small><h2>Bibliothèque mise à jour</h2></div></div>
      <div className="chess-stats">
        <span><strong>{report.games_created}</strong><small>nouvelles parties</small></span>
        <span><strong>{report.games_skipped}</strong><small>déjà présentes</small></span>
        <span><strong>{report.openings_updated}</strong><small>ouvertures ECO</small></span>
        <span><strong>{report.games_received}</strong><small>parties lues</small></span>
      </div>
      <p><Archive size={16} /> Notes écrites dans <code>{report.destination}</code></p>
    </section>}
  </div>
}
