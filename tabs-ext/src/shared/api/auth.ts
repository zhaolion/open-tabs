import { apiClient } from './client'
import { AUTH_ENDPOINTS } from '@shared/constants/api'
import { generateSignature } from '@shared/utils/signature'
import { generateNonce } from '@shared/utils/uuid'
import { nowUnix } from '@shared/utils/date'
import type { AuthTokenResponse } from '@shared/types/auth'

export async function sendVerificationCode(
  email: string,
  purpose: 'register' | 'login' | 'reset_password'
): Promise<void> {
  const nonce = generateNonce()
  const authAt = nowUnix()
  const signature = await generateSignature(email, nonce, authAt, purpose)

  await apiClient.post(AUTH_ENDPOINTS.SEND_VERIFICATION_CODE, {
    email,
    purpose,
    nonce,
    auth_at: authAt,
    signature,
  })
}

export async function loginWithVerificationCode(
  email: string,
  code: string
): Promise<AuthTokenResponse> {
  const nonce = generateNonce()
  const authAt = nowUnix()
  const signature = await generateSignature(email, nonce, authAt, 'login')

  return apiClient.post<AuthTokenResponse>(AUTH_ENDPOINTS.LOGIN_WITH_CODE, {
    email,
    code,
    nonce,
    auth_at: authAt,
    signature,
  })
}

export async function register(
  email: string,
  code: string,
  password: string
): Promise<AuthTokenResponse> {
  const nonce = generateNonce()
  const authAt = nowUnix()
  const signature = await generateSignature(email, nonce, authAt, 'register')

  return apiClient.post<AuthTokenResponse>(AUTH_ENDPOINTS.REGISTER, {
    email,
    code,
    password,
    nonce,
    auth_at: authAt,
    signature,
  })
}
