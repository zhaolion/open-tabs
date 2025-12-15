export interface User {
  uid: string
  username: string
  email: string | null
  display_name: string | null
  avatar_url: string | null
  status: 'pending' | 'active' | 'suspended' | 'deleted'
  created_at: string
}

export interface AuthTokenResponse {
  user: User
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface AuthState {
  user: User | null
  access_token: string | null
  token_expires_at: number | null
  is_authenticated: boolean
  is_loading: boolean
}

export interface LoginRequest {
  email: string
  code: string
  nonce: string
  auth_at: number
  signature: string
}

export interface SendVerificationCodeRequest {
  email: string
  purpose: 'register' | 'login' | 'reset_password'
  nonce: string
  auth_at: number
  signature: string
}
