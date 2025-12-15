import { useState } from 'react'
import { useSpaceStore } from '@shared/stores/space-store'
import SpaceItem from './SpaceItem'
import CreateSpaceModal from '../Modals/CreateSpaceModal'

function SpaceList() {
  const { spaces, activeSpaceId, setActiveSpace } = useSpaceStore()
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-2">
        <div className="flex items-center justify-between px-2 py-1 mb-2">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Spaces
          </span>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        {spaces.length === 0 ? (
          <div className="px-2 py-4 text-center text-sm text-gray-500">
            No spaces yet.
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="block mx-auto mt-2 text-primary-600 hover:text-primary-700"
            >
              Create your first space
            </button>
          </div>
        ) : (
          <div className="space-y-1">
            {spaces.map((space) => (
              <SpaceItem
                key={space.id}
                space={space}
                isActive={space.id === activeSpaceId}
                onClick={() => setActiveSpace(space.id)}
              />
            ))}
          </div>
        )}
      </div>

      <CreateSpaceModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  )
}

export default SpaceList
