import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowRight, Eye, EyeOff, Plane, ShieldCheck } from 'lucide-react'
import { registerUser } from '../services/auth'

export default function Register() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (password.length < 8) {
      setError('Your password must contain at least 8 characters.')
      return
    }

    if (password !== confirmPassword) {
      setError('Your passwords do not match.')
      return
    }

    setLoading(true)

    try {
      await registerUser({
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
      })

      const flight = searchParams.get('flight')
      const schedule = searchParams.get('schedule')

      const next = flight && schedule
        ? `/login?flight=${encodeURIComponent(flight)}&schedule=${encodeURIComponent(schedule)}`
        : '/login'

      navigate(next, {
        replace: true,
        state: { message: 'Account created successfully. Please sign in.' },
      })
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to create your account. Please try again.',
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

        <span className="eyebrow">START YOUR JOURNEY</span>
        <h1>Create your account</h1>
        <p className="auth-description">
          Join Aqua Airways and make your next journey easier to plan.
        </p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <label htmlFor="full-name">Full name</label>
          <input
            id="full-name"
            type="text"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="Enter your full name"
            autoComplete="name"
            required
          />

          <label htmlFor="register-email">Email address</label>
          <input
            id="register-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            required
          />

          <label htmlFor="register-password">Password</label>
          <div className="password-input">
            <input
              id="register-password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 8 characters"
              autoComplete="new-password"
              minLength={8}
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

          <label htmlFor="confirm-password">Confirm password</label>
          <input
            id="confirm-password"
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            placeholder="Enter your password again"
            autoComplete="new-password"
            required
          />

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>

        <div className="auth-security">
          <ShieldCheck size={17} />
          Your password is securely handled by Aqua Airways.
        </div>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </section>
    </main>
  )
}
