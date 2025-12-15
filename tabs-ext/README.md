# Open Tabs - Chrome Extension

A Chrome extension for saving and organizing browser tabs with spaces and collections.

## Features

- **Tab Home**: New Tab page replacement for managing all your saved tabs
- **Spaces**: Organize tabs into workspaces (e.g., Work, Personal, Research)
- **Collections**: Group related tabs within each space
- **Quick Save**: Save current tab via popup or keyboard shortcut
- **Context Menu**: Right-click to save any link
- **Offline First**: Works without internet, syncs when connected

## Tech Stack

- **Framework**: React 18 + TypeScript 5
- **Build Tool**: Vite + CRXJS
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Chrome Extension**: Manifest V3

## Project Structure

```
tabs-ext/
├── public/
│   └── icons/                    # Extension icons
├── src/
│   ├── manifest.ts               # Chrome MV3 manifest
│   ├── background/               # Service worker
│   │   └── index.ts              # Context menu, shortcuts, messaging
│   ├── popup/                    # Browser action popup
│   │   ├── index.html
│   │   ├── index.tsx
│   │   ├── App.tsx
│   │   └── components/
│   │       ├── SaveTabForm.tsx   # Quick save form
│   │       ├── QuickActions.tsx  # Action buttons
│   │       └── RecentTabs.tsx    # Recent saved tabs
│   ├── newtab/                   # New Tab override (Tab Home)
│   │   ├── index.html
│   │   ├── index.tsx
│   │   ├── App.tsx
│   │   └── components/
│   │       ├── Header.tsx
│   │       ├── Sidebar/
│   │       │   ├── SpaceList.tsx
│   │       │   └── SpaceItem.tsx
│   │       ├── MainArea/
│   │       │   ├── CollectionGrid.tsx
│   │       │   ├── CollectionCard.tsx
│   │       │   ├── TabList.tsx
│   │       │   └── TabItem.tsx
│   │       └── Modals/
│   │           ├── CreateSpaceModal.tsx
│   │           └── CreateCollectionModal.tsx
│   ├── options/                  # Extension options page
│   │   ├── index.html
│   │   └── App.tsx
│   └── shared/                   # Shared code
│       ├── api/
│       │   ├── client.ts         # API client with auth
│       │   └── auth.ts           # Auth endpoints
│       ├── stores/
│       │   ├── auth-store.ts     # Authentication state
│       │   ├── space-store.ts    # Spaces CRUD
│       │   ├── collection-store.ts
│       │   └── tab-store.ts      # Tabs CRUD (max 1000/collection)
│       ├── types/
│       │   ├── space.ts
│       │   ├── collection.ts
│       │   ├── tab.ts
│       │   └── auth.ts
│       ├── constants/
│       │   ├── api.ts
│       │   └── storage-keys.ts
│       └── utils/
│           ├── uuid.ts
│           ├── date.ts
│           └── signature.ts      # HMAC signature for API
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## Data Model

```
Space (workspace)
├── id, name, description, icon, order
└── Collections[]
    ├── id, space_id, name, description, icon, order
    └── Tabs[] (max 1000 per collection)
        ├── id, collection_id, title, url, favicon
        └── order, created_at, updated_at
```

## Development

### Prerequisites

- Node.js 18+
- pnpm

### Setup

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build
```

### Load Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `dist/` directory

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_SIGNATURE_SECRET` | HMAC signature secret | - |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+Shift+S` (Mac) / `Ctrl+Shift+S` (Win) | Save current tab |

## Chrome Permissions

| Permission | Usage |
|------------|-------|
| `storage` | Store spaces, collections, and tabs locally |
| `tabs` | Access current tab info for saving |
| `contextMenus` | Right-click "Save to Open Tabs" menu |

## Backend Integration

The extension is designed to work with the Open Tabs FastAPI backend. API endpoints needed:

```
# Spaces
GET/POST   /api/v1/spaces
GET/PUT/DELETE /api/v1/spaces/{id}

# Collections
GET/POST   /api/v1/spaces/{space_id}/collections
GET/PUT/DELETE /api/v1/collections/{id}

# Tabs
GET/POST   /api/v1/collections/{collection_id}/tabs
GET/PUT/DELETE /api/v1/tabs/{id}
POST /api/v1/tabs/batch
```

## License

MIT
