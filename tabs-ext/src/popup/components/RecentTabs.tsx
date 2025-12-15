import { useTabStore } from '@shared/stores/tab-store'

function RecentTabs() {
  const { tabs } = useTabStore()

  // Get 5 most recent tabs
  const recentTabs = [...tabs]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)

  if (recentTabs.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500 text-sm">
        No saved tabs yet. Save your first tab!
      </div>
    )
  }

  const handleOpenTab = (url: string) => {
    chrome.tabs.create({ url })
  }

  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-2">Recent Tabs</h3>
      <div className="space-y-1">
        {recentTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleOpenTab(tab.url)}
            className="w-full flex items-center gap-2 p-2 rounded-md hover:bg-gray-100 transition-colors text-left"
          >
            {tab.favicon ? (
              <img src={tab.favicon} alt="" className="w-4 h-4 rounded" />
            ) : (
              <div className="w-4 h-4 bg-gray-200 rounded" />
            )}
            <span className="flex-1 text-sm text-gray-700 truncate">
              {tab.title}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default RecentTabs
