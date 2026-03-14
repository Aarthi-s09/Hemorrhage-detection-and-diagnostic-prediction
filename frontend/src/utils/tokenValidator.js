/**
 * Token validation and cleanup utility
 */

/**
 * Decodes a JWT token without verification (for client-side inspection only)
 */
export function decodeToken(token) {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch (error) {
    console.error('Failed to decode token:', error)
    return null
  }
}

/**
 * Check if a token is expired
 */
export function isTokenExpired(token) {
  const decoded = decodeToken(token)
  if (!decoded || !decoded.exp) {
    return true
  }
  
  // Token exp is in seconds, Date.now() is in milliseconds
  return decoded.exp * 1000 < Date.now()
}

/**
 * Validate tokens and clear if invalid/expired
 * Returns true if tokens are valid, false if they were cleared
 */
export function validateAndCleanupTokens() {
  const accessToken = localStorage.getItem('accessToken')
  const refreshToken = localStorage.getItem('refreshToken')
  
  if (!accessToken && !refreshToken) {
    // No tokens, nothing to clean
    return false
  }
  
  // Check if access token is expired
  if (accessToken && isTokenExpired(accessToken)) {
    console.log('Access token expired')
    
    // Check if refresh token is also expired
    if (refreshToken && isTokenExpired(refreshToken)) {
      console.log('Refresh token also expired, clearing all tokens')
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      return false
    }
  }
  
  // Tokens exist and at least refresh token is valid
  return true
}

/**
 * Force clear all authentication data
 */
export function clearAllAuthData() {
  localStorage.removeItem('accessToken')
  localStorage.removeItem('refreshToken')
  localStorage.removeItem('user')
  console.log('All authentication data cleared')
}
