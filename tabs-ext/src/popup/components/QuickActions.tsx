function QuickActions() {
  const openTabHome = () => {
    chrome.runtime.sendMessage({ type: 'OPEN_NEWTAB' })
  }

  const openOptions = () => {
    chrome.runtime.openOptionsPage()
  }

  return (
    <div className="flex gap-2">
      <button
        onClick={openTabHome}
        className="flex-1 py-2 px-3 bg-gray-100 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-200 transition-colors"
      >
        Open Tab Home
      </button>
      <button
        onClick={openOptions}
        className="py-2 px-3 bg-gray-100 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-200 transition-colors"
      >
        Settings
      </button>
    </div>
  )
}

export default QuickActions
