import { BookOpen, ExternalLink, MapPin, Music2, Search, Youtube } from 'lucide-react'
import { FormEvent, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

type SearchResult = {
  title?: string
  description?: string
  url?: string
  thumbnail?: string
  channel?: string
}

export default function ResourcesPage() {
  const [youtubeQuery, setYoutubeQuery] = useState('')
  const [gallicaQuery, setGallicaQuery] = useState('')
  const [imslpQuery, setImslpQuery] = useState('')
  const [mapsQuery, setMapsQuery] = useState('')
  const [youtubeResults, setYoutubeResults] = useState<SearchResult[]>([])
  const [gallicaResults, setGallicaResults] = useState<SearchResult[]>([])
  const [message, setMessage] = useState<string | null>(null)

  async function searchYoutube(event: FormEvent) {
    event.preventDefault()
    if (!youtubeQuery.trim()) return
    setMessage(null)
    const response = await fetch(`${API_BASE}/resources/youtube/search?q=${encodeURIComponent(youtubeQuery)}&max_results=8`)
    const payload = await response.json()
    if (!response.ok) {
      setMessage(payload.detail ?? 'YouTube indisponible')
      return
    }
    setYoutubeResults(payload.results ?? [])
  }

  async function searchGallica(event: FormEvent) {
    event.preventDefault()
    if (!gallicaQuery.trim()) return
    setMessage(null)
    const response = await fetch(`${API_BASE}/resources/gallica/search?q=${encodeURIComponent(gallicaQuery)}&max_results=8`)
    const payload = await response.json()
    if (!response.ok) {
      setMessage(payload.detail ?? 'Gallica indisponible')
      return
    }
    setGallicaResults(payload.results ?? [])
  }

  function openImslp(event: FormEvent) {
    event.preventDefault()
    if (!imslpQuery.trim()) return
    window.open(`${API_BASE}/resources/imslp/search?q=${encodeURIComponent(imslpQuery)}`, '_blank')
  }

  function openMaps(event: FormEvent) {
    event.preventDefault()
    if (!mapsQuery.trim()) return
    window.open(`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(mapsQuery)}`, '_blank')
  }

  return (
    <div className="resources-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Hanuman / Ressources</p>
          <h1>Recherche transversale</h1>
          <p>YouTube, Gallica, IMSLP et Google Maps réunis dans un même espace.</p>
        </div>
      </header>

      {message && <div className="resources-message">{message}</div>}

      <section className="resources-grid">
        <article className="resource-panel">
          <div className="resource-panel__head"><Youtube size={22} /><div><b>YouTube</b><span>Vidéos, chaînes et métadonnées</span></div></div>
          <form onSubmit={searchYoutube}><input value={youtubeQuery} onChange={(e) => setYoutubeQuery(e.target.value)} placeholder="Ex. Ambroise Thomas" /><button><Search size={16} /> Rechercher</button></form>
          <div className="resource-results">{youtubeResults.map((item, index) => <a key={`${item.url}-${index}`} href={item.url} target="_blank" rel="noreferrer"><div><b>{item.title ?? 'Vidéo'}</b><span>{item.channel ?? item.description ?? ''}</span></div><ExternalLink size={15} /></a>)}</div>
        </article>

        <article className="resource-panel">
          <div className="resource-panel__head"><BookOpen size={22} /><div><b>Gallica</b><span>Collections numérisées de la BnF</span></div></div>
          <form onSubmit={searchGallica}><input value={gallicaQuery} onChange={(e) => setGallicaQuery(e.target.value)} placeholder="Ex. Massenet" /><button><Search size={16} /> Rechercher</button></form>
          <div className="resource-results">{gallicaResults.map((item, index) => <a key={`${item.url}-${index}`} href={item.url} target="_blank" rel="noreferrer"><div><b>{item.title ?? 'Document'}</b><span>{item.description ?? ''}</span></div><ExternalLink size={15} /></a>)}</div>
        </article>

        <article className="resource-panel compact">
          <div className="resource-panel__head"><Music2 size={22} /><div><b>IMSLP</b><span>Recherche rapide de partitions</span></div></div>
          <form onSubmit={openImslp}><input value={imslpQuery} onChange={(e) => setImslpQuery(e.target.value)} placeholder="Ex. Thaïs Massenet" /><button><ExternalLink size={16} /> Ouvrir</button></form>
        </article>

        <article className="resource-panel compact">
          <div className="resource-panel__head"><MapPin size={22} /><div><b>Google Maps</b><span>Itinéraire vers une adresse</span></div></div>
          <form onSubmit={openMaps}><input value={mapsQuery} onChange={(e) => setMapsQuery(e.target.value)} placeholder="Ex. 1 place d'Armes, Metz" /><button><ExternalLink size={16} /> Itinéraire</button></form>
        </article>
      </section>
    </div>
  )
}
