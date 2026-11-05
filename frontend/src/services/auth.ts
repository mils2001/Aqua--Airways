
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

const TOKEN_KEY = 'aqua_access_token'
const USER_KEY = 'aqua_user'

export interface AuthUser {
  id: number
  full_name: string
  email: string
  role: string
  is_active: boolean
}

interface AuthResponse {
  status: string
  message: string
  access_token?: string
  user?: AuthUser
}

interface ProfileResponse {
  status: string
  user: AuthUser
}

async function authRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.message || 'Something went wrong.')
  }

  return data as T
}

export async function registerUser(details: {
  full_name: string
  email: string
  password: string
}): Promise<AuthResponse> {
  return authRequest<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(details),
  })
}

export async function loginUser(details: {
  email: string
  password: string
}): Promise<AuthResponse> {
  const data = await authRequest<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(details),
  })

  if (!data.access_token || !data.user) {
    throw new Error('The server returned an invalid login response.')
  }

  localStorage.setItem(TOKEN_KEY, data.access_token)
  localStorage.setItem(USER_KEY, JSON.stringify(data.user))

  window.dispatchEvent(new Event('aqua-auth-change'))

  return data
}

export async function getCurrentUser(): Promise<AuthUser> {
  const token = getToken()

  if (!token) {
    throw new Error('You are not logged in.')
  }

  const data = await authRequest<ProfileResponse>('/api/auth/profile', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  localStorage.setItem(USER_KEY, JSON.stringify(data.user))

  return data.user
}

export function getStoredUser(): AuthUser | null {
  const storedUser = localStorage.getItem(USER_KEY)

  if (!storedUser) return null

  try {
    return JSON.parse(storedUser) as AuthUser
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function logoutUser(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)

  window.dispatchEvent(new Event('aqua-auth-change'))
}

