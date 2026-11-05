
import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react'
import {
  Camera,
  UserRound,
  Mail,
  ShieldCheck,
  Coins,
  Gift,
  CalendarDays,
  CheckCircle2,
  LoaderCircle,
  Save,
  Plane,
  Sparkles,
} from 'lucide-react'
import { getToken } from '../services/auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

interface ProfileUser {
  id: number
  full_name: string
  email: string
  role: string
  profile_image: string | null
  created_at: string
}

interface RewardClaim {
  id: number
  points: number
  claim_date: string
  created_at: string
}

interface Rewards {
  total_points: number
  daily_reward: number
  claimed_today: boolean
  next_claim_date: string | null
  claims: RewardClaim[]
}

export default function Profile() {
  const [user, setUser] = useState<ProfileUser | null>(null)
  const [rewards, setRewards] = useState<Rewards | null>(null)
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [claiming, setClaiming] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const token = getToken()

  const imageUrl = user?.profile_image
    ? user.profile_image.startsWith('http')
      ? user.profile_image
      : `${API_URL}${user.profile_image}`
    : null

  async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(data.message || 'Something went wrong.')
    }

    return data as T
  }

  async function loadProfile() {
    if (!token) {
      setError('Please log in to view your profile.')
      setLoading(false)
      return
    }

    try {
      const [profileData, rewardData] = await Promise.all([
        apiRequest<{ user: ProfileUser }>('/api/profile'),
        apiRequest<{ rewards: Rewards }>('/api/rewards'),
      ])

      setUser(profileData.user)
      setFullName(profileData.user.full_name)
      setRewards(rewardData.rewards)

      localStorage.setItem('aqua_user', JSON.stringify(profileData.user))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load your profile.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProfile()
  }, [])

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')
    setError('')
    setSaving(true)

    try {
      const data = await apiRequest<{ user: ProfileUser; message: string }>(
        '/api/profile',
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ full_name: fullName }),
        },
      )

      setUser(data.user)
      setFullName(data.user.full_name)
      localStorage.setItem('aqua_user', JSON.stringify(data.user))
      setMessage(data.message)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update your profile.')
    } finally {
      setSaving(false)
    }
  }

  async function handlePhotoUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    setMessage('')
    setError('')

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setError('Choose a JPEG, PNG or WEBP image.')
      event.target.value = ''
      return
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('Image must be smaller than 5 MB.')
      event.target.value = ''
      return
    }

    const formData = new FormData()
    formData.append('photo', file)

    setUploading(true)

    try {
      const data = await apiRequest<{ profile_image: string; message: string }>(
        '/api/profile/photo',
        {
          method: 'POST',
          body: formData,
        },
      )

      setUser((current) =>
        current ? { ...current, profile_image: data.profile_image } : current,
      )
      setMessage(data.message)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Photo upload failed.')
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  async function handleClaim() {
    setMessage('')
    setError('')
    setClaiming(true)

    try {
      const data = await apiRequest<{ rewards: Rewards; message: string }>(
        '/api/rewards/claim',
        { method: 'POST' },
      )

      setRewards(data.rewards)
      setMessage(data.message)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not claim your points.')
      try {
        const data = await apiRequest<{ rewards: Rewards }>('/api/rewards')
        setRewards(data.rewards)
      } catch {
        // Keep the existing rewards display if refreshing fails.
      }
    } finally {
      setClaiming(false)
    }
  }

  if (loading) {
    return (
      <div className="profile-loading">
        <LoaderCircle className="spin" size={30} />
        <p>Loading your passenger profile...</p>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="profile-page">
        <div className="profile-notice">
          <UserRound size={32} />
          <h2>Profile unavailable</h2>
          <p>{error || 'Please log in to continue.'}</p>
          <a href="/login" className="profile-primary-btn">Go to Login</a>
        </div>
      </div>
    )
  }

  return (
    <main className="profile-page">
      <div className="profile-heading">
        <div>
          <span className="profile-eyebrow">PASSENGER ACCOUNT</span>
          <h1>My Profile</h1>
          <p>Manage your account, membership and AQUA rewards.</p>
        </div>
        <div className="profile-status">
          <CheckCircle2 size={16} />
          Active passenger
        </div>
      </div>

      {message && (
        <div className="profile-message success">
          <CheckCircle2 size={18} />
          {message}
        </div>
      )}

      {error && (
        <div className="profile-message error">
          {error}
        </div>
      )}

      <section className="profile-layout">
        <div className="profile-main-column">
          <section className="profile-panel">
            <div className="profile-panel-heading">
              <div>
                <h2>Personal Information</h2>
                <p>Your passenger account details</p>
              </div>
              <UserRound size={22} />
            </div>

            <div className="profile-avatar-section">
              <div className="profile-avatar">
                {imageUrl ? (
                  <img src={imageUrl} alt="Passenger profile" />
                ) : (
                  <UserRound size={48} />
                )}
              </div>

              <div className="profile-photo-info">
                <h3>Profile photograph</h3>
                <p>JPEG, PNG or WEBP. Maximum 5 MB.</p>
                <label className="profile-upload-btn">
                  {uploading ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <Camera size={16} />
                  )}
                  {uploading ? 'Uploading...' : 'Change photo'}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handlePhotoUpload}
                    disabled={uploading}
                    hidden
                  />
                </label>
              </div>
            </div>

            <form onSubmit={handleSave} className="profile-form">
              <label>
                Full name
                <div className="profile-input-wrap">
                  <UserRound size={18} />
                  <input
                    type="text"
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    maxLength={120}
                    required
                  />
                </div>
              </label>

              <label>
                Email address
                <div className="profile-input-wrap disabled">
                  <Mail size={18} />
                  <input type="email" value={user.email} disabled />
                </div>
                <small>Email address cannot be changed here.</small>
              </label>

              <label>
                Membership type
                <div className="profile-input-wrap disabled">
                  <ShieldCheck size={18} />
                  <input value={user.role.toUpperCase()} disabled />
                </div>
              </label>

              <button type="submit" className="profile-primary-btn" disabled={saving}>
                {saving ? <LoaderCircle className="spin" size={17} /> : <Save size={17} />}
                {saving ? 'Saving...' : 'Save changes'}
              </button>
            </form>
          </section>
        </div>

        <div className="profile-side-column">
          <section className="aqua-membership-card">
            <div className="membership-card-top">
              <div className="membership-brand">
                <Plane size={22} />
                <span>AQUA AIRWAYS</span>
              </div>
              <span className="membership-chip">MEMBER</span>
            </div>

            <div className="membership-card-middle">
              <span>PASSENGER NAME</span>
              <h2>{user.full_name}</h2>
              <span>MEMBERSHIP NUMBER</span>
              <h3>AQ-{String(user.id).padStart(6, '0')}</h3>
            </div>

            <div className="membership-card-bottom">
              <span>BEYOND EVERY DESTINATION</span>
              <Sparkles size={22} />
            </div>
          </section>

          <section className="profile-rewards-panel">
            <div className="rewards-heading">
              <div className="rewards-icon">
                <Coins size={24} />
              </div>
              <div>
                <h2>AQUA Rewards</h2>
                <p>Your passenger loyalty points</p>
              </div>
            </div>

            <div className="rewards-balance">
              <span>AVAILABLE POINTS</span>
              <strong>{rewards?.total_points ?? 0}</strong>
              <small>AQUA Points</small>
            </div>

            <div className="daily-reward">
              <div>
                <h3><Gift size={17} /> Daily reward</h3>
                <p>Claim your daily 10 AQUA Points.</p>
              </div>
              <span>+10</span>
            </div>

            <button
              className="profile-claim-btn"
              onClick={handleClaim}
              disabled={claiming || rewards?.claimed_today}
            >
              {claiming ? (
                <LoaderCircle className="spin" size={17} />
              ) : rewards?.claimed_today ? (
                <CheckCircle2 size={17} />
              ) : (
                <Gift size={17} />
              )}
              {claiming
                ? 'Claiming...'
                : rewards?.claimed_today
                  ? 'Already claimed today'
                  : 'Claim daily points'}
            </button>

            <p className="rewards-disclaimer">
              AQUA Points are in-app loyalty rewards and are not cryptocurrency
              or cash.
            </p>
          </section>

          <section className="profile-history-panel">
            <div className="profile-panel-heading">
              <div>
                <h2>Reward history</h2>
                <p>Your recent daily claims</p>
              </div>
              <CalendarDays size={21} />
            </div>

            {rewards?.claims.length ? (
              <div className="reward-history-list">
                {rewards.claims.map((claim) => (
                  <div className="reward-history-item" key={claim.id}>
                    <div className="history-gift">
                      <Gift size={18} />
                    </div>
                    <div>
                      <strong>Daily reward</strong>
                      <small>{claim.claim_date}</small>
                    </div>
                    <span>+{claim.points} pts</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-rewards">
                <Gift size={25} />
                <p>No reward claims yet.</p>
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  )
}
