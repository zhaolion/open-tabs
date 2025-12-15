export interface Space {
  id: string
  name: string
  description?: string
  icon?: string
  color?: string
  order: number
  is_default?: boolean
  created_at: string
  updated_at: string
  synced_at?: string
  is_deleted?: boolean
}

export interface CreateSpaceInput {
  name: string
  description?: string
  icon?: string
  color?: string
}

export interface UpdateSpaceInput {
  name?: string
  description?: string
  icon?: string
  color?: string
  order?: number
}
