export function nowISO(): string {
  return new Date().toISOString()
}

export function nowUnix(): number {
  return Math.floor(Date.now() / 1000)
}
