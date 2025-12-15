export const STORAGE_KEYS = {
  // Auth
  AUTH_TOKEN: 'auth_token',
  AUTH_USER: 'auth_user',
  TOKEN_EXPIRES_AT: 'token_expires_at',

  // Data
  SPACES: 'spaces',
  COLLECTIONS: 'collections',
  TABS: 'tabs',

  // State
  ACTIVE_SPACE_ID: 'active_space_id',

  // Sync
  SYNC_QUEUE: 'sync_queue',
  LAST_SYNC_AT: 'last_sync_at',

  // Settings
  SETTINGS: 'settings',
  DEFAULT_SPACE_ID: 'default_space_id',
} as const

export type StorageKey = (typeof STORAGE_KEYS)[keyof typeof STORAGE_KEYS]
