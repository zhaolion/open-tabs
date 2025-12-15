import { create } from 'zustand'
import type { Collection, CreateCollectionInput, UpdateCollectionInput } from '@shared/types/collection'
import { STORAGE_KEYS } from '@shared/constants/storage-keys'
import { generateUUID } from '@shared/utils/uuid'
import { nowISO } from '@shared/utils/date'

interface CollectionStore {
  collections: Collection[]
  isLoading: boolean
  error: string | null

  // Actions
  loadCollections: () => Promise<void>
  getCollectionsBySpace: (spaceId: string) => Collection[]
  addCollection: (input: CreateCollectionInput) => Promise<Collection>
  updateCollection: (id: string, input: UpdateCollectionInput) => Promise<Collection>
  deleteCollection: (id: string) => Promise<void>
}

export const useCollectionStore = create<CollectionStore>((set, get) => ({
  collections: [],
  isLoading: false,
  error: null,

  loadCollections: async () => {
    set({ isLoading: true, error: null })
    try {
      const result = await chrome.storage.local.get(STORAGE_KEYS.COLLECTIONS)
      const collections = (result[STORAGE_KEYS.COLLECTIONS] || []) as Collection[]

      set({
        collections: collections.filter((c) => !c.is_deleted),
        isLoading: false,
      })
    } catch (error) {
      set({ error: 'Failed to load collections', isLoading: false })
      console.error('Failed to load collections:', error)
    }
  },

  getCollectionsBySpace: (spaceId: string) => {
    const { collections } = get()
    return collections
      .filter((c) => c.space_id === spaceId && !c.is_deleted)
      .sort((a, b) => a.order - b.order)
  },

  addCollection: async (input: CreateCollectionInput) => {
    const { collections } = get()
    const spaceCollections = collections.filter((c) => c.space_id === input.space_id)
    const now = nowISO()

    const newCollection: Collection = {
      id: generateUUID(),
      space_id: input.space_id,
      name: input.name,
      description: input.description,
      icon: input.icon || '📁',
      color: input.color,
      order: spaceCollections.length,
      view_mode: 'list',
      created_at: now,
      updated_at: now,
    }

    const updatedCollections = [...collections, newCollection]

    await chrome.storage.local.set({ [STORAGE_KEYS.COLLECTIONS]: updatedCollections })
    set({ collections: updatedCollections })

    return newCollection
  },

  updateCollection: async (id: string, input: UpdateCollectionInput) => {
    const { collections } = get()
    const index = collections.findIndex((c) => c.id === id)
    if (index === -1) throw new Error('Collection not found')

    const updatedCollection: Collection = {
      ...collections[index],
      ...input,
      updated_at: nowISO(),
    }

    const updatedCollections = [...collections]
    updatedCollections[index] = updatedCollection

    await chrome.storage.local.set({ [STORAGE_KEYS.COLLECTIONS]: updatedCollections })
    set({ collections: updatedCollections })

    return updatedCollection
  },

  deleteCollection: async (id: string) => {
    const { collections } = get()
    const index = collections.findIndex((c) => c.id === id)
    if (index === -1) return

    // Soft delete
    const updatedCollections = collections.map((c) =>
      c.id === id ? { ...c, is_deleted: true, updated_at: nowISO() } : c
    )

    await chrome.storage.local.set({ [STORAGE_KEYS.COLLECTIONS]: updatedCollections })
    set({ collections: updatedCollections.filter((c) => !c.is_deleted) })
  },
}))

// Initialize store on load
useCollectionStore.getState().loadCollections()
