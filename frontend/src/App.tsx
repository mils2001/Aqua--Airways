
import { useEffect, useState, type FormEvent } from 'react'
import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  Link,
  useNavigate,
  useLocation,
} from 'react-router-dom'
import {
  Plane,
  Menu,
  X,
  Search,
  MapPin,
  CalendarDays,
  ArrowRight,
  ArrowLeftRight,
  ShieldCheck,
  Headphones,
  Globe2,
  UserRound,
  Clock,
  Users,
  AlertCircle,
  LogOut,
  PlaneLanding,
} from 'lucide-react'

import {
  getFlights,
  searchFlights,
  type Flight,
  type FlightResult,
} from './services/api'

import {
  getStoredUser,
  logoutUser,
  type AuthUser,
} from './services/auth'

import Register from './pages/Register'
import Login from './pages/Login'
import Bookings from './pages/Bookings'
import Profile from './pages/Profile'
import './App.css'

const getNairobiDate = (offset = 0) => {
  const date = new Date()
  date.setDate(date.getDate() + offset)

  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Africa/Nairobi',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date)
}

const destinations = [
  ['Mombasa', 'Kenya', 'Discover the beautiful Kenyan coast', '/images/destinations/mombasa.jpg'],
  ['Paris', 'France', 'Experience the city of lights', '/images/destinations/paris.jpg'],
  ['Dubai', 'United Arab Emirates', 'Explore extraordinary places', '/images/destinations/dubai.jpg'],
  ['Zanzibar', 'Tanzania', 'Discover beautiful island beaches', '/images/destinations/zanzibar.jpg'],
]

const slides = destinations.map(([name, country, , image]) => ({
  name,
  country,
  image,
}))

const promotions = [
  {
    title: 'Discover the Kenyan Coast',
    description: 'Explore Mombasa and experience the beauty of Diani Beach.',
    image: '/images/destinations/mombasa.jpg',
    label: 'DESTINATION HIGHLIGHT',
  },
  {
    title: 'Beyond Every Destination',
    description: 'Your next journey begins with Aqua Airways.',
    image: '/images/destinations/paris.jpg',
    label: 'EXPLORE THE WORLD',
  },
  {
    title: 'Plan Your Next Journey',
    description: 'Check available flights, dates and schedules.',
    image: '/images/destinations/dubai.jpg',
    label: 'TRAVEL WITH AQUA',
  },
]

const navLinks = [
  ['Home', '/'],
  ['Flights', '/flights'],
  ['My Bookings', '/bookings'],
  ['About Us', '/about'],
]

const destinationImages: Record<string, string> = {
  nairobi: 'nairobi',
  mombasa: 'mombasa',
  kisumu: 'kisumu',
  eldoret: 'eldoret',
  malindi: 'malindi',
  ukunda: 'ukunda',
  lamu: 'lamu',
  lagos: 'lagos',
  kigali: 'kigali',
  kampala: 'kampala',
  'dar es salaam': 'dar-es-salaam',
  'addis ababa': 'addis-ababa',
  johannesburg: 'johannesburg',
  cairo: 'cairo',
  zanzibar: 'zanzibar',
  london: 'london',
  paris: 'paris',
  dubai: 'dubai',
  doha: 'doha',
  'new york': 'new-york',
  istanbul: 'istanbul',
  mumbai: 'mumbai',
  amsterdam: 'amsterdam',
}

