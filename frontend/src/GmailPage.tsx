import { AlertTriangle, ExternalLink, Inbox, LoaderCircle, Mail, RefreshCw, Search, Star } from 'lucide-react'
import { FormEvent, useEffect, useMemo, useState } from 'react'

type GmailStatus = { configured: boolean; connected: boolean; email?: string | null; unread: number; message?: string | null }
type GmailMessage = { id: string; thread_id: string; subject: string; sender: string; date?: string | null; snippet: string; unread: boolean; important: boolean; labels: string[] }
type GmailMessageDetail = GmailMessage & { recipients: string[]; cc: string[]; body: string }

async function api<T>(url: string): Promise<T> {
  const response = await fetch(url)
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || `Erreur HTTP ${response.status}`)
  return data as T
}

export default function GmailPage() {
  const [status, setStatus] = useState<GmailStatus | null>(null)
  const [messages, setMessages] = useState<GmailMessage[]>([])
  const [selected, setSelected] = useState<GmailMessageDetail | null>(null)
  const [query, setQuery] = useState('in:inbox')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function loadStatus() {
    const next = await api<GmailStatus>('/api/gmail/status')
    setStatus(next)
    return next
  }

  async function loadMessages(search = query) {
    setLoading(true); setError(null)
    try {
      const nextStatus = await loadStatus()
      if (!nextStatus.connected) { setMessages([]); return }
      const data = await api<{ messages: GmailMessage[] }>(`/api/gmail/messages?max_results=40&query=${encodeURIComponent(search)}`)
      setMessages(data.messages)
      if (data.messages[0]) await openMessage(data.messages[0].id)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Impossible de charger Gmail.')
    } finally { setLoading(false) }
  }

  async function openMessage(id: string) {
    try { setSelected(await api<GmailMessageDetail>(`/api/gmail/messages/${id}`)) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Impossible de lire le message.') }
  }

  async function connect() {
    try {
      const data = await api<{ url: string }>('/api/gmail/auth/start')
      window.open(data.url, '_blank', 'noopener,noreferrer')
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Impossible de lancer OAuth Gmail.') }
  }

  useEffect(() => { void loadMessages() }, [])
  const importantCount = useMemo(() => messages.filter((message) => message.important).length, [messages])

  function submit(event: FormEvent) { event.preventDefault(); void loadMessages(query) }

  return <div className="page gmail-page">
    <header className="gmail-header">
      <div><p className="eyebrow">Hanuman / Gmail</p><h1>La correspondance qui mérite ton attention.</h1><p>Lecture seule : Hanuman observe, résume et prépare le terrain sans envoyer, supprimer ni déplacer aucun message.</p></div>
      <button className="refresh-button" onClick={() => void loadMessages()} disabled={loading}><RefreshCw size={17} className={loading ? 'spin' : ''} /> Actualiser</button>
    </header>

    {!status?.connected ? <section className="gmail-connect">
      <Mail size={32} /><h2>Connecter Gmail</h2><p>{status?.message || 'Autorise Hanuman à consulter tes messages en lecture seule.'}</p>
      <button onClick={() => void connect()}>Ouvrir l’autorisation Google <ExternalLink size={16} /></button>
      <small>Après validation, reviens ici puis clique sur Actualiser.</small>
    </section> : <>
      <section className="compact-stats gmail-stats"><span><b>{status.unread}</b><small>non lus</small></span><span><b>{messages.length}</b><small>chargés</small></span><span><b>{importantCount}</b><small>importants</small></span><span><b>{status.email}</b><small>compte connecté</small></span></section>
      <form className="gmail-search" onSubmit={submit}><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Recherche Gmail : in:inbox, is:unread, from:…" /><button>Rechercher</button></form>
      {error && <div className="error-panel"><AlertTriangle size={18} /><b>Gmail proteste.</b><span>{error}</span></div>}
      <section className="gmail-workbench">
        <div className="gmail-list"><div className="panel-title"><span>Messages</span><small>{messages.length}</small></div>
          {loading ? <div className="gmail-empty"><LoaderCircle className="spin" /> Lecture de la boîte…</div> : messages.map((message) => <button key={message.id} className={`gmail-row ${selected?.id === message.id ? 'is-selected' : ''}`} onClick={() => void openMessage(message.id)}>
            <span className="gmail-row__icon">{message.important ? <Star size={16} /> : <Inbox size={16} />}</span><span><b>{message.subject}</b><small>{message.sender}</small><p>{message.snippet}</p></span>{message.unread && <i />}
          </button>)}
        </div>
        <article className="gmail-reader">{selected ? <><p className="eyebrow">Message</p><h2>{selected.subject}</h2><div className="gmail-meta"><b>{selected.sender}</b><span>{selected.date || 'Date inconnue'}</span></div><p className="gmail-recipients">À : {selected.recipients.join(', ') || '—'}</p><pre>{selected.body || selected.snippet}</pre></> : <div className="gmail-empty"><Mail size={27} /> Sélectionne un message.</div>}</article>
      </section>
    </>}
  </div>
}
