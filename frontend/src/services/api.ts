const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

export interface Flight {
  id: number
  flight_number: string
  origin: string
  destination: string
  origin_code: string
  destination_code: string
  base_price: number
  total_seats: number
  destination_image: string | null
}

export interface FlightSchedule {
  id: number
  flight_id: number
  flight_number: string
  departure_at: string
  arrival_at: string
  available_seats: number
  status: string
}

export interface FlightResult {
  flight: Flight
  schedule: FlightSchedule
}

interface FlightsResponse {
  status: string
  flights: Flight[]
}

interface SchedulesResponse {
  status: string
  schedules: FlightSchedule[]
}

async function request<T>(url: string): Promise<T> {
  const response = await fetch(`${API_URL}${url}`)

  if (!response.ok) {
    throw new Error(`API request failed (${response.status})`)
  }

  return response.json() as Promise<T>
}

export async function searchFlights(
  origin: string,
  destination: string,
  date: string,
): Promise<FlightResult[]> {
  const flightData = await request<FlightsResponse>('/api/flights')

  const matchingFlights = flightData.flights.filter((flight) => {
    return (
      flight.origin.toLowerCase().includes(origin.toLowerCase()) &&
      flight.destination.toLowerCase().includes(destination.toLowerCase())
    )
  })

  const scheduleResults = await Promise.all(
    matchingFlights.map(async (flight) => {
      const data = await request<SchedulesResponse>(
        `/api/flights/${flight.id}/schedules`,
      )

      return data.schedules
        .filter((schedule) => {
          const departureDate = new Intl.DateTimeFormat('en-CA', {
            timeZone: 'Africa/Nairobi',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
          }).format(new Date(schedule.departure_at))

          return (
            departureDate === date &&
            schedule.status === 'SCHEDULED' &&
            schedule.available_seats > 0
          )
        })
        .map((schedule) => ({
          flight,
          schedule,
        }))
    }),
  )

  return scheduleResults.flat()
}
