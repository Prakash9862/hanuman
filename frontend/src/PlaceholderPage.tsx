import type { LucideIcon } from 'lucide-react'

type PlaceholderPageProps = {
  eyebrow: string
  title: string
  description: string
  icon: LucideIcon
  note: string
}

export default function PlaceholderPage({ eyebrow, title, description, icon: Icon, note }: PlaceholderPageProps) {
  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </header>
      <section className="placeholder-panel">
        <Icon size={28} />
        <b>{note}</b>
        <span>Aucune fonctionnalité n’est simulée sur cet écran.</span>
      </section>
    </div>
  )
}
