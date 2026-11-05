
import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CalendarDays, Plane, Users, XCircle, RefreshCw } from 'lucide-react'
import { getToken } from '../services/auth'
import '../Bookings.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

interface Booking {
  id: number
  booking_reference: string
  seats_booked: number
  total_amount: number
  status: string
  created_at: string
  schedule: {
    id: number
    departure_at: string
    arrival_at: string
    status: string
  }
  flight: {
    id: number
    flight_number: string
    origin: string
    destination: string
    origin_code: string
    destination_code: string
  }
}

interface Schedule {
  id: number
  flight_id: number
  flight_number: string
  departure_at: string
  arrival_at: string
  available_seats: number
  status: string
}

interface Flight {
  id: number
  flight_number: string
  origin: string
  destination: string
  origin_code: string
  destination_code: string
  base_price: number
}

interface SelectedFlight {
  schedule: Schedule
  flight: Flight
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()

  if (!token) {
    throw new Error('Please sign in to continue.')
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.message || 'Something went wrong.')
  }

  return data as T
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-KE', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'Africa/Nairobi',
  }).format(new Date(value))
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('en-KE', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Africa/Nairobi',
  }).format(new Date(value))
}

export default function Bookings() {
  const [searchParams] = useSearchParams()
  const scheduleId = searchParams.get('schedule')

  const [bookings, setBookings] = useState<Booking[]>([])
  const [selectedFlight, setSelectedFlight] = useState<SelectedFlight | null>(null)
  const [seats, setSeats] = useState(1)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const loadBookings = useCallback(async () => {
    const data = await apiRequest<{ bookings: Booking[] }>('/api/bookings')
    setBookings(data.bookings)
  }, [])

  useEffect(() => {
    let active = true

    async function loadPage() {
      if (!getToken()) {
        setError('Please sign in to view and manage your bookings.')
        setLoading(false)
        return
      }

      try {
        const data = await apiRequest<{ bookings: Booking[] }>('/api/bookings')

        if (active) {
          setBookings(data.bookings)
        }

        if (scheduleId) {
          const [scheduleData, flightData] = await Promise.all([
            apiRequest<{ schedule: Schedule }>(`/api/schedules/${scheduleId}`),
            fetch(`${API_URL}/api/flights`).then(async response => {
              if (!response.ok) throw new Error('Unable to load flight details.')
              return response.json() as Promise<{ flights: Flight[] }>
            }),
          ])

          const flight = flightData.flights.find(
            item => item.id === scheduleData.schedule.flight_id,
          )

          if (!flight) throw new Error('The selected flight could not be found.')

          if (active) {
            setSelectedFlight({
              schedule: scheduleData.schedule,
              flight,
            })
          }
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unable to load bookings.')
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    loadPage()

    return () => {
      active = false
    }
  }, [scheduleId])

  async function createBooking() {
    if (!selectedFlight) return

    setCreating(true)
    setError('')
    setMessage('')

    try {
      const data = await apiRequest<{ message: string }>('/api/bookings', {
        method: 'POST',
        body: JSON.stringify({
          schedule_id: selectedFlight.schedule.id,
          seats_booked: seats,
        }),
      })

      setMessage(data.message)
      setSelectedFlight(null)
      await loadBookings()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create booking.')
    } finally {
      setCreating(false)
    }
  }

  async function cancelBooking(id: number) {
    const confirmed = window.confirm('Are you sure you want to cancel this booking?')
    if (!confirmed) return

    setError('')
    setMessage('')

    try {
      const data = await apiRequest<{ message: string }>(
        `/api/bookings/${id}/cancel`,
        { method: 'PATCH' },
      )

      setMessage(data.message)
      await loadBookings()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to cancel booking.')
    }
  }

  if (loading) {
    return (
      <main className="bookings-page">
        <p className="booking-loading">Loading your bookings...</p>
      </main>
    )
  }

  return (
    <main className="bookings-page">
      <section className="bookings-heading">
        <span className="eyebrow">AQUA AIRWAYS</span>
        <h1>My Bookings</h1>
        <p>Manage your journeys and keep your travel details in one place.</p>
      </section>

      {error && <div className="booking-alert error">{error}</div>}
      {message && <div className="booking-alert success">{message}</div>}

      {selectedFlight && (
        <section className="booking-create-card">
          <div className="booking-section-heading">
            <div>
              <span className="eyebrow">NEW RESERVATION</span>
              <h2>Confirm your flight</h2>
            </div>
            <button
              className="booking-close"
              type="button"
              onClick={() => setSelectedFlight(null)}
              aria-label="Close booking form"
            >
              <XCircle />
            </button>
          </div>

          <div className="booking-selected-route">
            <div>
              <strong>{selectedFlight.flight.origin_code}</strong>
              <span>{selectedFlight.flight.origin}</span>
              <time>{formatTime(selectedFlight.schedule.departure_at)}</time>
            </div>

            <Plane />

            <div>
              <strong>{selectedFlight.flight.destination_code}</strong>
              <span>{selectedFlight.flight.destination}</span>
              <time>{formatTime(selectedFlight.schedule.arrival_at)}</time>
            </div>
          </div>

          <p>
            Flight {selectedFlight.flight.flight_number} ·{' '}
            {formatDate(selectedFlight.schedule.departure_at)}
          </p>

          <label className="booking-seat-label" htmlFor="booking-seats">
            Number of passengers
          </label>

          <select
            id="booking-seats"
            value={seats}
            onChange={event => setSeats(Number(event.target.value))}
          >
            {Array.from(
              { length: Math.min(10, selectedFlight.schedule.available_seats) },
              (_, index) => index + 1,
            ).map(number => (
              <option key={number} value={number}>
                {number} {number === 1 ? 'passenger' : 'passengers'}
              </option>
            ))}
          </select>

          <div className="booking-total">
            <span>Total amount</span>
            <strong>
              KSh {(selectedFlight.flight.base_price * seats).toLocaleString('en-KE')}
            </strong>
          </div>

          <button
            className="booking-primary-button"
            type="button"
            disabled={creating || selectedFlight.schedule.available_seats < 1}
            onClick={createBooking}
          >
            {creating ? 'Creating booking...' : 'Confirm booking'}
          </button>
          <small>Payment is not included in this step.</small>
        </section>
      )}

      <section className="booking-list-section">
        <div className="booking-list-heading">
          <div>
            <h2>Your journeys</h2>
            <p>{bookings.length} booking(s) found</p>
          </div>

          <button
            type="button"
            className="booking-refresh"
            onClick={() => {
              setLoading(true)
              loadBookings()
                .catch(err => setError(err.message))
                .finally(() => setLoading(false))
            }}
          >
            <RefreshCw size={16} /> Refresh
          </button>
        </div>

        {bookings.length === 0 ? (
          <div className="booking-empty">
            <Plane size={38} />
            <h3>No bookings yet</h3>
            <p>Your confirmed reservations will appear here after you book a flight.</p>
            <Link to="/flights" className="booking-primary-button">
              Explore flights
            </Link>
          </div>
        ) : (
          <div className="booking-list">
            {bookings.map(booking => (
              <article className="booking-card" key={booking.id}>
                <div className="booking-card-top">
                  <span>BOOKING {booking.booking_reference}</span>
                  <span className={`booking-status ${booking.status.toLowerCase()}`}>
                    {booking.status}
                  </span>
                </div>

                <div className="booking-route">
                  <div>
                    <strong>{booking.flight.origin_code}</strong>
                    <span>{booking.flight.origin}</span>
                    <time>{formatTime(booking.schedule.departure_at)}</time>
                  </div>

                  <Plane />

                  <div>
                    <strong>{booking.flight.destination_code}</strong>
                    <span>{booking.flight.destination}</span>
                    <time>{formatTime(booking.schedule.arrival_at)}</time>
                  </div>
                </div>

                <div className="booking-card-details">
                  <span>
                    <CalendarDays size={15} />
                    {formatDate(booking.schedule.departure_at)}
                  </span>
                  <span>
                    <Users size={15} />
                    {booking.seats_booked} passenger(s)
                  </span>
                  <strong>
                    KSh {booking.total_amount.toLocaleString('en-KE')}
                  </strong>
                </div>

                {['PENDING', 'CONFIRMED'].includes(booking.status) && (
                  <button
                    type="button"
                    className="booking-cancel-button"
                    onClick={() => cancelBooking(booking.id)}
                  >
                    Cancel booking
                  </button>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}
