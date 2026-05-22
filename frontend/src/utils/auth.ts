export type UserRole = 'admin' | 'guest' | ''

export function getRoleFromToken(token: string | null): UserRole {
  if (!token) return ''

  try {
    const payload = token.split('.')[1]
    if (!payload) return ''

    const normalizedPayload = payload.replace(/-/g, '+').replace(/_/g, '/')
    const decodedPayload = decodeURIComponent(
      atob(normalizedPayload)
        .split('')
        .map((char) => `%${char.charCodeAt(0).toString(16).padStart(2, '0')}`)
        .join(''),
    )
    const data = JSON.parse(decodedPayload)

    return data.sub === 'guest' ? 'guest' : 'admin'
  } catch {
    return ''
  }
}

export function isGuestToken(token: string | null) {
  return getRoleFromToken(token) === 'guest'
}
