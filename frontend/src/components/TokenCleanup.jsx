import { useEffect, useState } from 'react'

/**
 * Automatically detects and cleans up invalid tokens on app startup
 */
export default function TokenCleanup() {
  const [showCleanupMessage, setShowCleanupMessage] = useState(false)

  useEffect(() => {
    const checkAndCleanTokens = async () => {
      const accessToken = localStorage.getItem('accessToken')
      const refreshToken = localStorage.getItem('refreshToken')

      // If no tokens, nothing to clean
      if (!accessToken && !refreshToken) {
        return
      }

      // Try to verify the token with backend
      try {
        const response = await fetch('/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        })

        if (response.status === 401) {
          // Token is invalid, clear everything
          console.log('🧹 Detected invalid tokens, clearing automatically...')
          setShowCleanupMessage(true)
          
          setTimeout(() => {
            localStorage.clear()
            window.location.reload()
          }, 2000)
        }
      } catch (error) {
        console.error('Token validation error:', error)
      }
    }

    checkAndCleanTokens()
  }, [])

  if (!showCleanupMessage) {
    return null
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md animate-fade-in">
        <div className="flex items-center gap-3 mb-4">
          <div className="animate-spin text-blue-600">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Cleaning Up Session</h3>
        </div>
        <p className="text-gray-600">
          Detected invalid authentication tokens. Clearing automatically...
        </p>
        <div className="mt-4 p-3 bg-blue-50 rounded text-sm text-blue-800">
          Please wait, refreshing page...
        </div>
      </div>
    </div>
  )
}
