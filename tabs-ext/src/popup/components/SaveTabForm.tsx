import { useState } from 'react'
import { useSpaceStore } from '@shared/stores/space-store'
import { useCollectionStore } from '@shared/stores/collection-store'
import { useTabStore } from '@shared/stores/tab-store'

interface SaveTabFormProps {
  currentTab: chrome.tabs.Tab | null
}

function SaveTabForm({ currentTab }: SaveTabFormProps) {
  const { spaces } = useSpaceStore()
  const { getCollectionsBySpace } = useCollectionStore()
  const { addTab } = useTabStore()

  const [selectedSpaceId, setSelectedSpaceId] = useState<string>('')
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  const spaceCollections = selectedSpaceId
    ? getCollectionsBySpace(selectedSpaceId)
    : []

  const handleSave = async () => {
    if (!currentTab?.url || !selectedCollectionId) return

    setIsSaving(true)
    try {
      await addTab({
        collection_id: selectedCollectionId,
        title: currentTab.title || 'Untitled',
        url: currentTab.url,
        favicon: currentTab.favIconUrl,
      })
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (error) {
      console.error('Failed to save tab:', error)
    } finally {
      setIsSaving(false)
    }
  }

  if (!currentTab) {
    return (
      <div className="text-gray-500 text-sm">Loading current tab...</div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Current Tab Preview */}
      <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
        {currentTab.favIconUrl && (
          <img
            src={currentTab.favIconUrl}
            alt=""
            className="w-6 h-6 rounded"
          />
        )}
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-900 truncate">
            {currentTab.title}
          </div>
          <div className="text-xs text-gray-500 truncate">
            {currentTab.url}
          </div>
        </div>
      </div>

      {/* Space Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Space
        </label>
        <select
          value={selectedSpaceId}
          onChange={(e) => {
            setSelectedSpaceId(e.target.value)
            setSelectedCollectionId('')
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">Select a space...</option>
          {spaces.map((space) => (
            <option key={space.id} value={space.id}>
              {space.icon} {space.name}
            </option>
          ))}
        </select>
      </div>

      {/* Collection Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Collection
        </label>
        <select
          value={selectedCollectionId}
          onChange={(e) => setSelectedCollectionId(e.target.value)}
          disabled={!selectedSpaceId}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">Select a collection...</option>
          {spaceCollections.map((collection) => (
            <option key={collection.id} value={collection.id}>
              {collection.icon} {collection.name}
            </option>
          ))}
        </select>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        disabled={!selectedCollectionId || isSaving}
        className="w-full py-2 px-4 bg-primary-600 text-white rounded-md font-medium hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {isSaving ? 'Saving...' : saveSuccess ? 'Saved!' : 'Save Tab'}
      </button>
    </div>
  )
}

export default SaveTabForm
