export interface Collection {
  id: string
  space_id: string
  name: string
  description?: string
  icon?: string
  color?: string
  order: number
  view_mode: 'list' | 'grid'
  created_at: string
  updated_at: string
  synced_at?: string
  is_deleted?: boolean
}

export interface CreateCollectionInput {
  space_id: string
  name: string
  description?: string
  icon?: string
  color?: string
}

export interface UpdateCollectionInput {
  name?: string
  description?: string
  icon?: string
  color?: string
  order?: number
  view_mode?: 'list' | 'grid'
}