function getDestinationImage(destination: string) {
  const imageName = destinationImages[destination.trim().toLowerCase()]

  return imageName
    ? `/images/destinations/${imageName}.jpg`
    : '/images/destinations/nairobi.jpg'
}

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [user, setUser] = useState<AuthUser | null>(getStoredUser)

  const closeMenu = () => setMenuOpen(false)

  useEffect(() => {
    const update = () => setUser(getStoredUser())

    window.addEventListener('storage', update)
    window.addEventListener('aqua-auth-change', update)

    return () => {
      window.removeEventListener('storage', update)
      window.removeEventListener('aqua-auth-change', update)
    }
  }, [])

  function signOut() {
    logoutUser()
    setUser(null)
    closeMenu()
    window.location.href = '/'
  }

  return (
    <header className="navbar">
      <div className="nav-container">
        <Link to="/" className="brand" onClick={closeMenu}>
          <span className="brand-icon"><Plane size={23} /></span>
          <span><strong>AQUA</strong><small>AIRWAYS</small></span>
        </Link>

        <button
          className="mobile-menu"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle navigation"
        >
          {menuOpen ? <X /> : <Menu />}
        </button>

        <nav className={menuOpen ? 'nav-links open' : 'nav-links'}>
          {navLinks.map(([label, path]) => (
            <NavLink key={path} to={path} onClick={closeMenu}>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="nav-actions">
          {user ? (
            <>
              <Link to="/profile" className="login-link">
                <UserRound size={17} /> {user.full_name.split(' ')[0]}
              </Link>
              <button className="nav-register" onClick={signOut}>
                Sign out <LogOut size={16} />
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="login-link">
                <UserRound size={17} /> Sign in
              </Link>
              <Link to="/register" className="nav-register">
                Get Started <ArrowRight size={16} />
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

function FlightSearch() {
  const navigate = useNavigate()

  const [flights, setFlights] = useState<Flight[]>([])
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [date, setDate] = useState(getNairobiDate(1))
  const [returnDate, setReturnDate] = useState(getNairobiDate(2))
  const [tripType, setTripType] = useState<'one-way' | 'round-trip'>('one-way')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    getFlights()
      .then(data => {
        if (active) setFlights(data)
      })
      .catch(() => {
        if (active) setError('Unable to load flight routes.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  const origins = [...new Set(flights.map(flight => flight.origin))].sort()
  const destinationsList = [...new Set(flights.map(flight => flight.destination))].sort()

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!date || (tripType === 'round-trip' && returnDate < date)) return

    const params = new URLSearchParams({
      origin,
      destination,
      date,
      tripType,
    })

    if (tripType === 'round-trip') {
      params.set('returnDate', returnDate)
    }

    navigate(`/flights?${params}`)
  }

  return (
    <div className="flight-search-wrapper">
      <div className="trip-type-switch">
        <button
          type="button"
          className={tripType === 'one-way' ? 'active' : ''}
          onClick={() => setTripType('one-way')}
        >
          One way
        </button>

        <button
          type="button"
          className={tripType === 'round-trip' ? 'active' : ''}
          onClick={() => setTripType('round-trip')}
        >
          <ArrowLeftRight size={16} /> Return trip
        </button>
      </div>

      <form className="search-form" onSubmit={handleSearch}>
        <div className="search-field">
          <label htmlFor="origin"><MapPin size={16} /> FROM</label>
          <select
            id="origin"
            value={origin}
            onChange={event => setOrigin(event.target.value)}
          >
            <option value="">Any departure city</option>
            {origins.map(city => <option key={city} value={city}>{city}</option>)}
          </select>
        </div>

        <div className="search-divider" />

        <div className="search-field">
          <label htmlFor="destination"><MapPin size={16} /> TO</label>
          <select
            id="destination"
            value={destination}
            onChange={event => setDestination(event.target.value)}
          >
            <option value="">Any destination</option>
            {destinationsList.map(city => <option key={city} value={city}>{city}</option>)}
          </select>
        </div>

        <div className="search-divider" />

        <div className="search-field date-field">
          <label htmlFor="travel-date"><CalendarDays size={16} /> DEPARTURE</label>
          <input
            id="travel-date"
            type="date"
            min={getNairobiDate(1)}
            value={date}
            onChange={event => {
              setDate(event.target.value)
              if (returnDate < event.target.value) {
                setReturnDate(event.target.value)
              }
            }}
            required
          />
        </div>

        {tripType === 'round-trip' && (
          <>
            <div className="search-divider" />
            <div className="search-field date-field">
              <label htmlFor="return-date"><CalendarDays size={16} /> RETURN</label>
              <input
                id="return-date"
                type="date"
                min={date}
                value={returnDate}
                onChange={event => setReturnDate(event.target.value)}
                required
              />
            </div>
          </>
        )}

        <button className="search-button" type="submit" disabled={loading}>
          <Search size={19} /> Search Flights
        </button>
      </form>

      <div className="search-bottom-line">
        <span>
          {loading ? 'Loading available routes...' : <><Plane size={14} /> {flights.length} routes available</>}
        </span>

        {error && <span className="route-load-error">{error}</span>}

        <button
          className="browse-routes-link"
          type="button"
          onClick={() => navigate(`/flights?date=${date}`)}
        >
          Browse all routes <ArrowRight size={14} />
        </button>
      </div>
    </div>
  )
}

function Home() {
  const [active, setActive] = useState(0)
  const slide = slides[active]

  useEffect(() => {
    const timer = window.setInterval(
      () => setActive(current => (current + 1) % slides.length),
      6000,
    )

    return () => window.clearInterval(timer)
  }, [])

  return (
    <>
      <section className="hero">
        <div
          className="hero-background"
          style={{ backgroundImage: `url("${slide.image}")` }}
        />
        <div className="hero-overlay" />

        <div className="hero-content">
          <div className="hero-tag">
            <Plane size={15} /> YOUR JOURNEY STARTS HERE
          </div>

          <h1>Beyond Every <span>Destination.</span></h1>

          <p>
            Discover new places, create unforgettable memories and travel
            with confidence. Your next adventure begins with Aqua Airways.
          </p>

          <div className="hero-buttons">
            <a href="#flight-search" className="primary-button">
              Book Your Flight <ArrowRight size={18} />
            </a>
            <Link to="/about" className="secondary-button">
              Discover Aqua
            </Link>
          </div>

          <div className="hero-stats">
            <div><strong>Comfort</strong><span>Every journey</span></div>
            <div><strong>Reliable</strong><span>Travel experience</span></div>
            <div><strong>Connected</strong><span>More destinations</span></div>
          </div>

          <div className="hero-slide-caption">
            <MapPin size={16} /> {slide.name}, {slide.country}
          </div>

          <div className="hero-controls">
            {slides.map((item, index) => (
              <button
                key={item.name}
                className={active === index ? 'hero-dot active' : 'hero-dot'}
                onClick={() => setActive(index)}
                aria-label={`Show ${item.name}`}
              />
            ))}
          </div>
        </div>

        <div className="hero-decoration">
          <Plane size={150} strokeWidth={0.6} />
        </div>
      </section>

      <section className="search-section" id="flight-search">
        <div className="section-heading">
          <span className="eyebrow">PLAN YOUR JOURNEY</span>
          <h2>Where would you like to go?</h2>
          <p>Find a flight that takes you where you want to be.</p>
        </div>
        <FlightSearch />
      </section>

      <section className="destinations-section">
        <div className="section-heading">
          <span className="eyebrow">EXPLORE THE WORLD</span>
          <h2>Destinations worth discovering</h2>
          <p>Find inspiration for your next adventure.</p>
        </div>

        <div className="destination-grid">
          {destinations.map(([name, country, description, image]) => (
            <article className="destination-card" key={name}>
              <img src={image} alt={`${name}, ${country}`} loading="lazy" />
              <div className="destination-overlay">
                <span>{country}</span>
                <h3>{name}</h3>
                <p>{description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="benefits-section">
        <div className="section-heading">
          <span className="eyebrow">THE AQUA EXPERIENCE</span>
          <h2>A better way to plan your journey</h2>
          <p>Simple tools and useful information to help you travel with confidence.</p>
        </div>

        <div className="benefit-grid">
          <article className="benefit-card">
            <span className="benefit-icon"><ShieldCheck /></span>
            <h3>Clear booking information</h3>
            <p>View flight details, travel dates and available seats before booking.</p>
          </article>

          <article className="benefit-card">
            <span className="benefit-icon"><Headphones /></span>
            <h3>Passenger support</h3>
            <p>Access your booking information and stay informed about your journey.</p>
          </article>

          <article className="benefit-card">
            <span className="benefit-icon"><Globe2 /></span>
            <h3>Discover new places</h3>
            <p>Explore destinations and find inspiration for your next adventure.</p>
          </article>
        </div>
      </section>

      <section className="cta-section">
        <div>
          <span className="eyebrow">YOUR NEXT ADVENTURE</span>
          <h2>The world is waiting.</h2>
          <p>Create your Aqua Airways account and start planning your journey.</p>
        </div>
        <Link to="/register" className="cta-button">
          Create Account <ArrowRight size={18} />
        </Link>
      </section>
    </>
  )
}

const formatTime = (value: string) =>
  new Intl.DateTimeFormat('en-KE', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Africa/Nairobi',
  }).format(new Date(value))

const formatDate = (value: string) =>
  new Intl.DateTimeFormat('en-KE', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'Africa/Nairobi',
  }).format(new Date(value))

function getDuration(start: string, end: string) {
  const minutes = Math.max(
    0,
    Math.round(
      (new Date(end).getTime() - new Date(start).getTime()) / 60000,
    ),
  )

  const hours = Math.floor(minutes / 60)

  return hours ? `${hours}h ${minutes % 60}m` : `${minutes}m`
}

function FlightCard({ result }: { result: FlightResult }) {
  const { flight, schedule } = result

  return (
    <article className="flight-card enhanced-flight-card">
      <img
        className="flight-image"
        src={getDestinationImage(flight.destination)}
        alt={`${flight.destination} destination`}
        loading="lazy"
        onError={event => {
          event.currentTarget.src = '/images/destinations/nairobi.jpg'
        }}
      />

      <div className="flight-card-content">
        <div className="flight-card-top">
          <span className="flight-number">{flight.flight_number}</span>
          <span className="flight-status">{schedule.status}</span>
        </div>

        <div className="flight-route enhanced-flight-route">
          <div className="timeline-stop">
            <span className="timeline-time">{formatTime(schedule.departure_at)}</span>
            <strong>{flight.origin_code}</strong>
            <span>{flight.origin}</span>
            <small>Departure</small>
          </div>

          <div className="flight-timeline">
            <span className="timeline-duration">
              {getDuration(schedule.departure_at, schedule.arrival_at)}
            </span>

            <div className="timeline-track">
              <span className="timeline-dot" />
              <span className="timeline-line" />
              <Plane size={19} />
              <span className="timeline-line" />
              <span className="timeline-dot" />
            </div>

            <span className="timeline-direct">Non-stop flight</span>
          </div>

          <div className="timeline-stop timeline-arrival">
            <span className="timeline-time">{formatTime(schedule.arrival_at)}</span>
            <strong>{flight.destination_code}</strong>
            <span>{flight.destination}</span>
            <small>Arrival</small>
          </div>
        </div>

        <div className="flight-details">
          <span><CalendarDays size={15} /> {formatDate(schedule.departure_at)}</span>
          <span><Users size={15} /> {schedule.available_seats} seats available</span>
          <span><Clock size={15} /> East Africa time</span>
        </div>
      </div>

      <div className="flight-price">
        <span>Ticket price</span>
        <strong>KSh {Number(flight.base_price).toLocaleString('en-KE')}</strong>
        <small>per passenger</small>

        <Link
          to={`/register?flight=${flight.id}&schedule=${schedule.id}`}
          className="select-flight"
        >
          Select flight <ArrowRight size={15} />
        </Link>
      </div>
    </article>
  )
}

function FlightResultsGroup({
  title,
  date,
  results,
}: {
  title: string
  date: string
  results: FlightResult[]
}) {
  return (
    <section className="flight-results-group">
      <div className="flight-group-heading">
        <div>
          <span className="eyebrow">{title}</span>
          <h2>{formatDate(`${date}T12:00:00`)}</h2>
        </div>

        <span className="route-count">
          {results.length} {results.length === 1 ? 'flight' : 'flights'}
        </span>
      </div>

      <div className="flight-results">
        {results.map(result => (
          <FlightCard key={result.schedule.id} result={result} />
        ))}
      </div>
    </section>
  )
}

function FlightsPage() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)

  const origin = params.get('origin') || ''
  const destination = params.get('destination') || ''

  // Automatically search tomorrow when the user opens /flights directly.
  const date = params.get('date') || getNairobiDate(1)

  const tripType = params.get('tripType') || 'one-way'
  const returnDate = params.get('returnDate') || ''

  const [results, setResults] = useState<FlightResult[]>([])
  const [returnResults, setReturnResults] = useState<FlightResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [promotion, setPromotion] = useState(0)

  useEffect(() => {
    const timer = window.setInterval(
      () => setPromotion(current => (current + 1) % promotions.length),
      6000,
    )

    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    let active = true

    async function load() {
      setLoading(true)
      setError('')
      setResults([])
      setReturnResults([])

      try {
        const outbound = await searchFlights(origin, destination, date)

        let inbound: FlightResult[] = []

        if (tripType === 'round-trip' && returnDate && origin && destination) {
          inbound = await searchFlights(destination, origin, returnDate)
        }

        if (active) {
          setResults(outbound)
          setReturnResults(inbound)
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load flights.',
          )
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    load()

    return () => {
      active = false
    }
  }, [origin, destination, date, tripType, returnDate])

  const hasRoute = Boolean(origin || destination)
  const promo = promotions[promotion]

  return (
    <main className="flights-page">
      <section className="flights-heading">
        <span className="eyebrow">AQUA AIRWAYS</span>
        <h1>Find your flight</h1>
        <p>Compare available flights and choose your next journey.</p>
      </section>

      <section className="promotion-banner">
        <img
          key={promo.image}
          src={promo.image}
          alt="Aqua Airways destination"
          onError={event => {
            event.currentTarget.style.display = 'none'
          }}
        />

        <div className="promotion-overlay">
          <span>{promo.label}</span>
          <h2>{promo.title}</h2>
          <p>{promo.description}</p>

          <div className="promotion-controls">
            <button
              onClick={() =>
                setPromotion(current =>
                  (current - 1 + promotions.length) % promotions.length,
                )
              }
            >
              &#8592;
            </button>

            <div className="promotion-dots">
              {promotions.map((item, index) => (
                <button
                  key={item.title}
                  className={index === promotion ? 'active' : ''}
                  aria-label={`Show promotion ${index + 1}`}
                  onClick={() => setPromotion(index)}
                />
              ))}
            </div>

            <button
              onClick={() =>
                setPromotion(current => (current + 1) % promotions.length)
              }
            >
              &#8594;
            </button>
          </div>
        </div>
      </section>

      <div className="results-summary">
        <div>
          <span>FROM</span>
          <strong>{origin || 'All cities'}</strong>
        </div>

        <ArrowRight />

        <div>
          <span>TO</span>
          <strong>{destination || 'All destinations'}</strong>
        </div>

        <div>
          <span>DEPARTURE</span>
          <strong>{date}</strong>
        </div>

        {tripType === 'round-trip' && returnDate && (
          <div>
            <span>RETURN</span>
            <strong>{returnDate}</strong>
          </div>
        )}

        <Link to="/#flight-search" className="edit-search">
          Edit search
        </Link>
      </div>

      {loading && (
        <div className="results-message">
          <span className="loading-spinner" />
          <p>Searching available flights for {date}...</p>
        </div>
      )}

      {error && (
        <div className="results-error">
          <AlertCircle size={22} />
          <p>{error}. Check that the Flask backend is running.</p>
        </div>
      )}

      {!loading && !error && results.length === 0 && (
        <div className="empty-results">
          <Plane size={35} />
          <h2>No outbound flights found</h2>
          <p>
            No scheduled flights are available for {date}.
            Try another date or choose a different route.
          </p>

          <Link to="/#flight-search" className="primary-button">
            Change search <ArrowRight size={17} />
          </Link>
        </div>
      )}

      {!loading && !error && results.length > 0 && (
        <FlightResultsGroup
          title="OUTBOUND JOURNEY"
          date={date}
          results={results}
        />
      )}

      {!loading &&
        !error &&
        tripType === 'round-trip' &&
        returnDate &&
        hasRoute &&
        (returnResults.length > 0 ? (
          <FlightResultsGroup
            title="RETURN JOURNEY"
            date={returnDate}
            results={returnResults}
          />
        ) : (
          <div className="empty-results return-empty">
            <PlaneLanding size={32} />
            <h2>No return flights found</h2>
            <p>
              No scheduled flights were found for the return date {returnDate}.
            </p>
          </div>
        ))}

      {!loading && !error && !hasRoute && results.length > 0 && (
        <p className="all-routes-note">
          Showing available flights across all Aqua Airways routes.
        </p>
      )}
    </main>
  )
}

function PagePlaceholder({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <main className="placeholder-page">
      <span className="eyebrow">AQUA AIRWAYS</span>
      <h1>{title}</h1>
      <p>{description}</p>
      <Link to="/" className="primary-button">
        Back to Home <ArrowRight size={17} />
      </Link>
    </main>
  )
}

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-main">
        <Link to="/" className="brand footer-brand">
          <span className="brand-icon"><Plane size={22} /></span>
          <span><strong>AQUA</strong><small>AIRWAYS</small></span>
        </Link>

        <p>Beyond Every Destination.</p>

        <div className="footer-links">
          <Link to="/flights">Flights</Link>
          <Link to="/bookings">My Bookings</Link>
          <Link to="/profile">My Profile</Link>
          <Link to="/about">About Us</Link>
          <Link to="/login">Sign In</Link>
        </div>
      </div>

      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} Aqua Airways. All rights reserved.</span>
        <span>Beyond Every Destination.</span>
      </div>
    </footer>
  )
}

function AppLayout() {
  return (
    <>
      <Navbar />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/flights" element={<FlightsPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/bookings" element={<Bookings />} />
        <Route path="/profile" element={<Profile />} />

        <Route
          path="/about"
          element={
            <PagePlaceholder
              title="Beyond Every Destination"
              description="Discover the Aqua Airways travel experience."
            />
          }
        />

        <Route
          path="/admin"
          element={
            <PagePlaceholder
              title="Admin Dashboard"
              description="Manage airline operations here."
            />
          }
        />

        <Route
          path="*"
          element={
            <PagePlaceholder
              title="Page not found"
              description="The page you requested could not be found."
            />
          }
        />
      </Routes>

      <Footer />
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}
