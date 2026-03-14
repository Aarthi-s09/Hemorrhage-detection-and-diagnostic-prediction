import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { scanApi } from '../services/api'
import { PageHeader, Card, LoadingSpinner, EmptyState, SeverityBadge, StatusBadge } from '../components/ui'
import { DocumentMagnifyingGlassIcon, CloudArrowUpIcon, FunnelIcon } from '@heroicons/react/24/outline'
import { useAuth } from '../context/AuthContext'

export default function Scans() {
  const { isRadiologist } = useAuth()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['scans', page, statusFilter],
    queryFn: () => scanApi.getAll(page, 20, statusFilter),
  })

  const scans = data?.data?.scans || []
  const total = data?.data?.total || 0
  const totalPages = Math.ceil(total / 20)

  return (
    <div>
      <PageHeader title="CT Scans" subtitle={`${total} total scans`}>
        {isRadiologist && (
          <Link to="/scans/upload" className="btn-primary">
            <CloudArrowUpIcon className="h-5 w-5 mr-2" />
            Upload Scan
          </Link>
        )}
      </PageHeader>

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
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </Card>

      {/* Scan List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      ) : scans.length === 0 ? (
        <EmptyState
          icon={DocumentMagnifyingGlassIcon}
          title="No scans found"
          description="Upload your first CT scan to get started"
          action={
            isRadiologist && (
              <Link to="/scans/upload" className="btn-primary">
                <CloudArrowUpIcon className="h-5 w-5 mr-2" />
                Upload Scan
              </Link>
            )
          }
        />
      ) : (
        <Card padding={false}>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Scan ID</th>
                  <th>Patient</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th>Result</th>
                  <th>Severity</th>
                  <th>Confidence</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {scans.map((scan) => (
                  <tr key={scan.id} className={scan.severity_level === 'severe' ? 'bg-red-50' : ''}>
                    <td className="font-medium">{scan.scan_id}</td>
                    <td>Patient #{scan.patient_id}</td>
                    <td>{new Date(scan.scan_date).toLocaleDateString()}</td>
                    <td><StatusBadge status={scan.status} /></td>
                    <td>
                      {scan.status === 'completed' && (
                        scan.has_hemorrhage ? (
                          <span className="text-red-600 font-medium">Positive</span>
                        ) : (
                          <span className="text-green-600 font-medium">Negative</span>
                        )
                      )}
                      {scan.status === 'processing' && (
                        <span className="text-blue-600">Analyzing...</span>
                      )}
                    </td>
                    <td>
                      {scan.status === 'completed' && (
                        <SeverityBadge level={scan.severity_level} />
                      )}
                    </td>
                    <td>
                      {scan.confidence_score ? (
                        <span className={scan.confidence_score > 0.8 ? 'text-green-600' : 'text-yellow-600'}>
                          {(scan.confidence_score * 100).toFixed(1)}%
                        </span>
                      ) : '-'}
                    </td>
                    <td>
                      <Link
                        to={`/scans/${scan.id}`}
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
