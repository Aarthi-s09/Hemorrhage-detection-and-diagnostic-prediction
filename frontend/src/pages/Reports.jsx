import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { reportApi } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { PageHeader, Card, LoadingSpinner, EmptyState, SeverityBadge, StatusBadge } from '../components/ui'
import { DocumentTextIcon, FunnelIcon } from '@heroicons/react/24/outline'

export default function Reports() {
  const { isRadiologist, isDoctor } = useAuth()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['reports', page, statusFilter],
    queryFn: () => reportApi.getAll(page, 20, statusFilter),
  })

  const reports = data?.data?.reports || []
  const total = data?.data?.total || 0
  const totalPages = Math.ceil(total / 20)

  return (
    <div>
      <PageHeader title="Medical Reports" subtitle={`${total} total reports`} />

      {/* Filters */}
      <Card className="mb-6">
        <div className="flex items-center gap-4">
          <FunnelIcon className="h-5 w-5 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value)
              setPage(1)
            }}
            className="select max-w-xs"
          >
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="pending_review">Pending Review</option>
            <option value="reviewed">Reviewed</option>
            <option value="sent">Sent</option>
            <option value="acknowledged">Acknowledged</option>
          </select>
        </div>
      </Card>

      {/* Report List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      ) : reports.length === 0 ? (
        <EmptyState
          icon={DocumentTextIcon}
          title="No reports found"
          description="Reports will appear here after scan analysis"
        />
      ) : (
        <Card padding={false}>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Report ID</th>
                  <th>Title</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Verified</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {reports.map((report) => (
                  <tr key={report.id} className={report.is_critical ? 'bg-red-50' : ''}>
                    <td className="font-medium">{report.report_id}</td>
                    <td className="max-w-xs truncate">{report.title}</td>
                    <td>
                      {report.severity_score !== null ? (
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{report.severity_score.toFixed(1)}%</span>
                          {report.is_critical && (
                            <span className="badge badge-danger">Critical</span>
                          )}
                        </div>
                      ) : '-'}
                    </td>
                    <td><StatusBadge status={report.status} /></td>
                    <td>
                      {report.is_verified ? (
                        <span className="text-green-600">✓ Verified</span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="text-gray-500">
                      {new Date(report.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <Link
                        to={`/reports/${report.id}`}
                        className="text-primary-600 hover:text-primary-900 font-medium"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <p className="text-sm text-gray-700">
                Showing page {page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="btn-secondary"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
