import {
  BookOpen,
  ExternalLink,
  MapPin,
  Music2,
  Search,
  Youtube,
} from 'lucide-react'
import { FormEvent, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

const API_BASE = 'http://127.0.0.1:8000'

type ResourceId = 'youtube' | 'gallica' | 'imslp' | 'maps'

type SearchResult = {
  title?: string
  description?: string
  url?: string
  thumbnail?: string
  channel?: string
}

const resources = [
  {
    id: 'youtube' as const,
    label: 'YouTube',
    eyebrow: 'Vidéo et veille',
    placeholder: 'Rechercher une vidéo, une chaîne, un sujet…',
    icon: Youtube,
  },
  {
    id: 'gallica' as const,
    label: 'Gallica',
    eyebrow: 'Patrimoine et sources',
    placeholder: 'Rechercher une œuvre, un compositeur, un manuscrit…',
    icon: BookOpen,
  },
  {
    id: 'imslp' as const,
    label: 'IMSLP',
    eyebrow: 'Partitions',
    placeholder: 'Rechercher une œuvre ou un compositeur…',
    icon: Music2,
  },
  {
    id: 'maps' as const,
    label: 'Google Maps',
    eyebrow: 'Trajets et rendez-vous',
    placeholder: 'Saisir une adresse ou un lieu…',
    icon: MapPin,
  },
]

export default function ResourcesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialSource = searchParams.get('source') as ResourceId | null
  const [active, setActive] = useState<ResourceId>(
    resources.some((resource) => resource.id === initialSource)
      ? initialSource!
      : 'gallica',
  )
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [message, setMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const current = useMemo(
    () => resources.find((resource) => resource.id === active)!,
    [active],
  )

  function selectSource(source: ResourceId) {
    setActive(source)
    setSearchParams({ source })
    setQuery('')
    setResults([])
    setMessage(null)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const normalized = query.trim()
    if (!normalized) return

    setMessage(null)
    setResults([])

    if (active === 'maps') {
      window.open(
        `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(normalized)}`,
        '_blank',
      )
      return
    }

    if (active === 'imslp') {
      const response = await fetch(
        `${API_BASE}/resources/imslp/search?q=${encodeURIComponent(normalized)}`,
      )
      const payload = await response.json()
      if (!response.ok || !payload.url) {
        setMessage(payload.detail ?? 'IMSLP indisponible')
        return
      }
      window.open(payload.url, '_blank')
      return
    }

    setLoading(true)
    try {
      const endpoint = active === 'youtube' ? 'youtube' : 'gallica'
      const response = await fetch(
        `${API_BASE}/resources/${endpoint}/search?q=${encodeURIComponent(normalized)}&max_results=12`,
      )
      const payload = await response.json()
      if (!response.ok) {
        setMessage(payload.detail ?? `${current.label} indisponible`)
        return
      }
      setResults(payload.results ?? [])
    } catch {
      setMessage(`Impossible de joindre ${current.label}`)
    } finally {
      setLoading(false)
    }
  }

  const ActiveIcon = current.icon

  return (
    <div className="resources-page">
      <header className="resources-hero">
        <div>
          <p className="eyebrow">Hanuman / Ressources</p>
          <h1>Un seul point d’entrée vers tes sources.</h1>
          <p>
            Hanuman ne remplace pas YouTube, Gallica, IMSLP ou Maps : il les
            rassemble, puis les reliera aux orchestrations.
          </p>
        </div>
        <div className="resources-hero__count">
          <b>{resources.length}</b>
          <span>sources disponibles</span>
        </div>
      </header>

      <section className="resources-shell">
        <nav className="resources-tabs" aria-label="Sources de recherche">
          {resources.map(({ id, label, eyebrow, icon: Icon }) => (
            <button
              key={id}
              type="button"
              className={active === id ? 'is-active' : ''}
              onClick={() => selectSource(id)}
            >
              <Icon size={18} />
              <span><b>{label}</b><small>{eyebrow}</small></span>
            </button>
          ))}
        </nav>

        <div className="resources-console">
          <div className="resources-console__heading">
            <span className="resources-console__icon"><ActiveIcon size={23} /></span>
            <div>
              <p>{current.eyebrow}</p>
              <h2>{current.label}</h2>
            </div>
          </div>

          <form className="resources-search" onSubmit={handleSubmit}>
            <Search size={19} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={current.placeholder}
              autoFocus
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Recherche…' : active === 'maps' ? 'Itinéraire' : active === 'imslp' ? 'Ouvrir' : 'Rechercher'}
            </button>
          </form>

          {message && <div className="resources-message">{message}</div>}

          {!message && !loading && results.length === 0 && (
            <div className="resources-empty">
              <ActiveIcon size={28} />
              <b>{active === 'maps' ? 'Prépare un trajet' : active === 'imslp' ? 'Ouvre la bibliothèque de partitions' : `Recherche dans ${current.label}`}</b>
              <span>{current.placeholder}</span>
            </div>
          )}

          {results.length > 0 && (
            <div className="resource-results">
              {results.map((item, index) => (
                <a
                  key={`${item.url}-${index}`}
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {item.thumbnail && <img src={item.thumbnail} alt="" />}
                  <div>
                    <b>{item.title ?? 'Résultat'}</b>
                    <span>{item.channel ?? item.description ?? ''}</span>
                  </div>
                  <ExternalLink size={16} />
                </a>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
