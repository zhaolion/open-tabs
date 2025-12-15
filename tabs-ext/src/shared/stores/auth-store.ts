import { create } from 'zustand'
import type { User, AuthState } from '@shared/types/auth'
import { STORAGE_KEYS } from '@shared/constants/storage-keys'

interface AuthStore extends AuthState {
  // Actions
  loadAuth: () => Promise<void>
  setAuth: (user: User, accessToken: string, expiresIn: number) => Promise<void>
  logout: () => Promise<void>
  isTokenExpired: () => boolean
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  access_token: null,
  token_expires_at: null,
  is_authenticated: false,
  is_loading: true,

  loadAuth: async () => {
    set({ is_loading: true })
    try {
      const result = await chrome.storage.local.get([
        STORAGE_KEYS.AUTH_USER,
        STORAGE_KEYS.AUTH_TOKEN,
        STORAGE_KEYS.TOKEN_EXPIRES_AT,
      ])

      const user = result[STORAGE_KEYS.AUTH_USER] as User | null
      const accessToken = result[STORAGE_KEYS.AUTH_TOKEN] as string | null
      const tokenExpiresAt = result[STORAGE_KEYS.TOKEN_EXPIRES_AT] as number | null

      // Check if token is expired
      if (tokenExpiresAt && Date.now() > tokenExpiresAt) {
        await get().logout()
        return
      }

      set({
        user,
        access_token: accessToken,
        token_expires_at: tokenExpiresAt,
        is_authenticated: !!user && !!accessToken,
        is_loading: false,
      })
    } catch (error) {
      console.error('Failed to load auth:', error)
      set({ is_loading: false })
    }
  },

  setAuth: async (user: User, accessToken: string, expiresIn: number) => {
    const tokenExpiresAt = Date.now() + expiresIn * 1000

    await chrome.storage.local.set({
      [STORAGE_KEYS.AUTH_USER]: user,
      [STORAGE_KEYS.AUTH_TOKEN]: accessToken,
      [STORAGE_KEYS.TOKEN_EXPIRES_AT]: tokenExpiresAt,
    })

    set({
      user,
      access_token: accessToken,
      token_expires_at: tokenExpiresAt,
      is_authenticated: true,
    })
  },

  logout: async () => {
    await chrome.storage.local.remove([
      STORAGE_KEYS.AUTH_USER,
      STORAGE_KEYS.AUTH_TOKEN,
      STORAGE_KEYS.TOKEN_EXPIRES_AT,
    ])

    set({
      user: null,
      access_token: null,
      token_expires_at: null,
      is_authenticated: false,
    })
  },

  isTokenExpired: () => {
    const { token_expires_at } = get()
    if (!token_expires_at) return true
    return Date.now() > token_expires_at
  },
}))

// Initialize store on load
useAuthStore.getState().loadAuth()
