import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowRight, Eye, EyeOff, Plane, ShieldCheck } from 'lucide-react'
import { loginUser } from '../services/auth'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const successMessage = (location.state as { message?: string } | null)?.message

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      await loginUser({
        email: email.trim().toLowerCase(),
        password,
      })

      const flight = searchParams.get('flight')
      const schedule = searchParams.get('schedule')

      if (flight && schedule) {
        navigate(`/bookings?flight=${encodeURIComponent(flight)}&schedule=${encodeURIComponent(schedule)}`, {
          replace: true,
        })
      } else {
        navigate('/profile', { replace: true })
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to sign in. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand">
          <span className="brand-icon"><Plane size={25} /></span>
          <span><strong>AQUA</strong><small>AIRWAYS</small></span>
        </div>

        <span className="eyebrow">WELCOME BACK</span>
        <h1>Sign in to Aqua</h1>
        <p className="auth-description">
          Access your account and continue planning your journey.
        </p>

        {successMessage && (
          <div className="auth-success">{successMessage}</div>
        )}

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <label htmlFor="login-email">Email address</label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            required
          />

          <label htmlFor="login-password">Password</label>
          <div className="password-input">
            <input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
            </button>
          </div>

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>

        <div className="auth-security">
          <ShieldCheck size={17} />
          Your account is protected by secure authentication.
        </div>

        <p className="auth-switch">
          New to Aqua Airways? <Link to="/register">Create an account</Link>
        </p>
      </section>
    </main>
  )
}
