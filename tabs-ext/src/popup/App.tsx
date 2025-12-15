import { useState, useEffect } from 'react'
import SaveTabForm from './components/SaveTabForm'
import QuickActions from './components/QuickActions'
import RecentTabs from './components/RecentTabs'

function App() {
  const [currentTab, setCurrentTab] = useState<chrome.tabs.Tab | null>(null)

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        setCurrentTab(tabs[0])
      }
    })
  }, [])

  return (
    <div className="w-[360px] min-h-[400px] bg-white">
      <header className="px-4 py-3 border-b border-gray-200">
        <h1 className="text-lg font-semibold text-gray-900">Open Tabs</h1>
      </header>

      <main className="p-4 space-y-4">
        <SaveTabForm currentTab={currentTab} />
        <QuickActions />
        <RecentTabs />
      </main>
    </div>
  )
}

export default App
