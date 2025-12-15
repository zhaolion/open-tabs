// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Auth endpoints
export const AUTH_ENDPOINTS = {
  SEND_VERIFICATION_CODE: '/auth/v1/verification-code/send',
  REGISTER: '/auth/v1/register',
  LOGIN: '/auth/v1/login',
  LOGIN_WITH_CODE: '/auth/v1/login/verification-code',
  RESET_PASSWORD: '/auth/v1/reset-password',
} as const

// API endpoints
export const API_ENDPOINTS = {
  // Spaces
  SPACES: '/api/v1/spaces',
  SPACE: (id: string) => `/api/v1/spaces/${id}`,

  // Collections
  COLLECTIONS: (spaceId: string) => `/api/v1/spaces/${spaceId}/collections`,
  COLLECTION: (id: string) => `/api/v1/collections/${id}`,

  // Tabs
  TABS: (collectionId: string) => `/api/v1/collections/${collectionId}/tabs`,
  TAB: (id: string) => `/api/v1/tabs/${id}`,
  TABS_BATCH: '/api/v1/tabs/batch',
} as const
