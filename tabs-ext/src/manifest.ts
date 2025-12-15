import { defineManifest } from '@crxjs/vite-plugin'
import packageJson from '../package.json'

const { version } = packageJson

export default defineManifest({
  manifest_version: 3,
  name: 'Open Tabs',
  description: 'Save and organize your browser tabs with spaces and collections',
  version,

  icons: {
    '16': 'icons/icon-16.png',
    '32': 'icons/icon-32.png',
    '48': 'icons/icon-48.png',
    '128': 'icons/icon-128.png',
  },

  action: {
    default_popup: 'src/popup/index.html',
    default_icon: {
      '16': 'icons/icon-16.png',
      '32': 'icons/icon-32.png',
    },
    default_title: 'Open Tabs',
  },

  background: {
    service_worker: 'src/background/index.ts',
    type: 'module',
  },

  chrome_url_overrides: {
    newtab: 'src/newtab/index.html',
  },

  options_page: 'src/options/index.html',

  permissions: [
    'storage',
    'tabs',
    'contextMenus',
  ],

  host_permissions: [
    '<all_urls>',
  ],

  commands: {
    'save-current-tab': {
      suggested_key: {
        default: 'Ctrl+Shift+S',
        mac: 'Command+Shift+S',
      },
      description: 'Save current tab to collection',
    },
  },
})
