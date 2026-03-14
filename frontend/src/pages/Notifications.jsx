import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationApi } from '../services/api'
import { PageHeader, Card, LoadingSpinner, EmptyState } from '../components/ui'
import { BellIcon, CheckIcon, TrashIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { formatDistanceToNow } from 'date-fns'
import { Link } from 'react-router-dom'

export default function Notifications() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationApi.getAll(),
  })

  const markReadMutation = useMutation({
    mutationFn: (ids) => notificationApi.markRead(ids),
    onSuccess: () => {
      queryClient.invalidateQueries(['notifications'])
      queryClient.invalidateQueries(['unreadNotifications'])
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationApi.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries(['notifications'])
      queryClient.invalidateQueries(['unreadNotifications'])
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => notificationApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['notifications'])
      queryClient.invalidateQueries(['unreadNotifications'])
    },
  })

  const notifications = data?.data?.notifications || []
  const unreadCount = data?.data?.unread_count || 0

  const getNotificationIcon = (type, priority) => {
    if (priority === 'critical') {
      return <ExclamationTriangleIcon className="h-6 w-6 text-red-600" />
    }
    return <BellIcon className="h-6 w-6 text-gray-400" />
  }

  const getNotificationLink = (notification) => {
    if (notification.scan_id) {
      return `/scans/${notification.scan_id}`
    }
    if (notification.report_id) {
      return `/reports/${notification.report_id}`
    }
    return null
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div>
      <PageHeader title="Notifications" subtitle={`${unreadCount} unread notifications`}>
        {unreadCount > 0 && (
          <button
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending}
            className="btn-secondary"
          >
            <CheckIcon className="h-5 w-5 mr-2" />
            Mark all as read
          </button>
        )}
      </PageHeader>

      {notifications.length === 0 ? (
        <EmptyState
          icon={BellIcon}
          title="No notifications"
          description="You're all caught up! Notifications will appear here."
        />
      ) : (
        <Card padding={false}>
          <ul className="divide-y divide-gray-200">
            {notifications.map((notification) => {
              const link = getNotificationLink(notification)
              const content = (
                <div className={`p-4 flex gap-4 ${!notification.is_read ? 'bg-blue-50' : ''} hover:bg-gray-50 transition-colors`}>
                  <div className="flex-shrink-0">
                    {getNotificationIcon(notification.type, notification.priority)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className={`text-sm ${!notification.is_read ? 'font-semibold' : 'font-medium'} text-gray-900`}>
                          {notification.title}
                        </p>
                        <p className="mt-1 text-sm text-gray-600">
                          {notification.message}
                        </p>
                        <p className="mt-1 text-xs text-gray-400">
                          {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {!notification.is_read && (
                          <button
                            onClick={(e) => {
                              e.preventDefault()
                              e.stopPropagation()
                              markReadMutation.mutate([notification.id])
                            }}
                            className="p-1 text-gray-400 hover:text-green-600"
                            title="Mark as read"
                          >
                            <CheckIcon className="h-5 w-5" />
                          </button>
                        )}
                        <button
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            deleteMutation.mutate(notification.id)
                          }}
                          className="p-1 text-gray-400 hover:text-red-600"
                          title="Delete"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                    {notification.priority === 'critical' && (
                      <span className="mt-2 inline-flex badge badge-danger">
                        Critical
                      </span>
                    )}
                  </div>
                </div>
              )

              return (
                <li key={notification.id}>
                  {link ? (
                    <Link to={link} onClick={() => {
                      if (!notification.is_read) {
                        markReadMutation.mutate([notification.id])
                      }
                    }}>
                      {content}
                    </Link>
                  ) : (
                    content
                  )}
                </li>
              )
            })}
          </ul>
        </Card>
      )}
    </div>
  )
}
