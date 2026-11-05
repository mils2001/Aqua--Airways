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
  ShieldCheck,
  Headphones,
  Globe2,
  UserRound,
  Clock,
  Users,
  AlertCircle,
  LogOut,
} from 'lucide-react'
import { searchFlights, type FlightResult } from './services/api'
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

const destinations = [
  {
    name: 'Mombasa',
    country: 'Kenya',
    description: 'Discover the beautiful Kenyan coast',
    image: 'https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?w=900&q=85',
  },
  {
    name: 'Paris',
    country: 'France',
    description: 'Experience the city of lights',
    image: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=900&q=85',
  },
  {
    name: 'Dubai',
    country: 'United Arab Emirates',
    description: 'Explore extraordinary places',
    image: 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=900&q=85',
  },
  {
    name: 'Cape Town',
    country: 'South Africa',
    description: 'Where nature meets the city',
    image: 'https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=900&q=85',
  },
]

const heroSlides = [
  {
    name: 'Mombasa',
    country: 'Kenya',
    image: 'https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?w=1920&q=85',
  },
  {
    name: 'Paris',
    country: 'France',
    image: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1920&q=85',
  },
  {
    name: 'Dubai',
    country: 'United Arab Emirates',
    image: 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1920&q=85',
  },
  {
    name: 'Cape Town',
    country: 'South Africa',
    image: 'https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=1920&q=85',
  },
]

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [user, setUser] = useState<AuthUser | null>(getStoredUser)

  const closeMenu = () => setMenuOpen(false)

  function handleLogout() {
    logoutUser()
    setUser(null)
    closeMenu()
    window.location.href = '/'
  }

  useEffect(() => {
    const updateUser = () => setUser(getStoredUser())

    window.addEventListener('storage', updateUser)
    window.addEventListener('aqua-auth-change', updateUser)

    return () => {
      window.removeEventListener('storage', updateUser)
      window.removeEventListener('aqua-auth-change', updateUser)
    }
  }, [])

  return (
    <header className="navbar">
      <div className="nav-container">
        <Link to="/" className="brand" onClick={closeMenu}>
          <span className="brand-icon">
            <Plane size={23} />
          </span>
          <span>
            <strong>AQUA</strong>
            <small>AIRWAYS</small>
          </span>
        </Link>

        <button
          className="mobile-menu"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle navigation"
        >
          {menuOpen ? <X /> : <Menu />}
        </button>

        <nav className={menuOpen ? 'nav-links open' : 'nav-links'}>
          <NavLink to="/" onClick={closeMenu}>Home</NavLink>
          <NavLink to="/flights" onClick={closeMenu}>Flights</NavLink>
          <NavLink to="/bookings" onClick={closeMenu}>My Bookings</NavLink>
          <NavLink to="/about" onClick={closeMenu}>About Us</NavLink>
        </nav>

        <div className="nav-actions">
          {user ? (
            <>
              <Link to="/profile" className="login-link" onClick={closeMenu}>
                <UserRound size={17} />
                {user.full_name.split(' ')[0]}
              </Link>
              <button className="nav-register" onClick={handleLogout}>
                Sign out <LogOut size={16} />
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="login-link" onClick={closeMenu}>
                <UserRound size={17} />
                Sign in
              </Link>
              <Link to="/register" className="nav-register" onClick={closeMenu}>
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

  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [date, setDate] = useState(
    new Date().toLocaleDateString('en-CA', {
      timeZone: 'Africa/Nairobi',
    }),
  )

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!origin.trim() || !destination.trim() || !date) return

    const params = new URLSearchParams({
      origin: origin.trim(),
      destination: destination.trim(),
      date,
    })

    navigate(`/flights?${params.toString()}`)
  }

  return (
    <form className="search-form" onSubmit={handleSearch}>
      <div className="search-field">
        <label htmlFor="origin">
          <MapPin size={16} /> FROM
        </label>
        <input
          id="origin"
          value={origin}
          onChange={(event) => setOrigin(event.target.value)}
          placeholder="Departure city"
          required
        />
      </div>

      <div className="search-divider" />

      <div className="search-field">
        <label htmlFor="destination">
          <MapPin size={16} /> TO
        </label>
        <input
          id="destination"
          value={destination}
          onChange={(event) => setDestination(event.target.value)}
          placeholder="Destination city"
          required
        />
      </div>

      <div className="search-divider" />

      <div className="search-field date-field">
        <label htmlFor="travel-date">
          <CalendarDays size={16} /> DEPARTURE
        </label>
        <input
          id="travel-date"
          type="date"
          value={date}
          onChange={(event) => setDate(event.target.value)}
          min={new Date().toLocaleDateString('en-CA', {
            timeZone: 'Africa/Nairobi',
          })}
          required
        />
      </div>

      <button className="search-button" type="submit">
        <Search size={19} />
        Search Flights
      </button>
    </form>
  )
}

