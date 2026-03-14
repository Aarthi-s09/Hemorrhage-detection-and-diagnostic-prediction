import { useEffect, useState } from 'react'
import { AlertTriangle, RefreshCw, LogOut } from 'lucide-react'
import { decodeToken, isTokenExpired } from '../utils/tokenValidator'

export default function TokenDebugger() {
  const [tokenInfo, setTokenInfo] = useState(null)
  const [showDebugger, setShowDebugger] = useState(false)

  useEffect(() => {
    checkTokens()
  }, [])

  const checkTokens = () => {
    const accessToken = localStorage.getItem('accessToken')
    const refreshToken = localStorage.getItem('refreshToken')

    if (!accessToken && !refreshToken) {
      setTokenInfo(null)
      return
    }

    const accessDecoded = accessToken ? decodeToken(accessToken) : null
    const refreshDecoded = refreshToken ? decodeToken(refreshToken) : null

    setTokenInfo({
      hasAccess: !!accessToken,
      hasRefresh: !!refreshToken,
      accessExpired: accessToken ? isTokenExpired(accessToken) : null,
      refreshExpired: refreshToken ? isTokenExpired(refreshToken) : null,
      accessExp: accessDecoded?.exp,
      refreshExp: refreshDecoded?.exp,
      userId: accessDecoded?.sub,
    })

    // Auto-show debugger if tokens are expired
    if (accessToken && isTokenExpired(accessToken) && refreshToken && isTokenExpired(refreshToken)) {
      setShowDebugger(true)
    }
  }

  const clearTokens = () => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  if (!tokenInfo || (!tokenInfo.hasAccess && !tokenInfo.hasRefresh)) {
    return null
  }

  const hasExpiredTokens = tokenInfo.accessExpired || tokenInfo.refreshExpired

  return (
    <>
      {/* Floating warning for expired tokens */}
      {hasExpiredTokens && !showDebugger && (
        <div className="fixed bottom-4 right-4 z-50">
          <div className="bg-red-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-bounce">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Token Expired!</span>
            <button
              onClick={() => setShowDebugger(true)}
              className="ml-2 px-3 py-1 bg-white text-red-600 rounded hover:bg-red-50 text-sm font-medium"
            >
              Fix Now
            </button>
          </div>
        </div>
      )}

      {/* Debug Panel */}
      {showDebugger && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-8 h-8 text-red-500" />
              <h2 className="text-2xl font-bold text-gray-900">Authentication Issue Detected</h2>
            </div>

            <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
              <h3 className="font-semibold text-red-800 mb-2">Your tokens are expired or invalid!</h3>
              <p className="text-red-700 text-sm">
                This usually happens when the database was reset. You need to clear your browser storage and login again.
              </p>
            </div>

            <div className="space-y-3 mb-6 bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-700 mb-2">Token Status:</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Access Token:</span>
                  <span className={tokenInfo.hasAccess ? (tokenInfo.accessExpired ? 'text-red-600 font-semibold' : 'text-green-600') : 'text-gray-400'}>
                    {tokenInfo.hasAccess ? (tokenInfo.accessExpired ? '❌ Expired' : '✅ Valid') : 'Not Found'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Refresh Token:</span>
                  <span className={tokenInfo.hasRefresh ? (tokenInfo.refreshExpired ? 'text-red-600 font-semibold' : 'text-green-600') : 'text-gray-400'}>
                    {tokenInfo.hasRefresh ? (tokenInfo.refreshExpired ? '❌ Expired' : '✅ Valid') : 'Not Found'}
                  </span>
                </div>
                {tokenInfo.userId && (
                  <div className="flex justify-between pt-2 border-t border-gray-200">
                    <span className="text-gray-600">User ID:</span>
                    <span className="text-gray-900 font-mono">{tokenInfo.userId}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-3">
              <button
                onClick={clearTokens}
                className="w-full flex items-center justify-center gap-2 bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                <LogOut className="w-5 h-5" />
                Clear Tokens & Login Again
              </button>
              
              <button
                onClick={() => setShowDebugger(false)}
                className="w-full text-gray-600 hover:text-gray-900 py-2"
              >
                Dismiss
              </button>
            </div>

            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-800">
                <strong>Alternative:</strong> Open DevTools (F12) → Application tab → Clear site data
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Debug Toggle Button (bottom-left corner) */}
      {!showDebugger && (
        <button
          onClick={() => setShowDebugger(true)}
          className="fixed bottom-4 left-4 z-40 bg-gray-800 text-white p-2 rounded-full shadow-lg hover:bg-gray-700 transition-colors"
          title="Token Debugger"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      )}
    </>
  )
}
