import { create } from 'zustand'
import type { Tab, CreateTabInput, UpdateTabInput } from '@shared/types/tab'
import { STORAGE_KEYS } from '@shared/constants/storage-keys'
import { generateUUID } from '@shared/utils/uuid'
import { nowISO } from '@shared/utils/date'

const MAX_TABS_PER_COLLECTION = 1000

interface TabStore {
  tabs: Tab[]
  isLoading: boolean
  error: string | null

  // Actions
  loadTabs: () => Promise<void>
  getTabsByCollection: (collectionId: string) => Tab[]
  addTab: (input: CreateTabInput) => Promise<Tab>
  updateTab: (id: string, input: UpdateTabInput) => Promise<Tab>
  deleteTab: (id: string) => Promise<void>
  moveTab: (id: string, targetCollectionId: string) => Promise<void>
}

export const useTabStore = create<TabStore>((set, get) => ({
  tabs: [],
  isLoading: false,
  error: null,

  loadTabs: async () => {
    set({ isLoading: true, error: null })
    try {
      const result = await chrome.storage.local.get(STORAGE_KEYS.TABS)
      const tabs = (result[STORAGE_KEYS.TABS] || []) as Tab[]

      set({
        tabs: tabs.filter((t) => !t.is_deleted),
        isLoading: false,
      })
    } catch (error) {
      set({ error: 'Failed to load tabs', isLoading: false })
      console.error('Failed to load tabs:', error)
    }
  },

  getTabsByCollection: (collectionId: string) => {
    const { tabs } = get()
    return tabs
      .filter((t) => t.collection_id === collectionId && !t.is_deleted)
      .sort((a, b) => a.order - b.order)
  },

  addTab: async (input: CreateTabInput) => {
    const { tabs } = get()
    const collectionTabs = tabs.filter((t) => t.collection_id === input.collection_id)

    // Check limit
    if (collectionTabs.length >= MAX_TABS_PER_COLLECTION) {
      throw new Error(`Collection already has ${MAX_TABS_PER_COLLECTION} tabs`)
    }

    // Check for duplicate URL in same collection
    const existingTab = collectionTabs.find((t) => t.url === input.url)
    if (existingTab) {
      // Update existing tab instead
      return get().updateTab(existingTab.id, {
        title: input.title,
        favicon: input.favicon,
      })
    }

    const now = nowISO()

    const newTab: Tab = {
      id: generateUUID(),
      collection_id: input.collection_id,
      title: input.title,
      url: input.url,
      favicon: input.favicon,
      description: input.description,
      order: collectionTabs.length,
      tags: input.tags,
      created_at: now,
      updated_at: now,
    }

    const updatedTabs = [...tabs, newTab]

    await chrome.storage.local.set({ [STORAGE_KEYS.TABS]: updatedTabs })
    set({ tabs: updatedTabs })

    return newTab
  },

  updateTab: async (id: string, input: UpdateTabInput) => {
    const { tabs } = get()
    const index = tabs.findIndex((t) => t.id === id)
    if (index === -1) throw new Error('Tab not found')

    const updatedTab: Tab = {
      ...tabs[index],
      ...input,
      updated_at: nowISO(),
    }

    const updatedTabs = [...tabs]
    updatedTabs[index] = updatedTab

    await chrome.storage.local.set({ [STORAGE_KEYS.TABS]: updatedTabs })
    set({ tabs: updatedTabs })

    return updatedTab
  },

  deleteTab: async (id: string) => {
    const { tabs } = get()
    const index = tabs.findIndex((t) => t.id === id)
    if (index === -1) return

    // Soft delete
    const updatedTabs = tabs.map((t) =>
      t.id === id ? { ...t, is_deleted: true, updated_at: nowISO() } : t
    )

    await chrome.storage.local.set({ [STORAGE_KEYS.TABS]: updatedTabs })
    set({ tabs: updatedTabs.filter((t) => !t.is_deleted) })
  },

  moveTab: async (id: string, targetCollectionId: string) => {
    const { tabs } = get()
    const tab = tabs.find((t) => t.id === id)
    if (!tab) throw new Error('Tab not found')

    const targetCollectionTabs = tabs.filter((t) => t.collection_id === targetCollectionId)

    // Check limit
    if (targetCollectionTabs.length >= MAX_TABS_PER_COLLECTION) {
      throw new Error(`Target collection already has ${MAX_TABS_PER_COLLECTION} tabs`)
    }

    await get().updateTab(id, {
      collection_id: targetCollectionId,
      order: targetCollectionTabs.length,
    })
  },
}))

// Initialize store on load
useTabStore.getState().loadTabs()
