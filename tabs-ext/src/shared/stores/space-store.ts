import { create } from 'zustand'
import type { Space, CreateSpaceInput, UpdateSpaceInput } from '@shared/types/space'
import { STORAGE_KEYS } from '@shared/constants/storage-keys'
import { generateUUID } from '@shared/utils/uuid'
import { nowISO } from '@shared/utils/date'

interface SpaceStore {
  spaces: Space[]
  activeSpaceId: string | null
  activeSpace: Space | null
  isLoading: boolean
  error: string | null

  // Actions
  loadSpaces: () => Promise<void>
  addSpace: (input: CreateSpaceInput) => Promise<Space>
  updateSpace: (id: string, input: UpdateSpaceInput) => Promise<Space>
  deleteSpace: (id: string) => Promise<void>
  setActiveSpace: (id: string) => void
}

export const useSpaceStore = create<SpaceStore>((set, get) => ({
  spaces: [],
  activeSpaceId: null,
  activeSpace: null,
  isLoading: false,
  error: null,

  loadSpaces: async () => {
    set({ isLoading: true, error: null })
    try {
      const result = await chrome.storage.local.get([STORAGE_KEYS.SPACES, STORAGE_KEYS.ACTIVE_SPACE_ID])
      const spaces = (result[STORAGE_KEYS.SPACES] || []) as Space[]
      const activeSpaceId = result[STORAGE_KEYS.ACTIVE_SPACE_ID] as string | null

      set({
        spaces: spaces.filter((s) => !s.is_deleted),
        activeSpaceId,
        activeSpace: spaces.find((s) => s.id === activeSpaceId) || null,
        isLoading: false,
      })
    } catch (error) {
      set({ error: 'Failed to load spaces', isLoading: false })
      console.error('Failed to load spaces:', error)
    }
  },

  addSpace: async (input: CreateSpaceInput) => {
    const { spaces } = get()
    const now = nowISO()

    const newSpace: Space = {
      id: generateUUID(),
      name: input.name,
      description: input.description,
      icon: input.icon || '📁',
      color: input.color,
      order: spaces.length,
      created_at: now,
      updated_at: now,
    }

    const updatedSpaces = [...spaces, newSpace]

    await chrome.storage.local.set({ [STORAGE_KEYS.SPACES]: updatedSpaces })
    set({ spaces: updatedSpaces })

    // Auto-select if first space
    if (updatedSpaces.length === 1) {
      get().setActiveSpace(newSpace.id)
    }

    return newSpace
  },

  updateSpace: async (id: string, input: UpdateSpaceInput) => {
    const { spaces } = get()
    const index = spaces.findIndex((s) => s.id === id)
    if (index === -1) throw new Error('Space not found')

    const updatedSpace: Space = {
      ...spaces[index],
      ...input,
      updated_at: nowISO(),
    }

    const updatedSpaces = [...spaces]
    updatedSpaces[index] = updatedSpace

    await chrome.storage.local.set({ [STORAGE_KEYS.SPACES]: updatedSpaces })
    set({
      spaces: updatedSpaces,
      activeSpace: get().activeSpaceId === id ? updatedSpace : get().activeSpace,
    })

    return updatedSpace
  },

  deleteSpace: async (id: string) => {
    const { spaces, activeSpaceId } = get()
    const index = spaces.findIndex((s) => s.id === id)
    if (index === -1) return

    // Soft delete
    const updatedSpaces = spaces.map((s) =>
      s.id === id ? { ...s, is_deleted: true, updated_at: nowISO() } : s
    )

    await chrome.storage.local.set({ [STORAGE_KEYS.SPACES]: updatedSpaces })

    const visibleSpaces = updatedSpaces.filter((s) => !s.is_deleted)
    set({ spaces: visibleSpaces })

    // Select another space if current was deleted
    if (activeSpaceId === id) {
      const nextSpace = visibleSpaces[0]
      if (nextSpace) {
        get().setActiveSpace(nextSpace.id)
      } else {
        set({ activeSpaceId: null, activeSpace: null })
      }
    }
  },

  setActiveSpace: (id: string) => {
    const { spaces } = get()
    const space = spaces.find((s) => s.id === id)

    chrome.storage.local.set({ [STORAGE_KEYS.ACTIVE_SPACE_ID]: id })
    set({ activeSpaceId: id, activeSpace: space || null })
  },
}))

// Initialize store on load
useSpaceStore.getState().loadSpaces()
