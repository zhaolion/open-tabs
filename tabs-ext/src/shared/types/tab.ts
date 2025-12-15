export interface Tab {
  id: string
  collection_id: string
  title: string
  url: string
  favicon?: string
  description?: string
  order: number
  tags?: string[]
  created_at: string
  updated_at: string
  synced_at?: string
  is_deleted?: boolean
  meta?: {
    og_image?: string
    og_description?: string
  }
}

export interface CreateTabInput {
  collection_id: string
  title: string
  url: string
  favicon?: string
  description?: string
  tags?: string[]
}

export interface UpdateTabInput {
  title?: string
  url?: string
  favicon?: string
  description?: string
  order?: number
  tags?: string[]
  collection_id?: string
}
