export type UserRole = 'admin' | 'guest' | ''

function decodeJwtPayload(token: string): Record<string, any> | null {
  const payload = token.split('.')[1]
  if (!payload) return null

  const normalizedPayload = payload.replace(/-/g, '+').replace(/_/g, '/')
  const padding = '='.repeat((4 - normalizedPayload.length % 4) % 4)
  const decodedPayload = decodeURIComponent(
    atob(`${normalizedPayload}${padding}`)
      .split('')
      .map((char) => `%${char.charCodeAt(0).toString(16).padStart(2, '0')}`)
      .join(''),
  )

  return JSON.parse(decodedPayload)
}

export function isTokenExpired(token: string | null): boolean {
  if (!token) return true

  try {
    const data = decodeJwtPayload(token)
    if (!data) return true
    if (typeof data.exp !== 'number') return false
    return data.exp * 1000 <= Date.now()
  } catch {
    return true
  }
}

export function getRoleFromToken(token: string | null): UserRole {
  if (!token) return ''

  try {
    if (isTokenExpired(token)) return ''
    const data = decodeJwtPayload(token)
    if (!data) return ''

    return data.sub === 'guest' ? 'guest' : 'admin'
  } catch {
    return ''
  }
}

export function isGuestToken(token: string | null) {
  return getRoleFromToken(token) === 'guest'
}
