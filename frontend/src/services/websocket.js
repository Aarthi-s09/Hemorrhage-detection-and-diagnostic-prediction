import { useEffect, useRef, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'

export function useWebSocket(onMessage) {
  const { user, logout } = useAuth()
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttemptsRef = useRef(0)
  const maxReconnectAttempts = 5

  const connect = useCallback(() => {
    // Disabled for development - WebSocket authentication issues
    console.log('WebSocket disabled for development')
    return
    
    if (!user) {
      return
    }

    const token = localStorage.getItem('accessToken')
    if (!token) {
      console.log('No access token available for WebSocket')
      return
    }

    // Use backend URL directly
    const wsUrl = `ws://127.0.0.1:8082/api/v1/notifications/ws/${token}`

    try {
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        console.log('WebSocket connected successfully')
        reconnectAttemptsRef.current = 0
      }

      wsRef.current.onmessage = (event) => {
        // Ignore pong messages (they're plain text, not JSON)
        if (event.data === 'pong') {
          return
        }
        
        try {
          const data = JSON.parse(event.data)
          onMessage?.(data)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason)
        
        // Handle authentication errors
        if (event.code === 4001) {
          console.error('WebSocket authentication failed - invalid token')
          // Clear tokens and redirect to login
          localStorage.removeItem('accessToken')
          localStorage.removeItem('refreshToken')
          logout()
          return
        }
        
        // Attempt to reconnect if not too many attempts
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000)
          console.log(`Reconnecting in ${delay/1000}s (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)
          reconnectTimeoutRef.current = setTimeout(connect, delay)
        } else {
          console.error('Max WebSocket reconnection attempts reached')
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }, [user, onMessage, logout])

  useEffect(() => {
    connect()

    // Send ping every 30 seconds
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 30000)

    return () => {
      clearInterval(pingInterval)
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  return { sendMessage }
}
