import {
  CalendarDays,
  ExternalLink,
  MapPin,
  Navigation,
  RefreshCw,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

type CalendarInfo = {
  id: string
  summary: string
  description?: string | null
  primary: boolean
  access_role?: string | null
}

type CalendarEvent = {
  id: string
  summary: string
  description?: string | null
  location?: string | null
  start: string
  end?: string | null
  all_day: boolean
  status?: string | null
  html_link?: string | null
}

type CalendarResponse = {
  ok: boolean
  count: number
  calendars: CalendarInfo[]
}

type EventsResponse = {
  ok: boolean
  count: number
  events: CalendarEvent[]
}

const API_BASE = 'http://127.0.0.1:8000'

function formatEventDate(event: CalendarEvent): string {
  if (!event.start) return 'Date inconnue'

  if (event.all_day) {
    return new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'full',
    }).format(new Date(`${event.start}T12:00:00`))
  }

  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'full',
    timeStyle: 'short',
  }).format(new Date(event.start))
}

function mapsSearchUrl(location: string): string {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(location)}`
}

function mapsDirectionsUrl(location: string): string {
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(location)}`
}

export default function CalendarPage() {
  const [calendars, setCalendars] = useState<CalendarInfo[]>([])
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadCalendar = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const [calendarsResponse, eventsResponse] = await Promise.all([
        fetch(`${API_BASE}/calendar/calendars`),
        fetch(`${API_BASE}/calendar/events?max_results=30`),
      ])

      if (!calendarsResponse.ok || !eventsResponse.ok) {
        throw new Error('Impossible de charger Google Calendar')
      }

      const calendarsData =
        (await calendarsResponse.json()) as CalendarResponse

      const eventsData =
        (await eventsResponse.json()) as EventsResponse

      setCalendars(calendarsData.calendars ?? [])
      setEvents(eventsData.events ?? [])
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'Erreur inconnue lors du chargement',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadCalendar()
  }, [loadCalendar])

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Hanuman / Google Calendar</p>
          <h1>Calendrier</h1>
          <p>
            Tes prochains événements Google Calendar, avec accès rapide
            aux lieux et itinéraires Google Maps.
          </p>
        </div>

        <button
          type="button"
          className="calendar-refresh"
          onClick={() => void loadCalendar()}
          disabled={loading}
        >
          <RefreshCw size={17} />
          Actualiser
        </button>
      </header>

      <section className="calendar-summary">
        <article>
          <CalendarDays size={22} />
          <div>
            <b>{calendars.length}</b>
            <span>calendriers connectés</span>
          </div>
        </article>

        <article>
          <CalendarDays size={22} />
          <div>
            <b>{events.length}</b>
            <span>événements à venir</span>
          </div>
        </article>
      </section>

      {loading && (
        <div className="placeholder-panel">
          <RefreshCw size={25} />
          <b>Chargement du calendrier…</b>
        </div>
      )}

      {error && (
        <div className="calendar-error">
          <b>Calendar n’a pas pu être chargé.</b>
          <span>{error}</span>
          <a href={`${API_BASE}/calendar/auth`}>
            Reconnecter Google Calendar
          </a>
        </div>
      )}

      {!loading && !error && events.length === 0 && (
        <div className="placeholder-panel">
          <CalendarDays size={28} />
          <b>Aucun événement à venir</b>
          <span>
            Google Calendar est connecté, mais aucun événement futur
            n’a été trouvé.
          </span>
        </div>
      )}

      {!loading && !error && events.length > 0 && (
        <section className="calendar-events">
          {events.map((event) => (
            <article key={event.id} className="calendar-event">
              <div className="calendar-event__date">
                <CalendarDays size={17} />
                <span>{formatEventDate(event)}</span>
              </div>

              <h2>{event.summary}</h2>

              {event.location && (
                <>
                  <p className="calendar-event__location">
                    <MapPin size={15} />
                    {event.location}
                  </p>
                  <div className="calendar-event__maps">
                    <a
                      href={mapsSearchUrl(event.location)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <MapPin size={14} />
                      Voir le lieu
                    </a>
                    <a
                      href={mapsDirectionsUrl(event.location)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Navigation size={14} />
                      Itinéraire
                    </a>
                  </div>
                </>
              )}

              {event.description && (
                <p className="calendar-event__description">
                  {event.description}
                </p>
              )}

              {event.html_link && (
                <a
                  href={event.html_link}
                  target="_blank"
                  rel="noreferrer"
                >
                  Ouvrir dans Google Calendar
                  <ExternalLink size={14} />
                </a>
              )}
            </article>
          ))}
        </section>
      )}
    </div>
  )
}
