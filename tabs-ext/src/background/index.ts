// Background service worker for Open Tabs extension

// Initialize context menus on install
chrome.runtime.onInstalled.addListener(() => {
  console.log('Open Tabs extension installed')

  // Create context menu
  chrome.contextMenus.create({
    id: 'save-to-collection',
    title: 'Save to Open Tabs',
    contexts: ['page', 'link'],
  })
})

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'save-to-collection') {
    const url = info.linkUrl || info.pageUrl
    const title = tab?.title || 'Untitled'

    // Send message to save tab
    chrome.runtime.sendMessage({
      type: 'SAVE_TAB',
      payload: {
        url,
        title,
        favicon: tab?.favIconUrl,
      },
    })
  }
})

// Handle keyboard shortcuts
chrome.commands.onCommand.addListener((command) => {
  if (command === 'save-current-tab') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.runtime.sendMessage({
          type: 'SAVE_TAB',
          payload: {
            url: tabs[0].url,
            title: tabs[0].title,
            favicon: tabs[0].favIconUrl,
          },
        })
      }
    })
  }
})

// Handle messages from popup/newtab
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  console.log('Background received message:', message)

  switch (message.type) {
    case 'GET_CURRENT_TAB':
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        sendResponse({ tab: tabs[0] })
      })
      return true // Keep channel open for async response

    case 'OPEN_NEWTAB':
      chrome.tabs.create({ url: chrome.runtime.getURL('src/newtab/index.html') })
      sendResponse({ success: true })
      break

    default:
      sendResponse({ error: 'Unknown message type' })
  }
})

export {}
