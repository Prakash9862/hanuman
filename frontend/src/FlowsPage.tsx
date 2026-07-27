import { ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { flowDefinitions } from './models/flows'

export default function FlowsPage() {
  const navigate = useNavigate()
  const flows = flowDefinitions.filter(({ kind }) => kind === 'flow')
  const readOnlySpaces = flowDefinitions.filter(({ kind }) => kind === 'read-only-space')

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Hanuman / Flux</p>
          <h1>Les parcours où les outils coopèrent.</h1>
          <p>Chaque flux relie plusieurs systèmes autour d’un échange explicite, tout en restant intégré au même environnement Hanuman.</p>
        </div>
      </header>

      <section className="catalog-grid" aria-label="Flux disponibles">
        {flows.map(({ id, title, description, path, tone, status, icon: Icon }) => (
          <button key={id} className={`catalog-card tone-${tone}`} onClick={() => navigate(path)}>
            <span className="catalog-card__top"><span className="orchestration-card__icon"><Icon size={21} /></span><span className="catalog-status">{status}</span></span>
            <b>{title}</b>
            <p>{description}</p>
            <span className="catalog-card__footer">Entrer dans le flux <ArrowRight size={16} /></span>
          </button>
        ))}
      </section>

      <section className="catalog-section">
        <div className="section-heading">
          <div><p className="eyebrow">Capacités accessibles</p><h2>Espaces en lecture seule</h2></div>
        </div>
        <p className="catalog-section__intro">Ces espaces donnent accès à un seul système. Ils ne sont pas présentés comme des flux multi-outils.</p>
        <div className="catalog-grid catalog-grid--compact">
          {readOnlySpaces.map(({ id, title, description, path, tone, status, icon: Icon }) => (
            <button key={id} className={`catalog-card tone-${tone}`} onClick={() => navigate(path)}>
              <span className="catalog-card__top"><span className="orchestration-card__icon"><Icon size={21} /></span><span className="catalog-status">{status}</span></span>
              <b>{title}</b>
              <p>{description}</p>
              <span className="catalog-card__footer">Ouvrir l’espace <ArrowRight size={16} /></span>
            </button>
          ))}
        </div>
      </section>
    </div>
  )
}
