import type { Space } from '@shared/types/space'

interface SpaceItemProps {
  space: Space
  isActive: boolean
  onClick: () => void
}

function SpaceItem({ space, isActive, onClick }: SpaceItemProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
        isActive
          ? 'bg-primary-50 text-primary-700'
          : 'text-gray-700 hover:bg-gray-100'
      }`}
    >
      <span className="text-lg">{space.icon || '📁'}</span>
      <span className="flex-1 truncate font-medium">{space.name}</span>
    </button>
  )
}

export default SpaceItem
