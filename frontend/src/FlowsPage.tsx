import { ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { flowDefinitions } from './models/flows'

export default function FlowsPage() {
  const navigate = useNavigate()

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
        {flowDefinitions.map(({ id, title, description, path, tone, status, icon: Icon }) => (
          <button key={id} className={`catalog-card tone-${tone}`} onClick={() => navigate(path)}>
            <span className="catalog-card__top"><span className="orchestration-card__icon"><Icon size={21} /></span><span className="catalog-status">{status}</span></span>
            <b>{title}</b>
            <p>{description}</p>
            <span className="catalog-card__footer">Entrer dans le flux <ArrowRight size={16} /></span>
          </button>
        ))}
      </section>
    </div>
  )
}
