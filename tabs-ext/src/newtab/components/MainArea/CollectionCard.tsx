import type { Collection } from '@shared/types/collection'
import { useTabStore } from '@shared/stores/tab-store'

interface CollectionCardProps {
  collection: Collection
  onClick: () => void
}

function CollectionCard({ collection, onClick }: CollectionCardProps) {
  const { getTabsByCollection } = useTabStore()
  const tabs = getTabsByCollection(collection.id)
  const tabCount = tabs.length

  return (
    <button
      onClick={onClick}
      className="p-4 bg-white border border-gray-200 rounded-xl hover:border-primary-300 hover:shadow-md transition-all text-left group"
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-2xl">{collection.icon || '📁'}</span>
        <span className="text-xs text-gray-400 group-hover:text-gray-500">
          {tabCount} tab{tabCount !== 1 ? 's' : ''}
        </span>
      </div>

      <h4 className="font-semibold text-gray-900 mb-1 truncate">
        {collection.name}
      </h4>

      {collection.description && (
        <p className="text-sm text-gray-500 line-clamp-2">
          {collection.description}
        </p>
      )}

      {/* Preview of tabs */}
      {tabs.length > 0 && (
        <div className="mt-3 flex -space-x-2">
          {tabs.slice(0, 5).map((tab) => (
            <div
              key={tab.id}
              className="w-6 h-6 bg-gray-100 rounded-full border-2 border-white overflow-hidden"
            >
              {tab.favicon ? (
                <img src={tab.favicon} alt="" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-gray-300" />
              )}
            </div>
          ))}
          {tabs.length > 5 && (
            <div className="w-6 h-6 bg-gray-200 rounded-full border-2 border-white flex items-center justify-center text-xs text-gray-600">
              +{tabs.length - 5}
            </div>
          )}
        </div>
      )}
    </button>
  )
}

export default CollectionCard
