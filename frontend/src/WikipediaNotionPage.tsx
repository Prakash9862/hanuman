import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ExternalLink,
  LoaderCircle,
  RotateCcw,
  Sparkles,
} from 'lucide-react'
import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

type RunState = 'idle' | 'loading' | 'success' | 'error'

type PublishResponse = {
  ok: boolean
  notion?: { id: string; url: string }
  error?: string
}

export default function WikipediaNotionPage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [parentId, setParentId] = useState('')
  const [state, setState] = useState<RunState>('idle')
  const [message, setMessage] = useState('')
  const [result, setResult] = useState<PublishResponse['notion'] | null>(null)

  async function publish(event: FormEvent) {
    event.preventDefault()
    const cleanQuery = query.trim()
    if (!cleanQuery) {
      setState('error')
      setMessage('Indique un titre ou une URL Wikipédia.')
      return
    }

    setState('loading')
    setMessage('Hanuman récupère l’article, structure son contenu et prépare la page Notion…')
    setResult(null)

    try {
      const response = await fetch('/api/orchestrations/wikipedia-to-notion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: cleanQuery,
          parent_id: parentId.trim() || null,
        }),
      })
      const data = (await response.json()) as PublishResponse
      if (!response.ok || !data.ok || !data.notion) {
        throw new Error(data.error || `Erreur HTTP ${response.status}`)
      }
      setState('success')
      setMessage('La page Wikipédia a été publiée dans Notion.')
      setResult(data.notion)
    } catch (caught) {
      setState('error')
      setMessage(caught instanceof Error ? caught.message : 'Échec de la publication vers Notion.')
    }
  }

  function reset() {
    setState('idle')
    setMessage('')
    setResult(null)
  }

  return (
    <div className="page wikipedia-space">
      <header className="wikipedia-header">
        <div>
          <button className="wikipedia-breadcrumb" onClick={() => navigate('/flows')}>← Flux</button>
          <p className="eyebrow">Espace spécialisé</p>
          <h1>Wikipédia <span>→</span> Notion</h1>
          <p>Transformer un article encyclopédique en page Notion structurée, lisible et directement exploitable.</p>
        </div>
        <div className="wikipedia-state-pill" data-state={state}>
          {state === 'idle' && <><Sparkles size={16} /> Prêt</>}
          {state === 'loading' && <><LoaderCircle size={16} className="spin" /> En cours</>}
          {state === 'success' && <><CheckCircle2 size={16} /> Réussi</>}
          {state === 'error' && <><AlertTriangle size={16} /> Erreur</>}
        </div>
      </header>

      <section className="wikipedia-layout">
        <form className="wikipedia-form" onSubmit={publish}>
          <div className="wikipedia-panel-heading">
            <BookOpen size={19} />
            <div><b>Nouvelle publication</b><small>Le moteur existant est appelé directement.</small></div>
          </div>

          <label>
            <span>Titre ou URL Wikipédia</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ex. Ambroise Thomas ou https://fr.wikipedia.org/…"
              disabled={state === 'loading'}
            />
          </label>

          <label>
            <span>Page parente Notion <small>facultatif</small></span>
            <input
              value={parentId}
              onChange={(event) => setParentId(event.target.value)}
              placeholder="Utilise la configuration par défaut si vide"
              disabled={state === 'loading'}
            />
          </label>

          <button className="wikipedia-submit" type="submit" disabled={state === 'loading'}>
            {state === 'loading' ? <LoaderCircle size={17} className="spin" /> : <ArrowRight size={17} />}
            {state === 'loading' ? 'Publication en cours…' : 'Publier dans Notion'}
          </button>
        </form>

        <aside className="wikipedia-status-panel">
          <div className={`wikipedia-state-card state-${state}`}>
            {state === 'idle' && <>
              <Sparkles size={28} />
              <h2>Prête à travailler</h2>
              <p>Entre un titre ou une URL. Hanuman récupérera le contenu, créera les blocs et publiera la page.</p>
            </>}

            {state === 'loading' && <>
              <LoaderCircle size={30} className="spin" />
              <h2>Orchestration en cours</h2>
              <p>{message}</p>
              <div className="wikipedia-progress"><span /></div>
            </>}

            {state === 'success' && <>
              <CheckCircle2 size={30} />
              <h2>Publication terminée</h2>
              <p>{message}</p>
              {result && <>
                <div className="wikipedia-result-meta"><span>Page ID</span><code>{result.id}</code></div>
                <a className="wikipedia-open" href={result.url} target="_blank" rel="noreferrer"><ExternalLink size={16} /> Ouvrir dans Notion</a>
              </>}
              <button className="wikipedia-reset" onClick={reset}><RotateCcw size={15} /> Nouvelle publication</button>
            </>}

            {state === 'error' && <>
              <AlertTriangle size={30} />
              <h2>La publication a échoué</h2>
              <p>{message}</p>
              <div className="wikipedia-error-help">Vérifie le token Notion, l’accès de l’intégration à la page parente et l’identifiant configuré.</div>
              <button className="wikipedia-reset" onClick={reset}><RotateCcw size={15} /> Réessayer</button>
            </>}
          </div>

          <div className="wikipedia-pipeline">
            <h3>Pipeline</h3>
            <span><i /> Recherche Wikipédia</span>
            <span><i /> Extraction des sections</span>
            <span><i /> Construction des blocs Notion</span>
            <span><i /> Publication sous le parent</span>
          </div>
        </aside>
      </section>
    </div>
  )
}