function Home() {
  const [activeSlide, setActiveSlide] = useState(0)

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveSlide((current) => (current + 1) % heroSlides.length)
    }, 6000)

    return () => window.clearInterval(timer)
  }, [])

  const slide = heroSlides[activeSlide]

  return (
    <>
      <section className="hero">
        <div
          className="hero-background"
          key={slide.image}
          style={{ backgroundImage: `url("${slide.image}")` }}
        />
        <div className="hero-overlay" />

        <div className="hero-content">
          <div className="hero-tag">
            <Plane size={15} />
            YOUR JOURNEY STARTS HERE
          </div>

          <h1>
            Beyond Every
            <span>Destination.</span>
          </h1>

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
            <div>
              <strong>Comfort</strong>
              <span>Every journey</span>
            </div>
            <div>
              <strong>Reliable</strong>
              <span>Travel experience</span>
            </div>
            <div>
              <strong>Connected</strong>
              <span>More destinations</span>
            </div>
          </div>

          <div className="hero-slide-caption">
            <MapPin size={16} />
            <span>{slide.name}, {slide.country}</span>
          </div>

          <div className="hero-controls" aria-label="Choose destination image">
            {heroSlides.map((item, index) => (
              <button
                key={item.name}
                type="button"
                className={activeSlide === index ? 'hero-dot active' : 'hero-dot'}
                onClick={() => setActiveSlide(index)}
                aria-label={`Show ${item.name}`}
                aria-pressed={activeSlide === index}
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
          {destinations.map((destination) => (
            <article className="destination-card" key={destination.name}>
              <img
                src={destination.image}
                alt={`${destination.name}, ${destination.country}`}
                loading="lazy"
              />
              <div className="destination-overlay">
                <span>{destination.country}</span>
                <h3>{destination.name}</h3>
                <p>{destination.description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="benefits-section">
        <div className="section-heading">
          <span className="eyebrow">THE AQUA EXPERIENCE</span>
          <h2>A better way to plan your journey</h2>
          <p>
            Simple tools and useful information to help you travel
            with confidence.
          </p>
        </div>

        <div className="benefit-grid">
          <article className="benefit-card">
            <span className="benefit-icon"><ShieldCheck /></span>
            <h3>Clear booking information</h3>
            <p>
              View your flight details, travel dates and available
              seats before making your booking.
            </p>
          </article>

          <article className="benefit-card">
            <span className="benefit-icon"><Headphones /></span>
            <h3>Passenger support</h3>
            <p>
              Access your booking information and stay informed
              about your journey.
            </p>
          </article>

          <article className="benefit-card">
            <span className="benefit-icon"><Globe2 /></span>
            <h3>Discover new places</h3>
            <p>
              Explore destinations and find inspiration for your
              next travel experience.
            </p>
          </article>
        </div>
      </section>

      <section className="cta-section">
        <div>
          <span className="eyebrow">YOUR NEXT ADVENTURE</span>
          <h2>The world is waiting.</h2>
          <p>
            Create your Aqua Airways account and start planning
            your journey.
          </p>
        </div>
        <Link to="/register" className="cta-button">
          Create Account <ArrowRight size={18} />
        </Link>
      </section>
    </>
  )
}

function FlightsPage() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)

  const origin = params.get('origin') || ''
  const destination = params.get('destination') || ''
  const date = params.get('date') || ''

  const [results, setResults] = useState<FlightResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [promotionIndex, setPromotionIndex] = useState(0)

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
      image: destinations[1].image,
      label: 'EXPLORE THE WORLD',
    },
    {
      title: 'Plan Your Next Journey',
      description: 'Check available flights, travel dates and schedules.',
      image: destinations[2].image,
      label: 'TRAVEL WITH AQUA',
    },
  ]

  useEffect(() => {
    const timer = window.setInterval(() => {
      setPromotionIndex(current => (current + 1) % promotions.length)
    }, 6000)

    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    if (!origin || !destination || !date) {
      setResults([])
      return
    }

    let active = true

    async function loadFlights() {
      setLoading(true)
      setError('')
      setResults([])

      try {
        const data = await searchFlights(origin, destination, date)
        if (active) setResults(data)
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load flights. Please try again.',
          )
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    loadFlights()

    return () => {
      active = false
    }
  }, [origin, destination, date])

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

  return (
    <main className="flights-page">
      <section className="flights-heading">
        <span className="eyebrow">AQUA AIRWAYS</span>
        <h1>Find your flight</h1>
        <p>Compare available flights and choose your next journey.</p>
      </section>

      <section className="promotion-banner">
        <img
          key={promotions[promotionIndex].image}
          src={promotions[promotionIndex].image}
          alt="Aqua Airways destination highlight"
          onError={event => {
            event.currentTarget.style.display = 'none'
          }}
        />
        <div className="promotion-overlay">
          <span>{promotions[promotionIndex].label}</span>
          <h2>{promotions[promotionIndex].title}</h2>
          <p>{promotions[promotionIndex].description}</p>
          <div className="promotion-controls">
            <button
              type="button"
              aria-label="Previous promotion"
              onClick={() => setPromotionIndex(current =>
                (current - 1 + promotions.length) % promotions.length
              )}
            >
              &#8592;
            </button>
            <div className="promotion-dots">
              {promotions.map((promotion, index) => (
                <button
                  key={promotion.title}
                  type="button"
                  aria-label={`Show promotion ${index + 1}`}
                  className={index === promotionIndex ? 'active' : ''}
                  onClick={() => setPromotionIndex(index)}
                />
              ))}
            </div>
            <button
              type="button"
              aria-label="Next promotion"
              onClick={() => setPromotionIndex(current =>
                (current + 1) % promotions.length
              )}
            >
              &#8594;
            </button>
          </div>
        </div>
      </section>

      {origin && destination && date ? (
        <div className="results-summary">
          <div>
            <span>FROM</span>
            <strong>{origin}</strong>
          </div>
          <ArrowRight />
          <div>
            <span>TO</span>
            <strong>{destination}</strong>
          </div>
          <div>
            <span>DEPARTURE</span>
            <strong>{date}</strong>
          </div>
          <Link to="/#flight-search" className="edit-search">Edit search</Link>
        </div>
      ) : (
        <div className="empty-search">
          <Search size={28} />
          <h2>Ready for your next journey?</h2>
          <p>Enter your departure city, destination and travel date.</p>
          <Link to="/#flight-search" className="primary-button">
            Search Flights <ArrowRight size={17} />
          </Link>
        </div>
      )}

      {loading && (
        <div className="results-message">
          <span className="loading-spinner" />
          <p>Searching available flights...</p>
        </div>
      )}

      {error && (
        <div className="results-error">
          <AlertCircle size={22} />
          <p>{error}. Check that the Flask backend is running.</p>
        </div>
      )}

      {!loading && !error && origin && destination && date && results.length === 0 && (
        <div className="empty-results">
          <Plane size={35} />
          <h2>No flights found</h2>
          <p>
            We couldn't find scheduled flights for this route and date.
            Try another date or destination.
          </p>
          <Link to="/#flight-search" className="primary-button">
            Search another date <ArrowRight size={17} />
          </Link>
        </div>
      )}

      <div className="flight-results">
        {results.map(({ flight, schedule }) => (
          <article className="flight-card" key={schedule.id}>
            {flight.destination_image ? (
              <img
                className="flight-image"
                src={
                  flight.destination_image.startsWith('http')
                    ? flight.destination_image
                    : `${window.location.origin}${flight.destination_image}`
                }
                alt={`${flight.destination} destination`}
                onError={event => {
                  event.currentTarget.style.display = 'none'
                }}
              />
            ) : (
              <div className="flight-image flight-image-placeholder">
                <Globe2 size={35} />
              </div>
            )}

            <div className="flight-card-content">
              <div className="flight-card-top">
                <span className="flight-number">
                  {flight.flight_number}
                </span>
                <span className="flight-status">
                  {schedule.status}
                </span>
              </div>

              <div className="flight-route">
                <div>
                  <strong>{flight.origin_code}</strong>
                  <span>{flight.origin}</span>
                  <time>{formatTime(schedule.departure_at)}</time>
                </div>

                <div className="route-line">
                  <Plane size={17} />
                  <span>Direct flight</span>
                </div>

                <div>
                  <strong>{flight.destination_code}</strong>
                  <span>{flight.destination}</span>
                  <time>{formatTime(schedule.arrival_at)}</time>
                </div>
              </div>

              <div className="flight-details">
                <span>
                  <CalendarDays size={15} />
                  {formatDate(schedule.departure_at)}
                </span>
                <span>
                  <Users size={15} />
                  {schedule.available_seats} seats available
                </span>
                <span>
                  <Clock size={15} />
                  Local time: Nairobi
                </span>
              </div>
            </div>

            <div className="flight-price">
              <span>From</span>
              <strong>
                KSh {Number(flight.base_price).toLocaleString('en-KE')}
              </strong>
              <small>per passenger</small>
              <Link
                to={`/register?flight=${flight.id}&schedule=${schedule.id}`}
                className="select-flight"
              >
                Select flight <ArrowRight size={15} />
              </Link>
            </div>
          </article>
        ))}
      </div>
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
          <span>
            <strong>AQUA</strong>
            <small>AIRWAYS</small>
          </span>
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
        <span>
          © {new Date().getFullYear()} Aqua Airways. All rights reserved.
        </span>
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

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}

export default App
