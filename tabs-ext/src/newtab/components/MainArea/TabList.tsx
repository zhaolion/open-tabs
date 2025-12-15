import { useTabStore } from '@shared/stores/tab-store'
import { useCollectionStore } from '@shared/stores/collection-store'
import TabItem from './TabItem'

interface TabListProps {
  collectionId: string
  onBack: () => void
}

function TabList({ collectionId, onBack }: TabListProps) {
  const { getTabsByCollection, deleteTab } = useTabStore()
  const { collections } = useCollectionStore()

  const collection = collections.find((c) => c.id === collectionId)
  const tabs = getTabsByCollection(collectionId)

  const handleOpenTab = (url: string) => {
    chrome.tabs.create({ url })
  }

  const handleDeleteTab = async (tabId: string) => {
    await deleteTab(tabId)
  }

  const handleOpenAllTabs = () => {
    tabs.forEach((tab) => {
      chrome.tabs.create({ url: tab.url, active: false })
    })
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {collection?.icon} {collection?.name}
            </h3>
            <p className="text-sm text-gray-500">
              {tabs.length} tab{tabs.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>

        {tabs.length > 0 && (
          <button
            onClick={handleOpenAllTabs}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Open All
          </button>
        )}
      </div>

      {/* Tab List */}
      {tabs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-4">🔖</div>
          <p>No tabs in this collection yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {tabs.map((tab) => (
            <TabItem
              key={tab.id}
              tab={tab}
              onOpen={() => handleOpenTab(tab.url)}
              onDelete={() => handleDeleteTab(tab.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default TabList
