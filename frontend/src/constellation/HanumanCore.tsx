import { BrainCircuit } from 'lucide-react'

type Props = {
  selected: boolean
  onSelect: () => void
}

export function HanumanCore({ selected, onSelect }: Props) {
  return (
    <button
      type="button"
      className={`constellation-core${selected ? ' is-selected' : ''}`}
      aria-label="Hanuman, moteur d’orchestration"
      aria-pressed={selected}
      onClick={onSelect}
    >
      <span className="constellation-core__orbits" aria-hidden="true" />
      <span className="constellation-core__body"><BrainCircuit size={25} /></span>
      <span className="constellation-core__copy">
        <b>Hanuman</b>
        <small>Moteur d’orchestration</small>
      </span>
    </button>
  )
}
