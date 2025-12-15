// HMAC signature generation (matches backend: tabapi/app/modules/auth/utils/signature.py)

const SIGNATURE_SECRET = import.meta.env.VITE_SIGNATURE_SECRET || 'default_secret_key'

export async function generateSignature(
  email: string,
  nonce: string,
  authAt: number,
  purpose: string
): Promise<string> {
  const message = `${email}:${nonce}:${authAt}:${purpose}`

  const encoder = new TextEncoder()
  const keyData = encoder.encode(SIGNATURE_SECRET)
  const messageData = encoder.encode(message)

  const key = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  )

  const signature = await crypto.subtle.sign('HMAC', key, messageData)

  // Convert to hex string
  return Array.from(new Uint8Array(signature))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}
