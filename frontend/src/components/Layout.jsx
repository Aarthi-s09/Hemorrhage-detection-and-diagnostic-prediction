import { useState, useCallback } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useWebSocket } from '../services/websocket'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { notificationApi } from '../services/api'
import toast from 'react-hot-toast'
import {
  HomeIcon,
  UserGroupIcon,
  DocumentMagnifyingGlassIcon,
  DocumentTextIcon,
  BellIcon,
  UserCircleIcon,
  ArrowLeftOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  CloudArrowUpIcon,
} from '@heroicons/react/24/outline'
import { BellAlertIcon } from '@heroicons/react/24/solid'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Patients', href: '/patients', icon: UserGroupIcon },
  { name: 'CT Scans', href: '/scans', icon: DocumentMagnifyingGlassIcon },
  { name: 'Upload Scan', href: '/scans/upload', icon: CloudArrowUpIcon, radiologistOnly: true },
  { name: 'Reports', href: '/reports', icon: DocumentTextIcon },
  { name: 'Notifications', href: '/notifications', icon: BellIcon },
]

export default function Layout() {
  const { user, logout, isRadiologist } = useAuth()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const queryClient = useQueryClient()

  // Fetch unread notification count
  const { data: unreadData } = useQuery({
    queryKey: ['unreadNotifications'],
    queryFn: () => notificationApi.getUnreadCount(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const unreadCount = unreadData?.data?.unread_count || 0

  // WebSocket for real-time notifications
  const handleWebSocketMessage = useCallback((message) => {
    if (message.type === 'critical_alert') {
      toast.error(message.data.message, { duration: 10000 })
      // Play alert sound
      const audio = new Audio('/alert.mp3')
      audio.play().catch(() => {})
    } else if (message.type === 'scan_complete' || message.type === 'new_report') {
      toast.success(message.data.message)
    }
    
    // Refresh notification count
    queryClient.invalidateQueries(['unreadNotifications'])
  }, [queryClient])

  useWebSocket(handleWebSocketMessage)

  const filteredNavigation = navigation.filter(item => 
    !item.radiologistOnly || isRadiologist
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? '' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-900/80" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl">
          <div className="flex h-16 items-center justify-between px-4 border-b">
            <span className="text-xl font-bold text-primary-600">HemDetect</span>
            <button onClick={() => setSidebarOpen(false)} className="text-gray-500">
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          <nav className="p-4 space-y-1">
            {filteredNavigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  location.pathname === item.href
                    ? 'bg-primary-50 text-primary-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
                {item.name === 'Notifications' && unreadCount > 0 && (
                  <span className="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                    {unreadCount}
                  </span>
                )}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white border-r">
          <div className="flex h-16 items-center px-6 border-b">
            <span className="text-xl font-bold text-primary-600">HemDetect</span>
          </div>
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {filteredNavigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  location.pathname === item.href
                    ? 'bg-primary-50 text-primary-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
                {item.name === 'Notifications' && unreadCount > 0 && (
                  <span className="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                    {unreadCount}
                  </span>
                )}
              </Link>
            ))}
          </nav>
          <div className="p-4 border-t">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                <span className="text-primary-600 font-medium">
                  {user?.full_name?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.full_name}
                </p>
                <p className="text-xs text-gray-500 capitalize">
                  {user?.role}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Link
                to="/profile"
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                <UserCircleIcon className="h-4 w-4" />
                Profile
              </Link>
              <button
                onClick={logout}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
              >
                <ArrowLeftOnRectangleIcon className="h-4 w-4" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <div className="sticky top-0 z-40 flex h-16 items-center gap-4 bg-white border-b px-4 lg:hidden">
          <button onClick={() => setSidebarOpen(true)} className="text-gray-500">
            <Bars3Icon className="h-6 w-6" />
          </button>
          <span className="text-lg font-bold text-primary-600">HemDetect</span>
          <div className="ml-auto flex items-center gap-4">
            <Link to="/notifications" className="relative">
              {unreadCount > 0 ? (
                <BellAlertIcon className="h-6 w-6 text-red-500" />
              ) : (
                <BellIcon className="h-6 w-6 text-gray-500" />
              )}
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 flex items-center justify-center rounded-full">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Link>
          </div>
        </div>

        {/* Page content */}
        <main className="p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
