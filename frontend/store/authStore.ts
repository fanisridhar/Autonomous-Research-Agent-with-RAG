import { create } from 'zustand'

interface AuthState {
  accessToken: string | null
  user: {
    id: number
    email: string
    username: string
    full_name?: string
  } | null
  isAuthenticated: boolean
  setAuth: (token: string, user: any) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isAuthenticated: false,
  setAuth: (token, user) => {
    localStorage.setItem('access_token', token)
    set({
      accessToken: token,
      user,
      isAuthenticated: true,
    })
  },
  clearAuth: () => {
    localStorage.removeItem('access_token')
    set({
      accessToken: null,
      user: null,
      isAuthenticated: false,
    })
  },
}))

// Initialize from localStorage on mount
if (typeof window !== 'undefined') {
  const token = localStorage.getItem('access_token')
  if (token) {
    // Try to get user info from token (basic check)
    useAuthStore.setState({ accessToken: token, isAuthenticated: true })
  }
}

