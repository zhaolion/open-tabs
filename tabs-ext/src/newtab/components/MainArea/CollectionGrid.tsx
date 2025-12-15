import { useState } from 'react'
import { useSpaceStore } from '@shared/stores/space-store'
import { useCollectionStore } from '@shared/stores/collection-store'
import CollectionCard from './CollectionCard'
import TabList from './TabList'
import CreateCollectionModal from '../Modals/CreateCollectionModal'

function CollectionGrid() {
  const { activeSpaceId } = useSpaceStore()
  const { getCollectionsBySpace } = useCollectionStore()
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  const collections = activeSpaceId ? getCollectionsBySpace(activeSpaceId) : []

  if (!activeSpaceId) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Select a space from the sidebar to get started
      </div>
    )
  }

  // If a collection is selected, show tabs
  if (selectedCollectionId) {
    return (
      <TabList
        collectionId={selectedCollectionId}
        onBack={() => setSelectedCollectionId(null)}
      />
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Collections</h3>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Collection
        </button>
      </div>

      {collections.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-4">📚</div>
          <p className="mb-2">No collections yet</p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="text-primary-600 hover:text-primary-700"
          >
            Create your first collection
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {collections.map((collection) => (
            <CollectionCard
              key={collection.id}
              collection={collection}
              onClick={() => setSelectedCollectionId(collection.id)}
            />
          ))}
        </div>
      )}

      <CreateCollectionModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        spaceId={activeSpaceId}
      />
    </div>
  )
}

export default CollectionGrid
