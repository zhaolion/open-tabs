export function generateUUID(): string {
  return crypto.randomUUID()
}

export function generateNonce(): string {
  return crypto.randomUUID()
}
