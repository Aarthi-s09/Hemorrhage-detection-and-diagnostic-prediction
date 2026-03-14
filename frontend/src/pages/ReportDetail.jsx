import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reportApi, authApi } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { PageHeader, Card, LoadingSpinner, SeverityBadge, StatusBadge, Modal } from '../components/ui'
import { ArrowLeftIcon, CheckIcon, PaperAirplaneIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function ReportDetail() {
  const { id } = useParams()
  const { isRadiologist, isDoctor } = useAuth()
  const queryClient = useQueryClient()
  const [showSendModal, setShowSendModal] = useState(false)
  const [selectedDoctor, setSelectedDoctor] = useState('')

  const { data: report, isLoading } = useQuery({
    queryKey: ['report', id],
    queryFn: () => reportApi.getById(id),
  })

  const { data: doctors } = useQuery({
    queryKey: ['doctors'],
    queryFn: () => authApi.getDoctors(),
    enabled: isRadiologist,
  })

  const verifyMutation = useMutation({
    mutationFn: () => reportApi.verify(id, { is_verified: true }),
    onSuccess: () => {
      toast.success('Report verified')
      queryClient.invalidateQueries(['report', id])
    },
  })

  const sendMutation = useMutation({
    mutationFn: (doctorId) => reportApi.send(id, { doctor_id: doctorId }),
    onSuccess: () => {
      toast.success('Report sent to doctor')
      setShowSendModal(false)
      queryClient.invalidateQueries(['report', id])
    },
  })

  const acknowledgeMutation = useMutation({
    mutationFn: () => reportApi.acknowledge(id),
    onSuccess: () => {
      toast.success('Report acknowledged')
      queryClient.invalidateQueries(['report', id])
    },
  })

  const generatePdfMutation = useMutation({
    mutationFn: () => reportApi.generatePdf(id),
    onSuccess: (response) => {
      toast.success('PDF generated successfully')
      // Download the PDF via the backend API
      const downloadUrl = `http://127.0.0.1:8082/api/v1/reports/${id}/pdf`
      // Open in new tab or trigger download
      window.open(downloadUrl, '_blank')
    },
    onError: (error) => {
      toast.error('Failed to generate PDF: ' + (error.response?.data?.detail || error.message))
    }
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const reportData = report?.data

  return (
    <div>
      <PageHeader
        title={reportData?.title}
        subtitle={`Report: ${reportData?.report_id}`}
      >
        <Link to="/reports" className="btn-secondary">
          <ArrowLeftIcon className="h-5 w-5 mr-2" />
          Back
        </Link>
      </PageHeader>

      {/* Critical Alert */}
      {reportData?.is_critical && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="font-bold text-red-900">⚠️ CRITICAL CASE</p>
          <p className="text-sm text-red-700">
            This report requires immediate attention. Severity: {reportData.severity_score?.toFixed(1)}%
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Report Content */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Findings</h3>
            <div className="prose prose-sm max-w-none">
              <p className="whitespace-pre-wrap">{reportData?.findings}</p>
            </div>
          </Card>

          {reportData?.recommendations && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
              <div className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap">{reportData.recommendations}</p>
              </div>
            </Card>
          )}

          {reportData?.radiologist_notes && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Radiologist Notes</h3>
              <div className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap">{reportData.radiologist_notes}</p>
              </div>
            </Card>
          )}

          {reportData?.conclusion && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Conclusion</h3>
              <div className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap">{reportData.conclusion}</p>
              </div>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Report Info</h3>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Status</dt>
                <dd><StatusBadge status={reportData?.status} /></dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Verified</dt>
                <dd>
                  {reportData?.is_verified ? (
                    <span className="text-green-600 font-medium">✓ Yes</span>
                  ) : (
                    <span className="text-gray-400">No</span>
                  )}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Severity Score</dt>
                <dd className="font-medium">
                  {reportData?.severity_score?.toFixed(1)}%
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Created</dt>
                <dd className="text-sm">
                  {new Date(reportData?.created_at).toLocaleString()}
                </dd>
              </div>
              {reportData?.sent_at && (
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Sent</dt>
                  <dd className="text-sm">
                    {new Date(reportData.sent_at).toLocaleString()}
                  </dd>
                </div>
              )}
            </dl>
          </Card>

          {/* Related Info */}
          {reportData?.scan_info && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Scan Info</h3>
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Scan ID</dt>
                  <dd className="text-sm font-medium">{reportData.scan_info.scan_id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Hemorrhage</dt>
                  <dd>
                    {reportData.scan_info.has_hemorrhage ? (
                      <span className="text-red-600 font-medium">Detected</span>
                    ) : (
                      <span className="text-green-600 font-medium">Not Detected</span>
                    )}
                  </dd>
                </div>
                <Link
                  to={`/scans/${reportData.scan_id}`}
                  className="btn-secondary w-full justify-center mt-4"
                >
                  View Scan
                </Link>
              </dl>
            </Card>
          )}

          {/* Actions */}
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions</h3>
            <div className="space-y-3">
              {/* Radiologist actions */}
              {isRadiologist && !reportData?.is_verified && (
                <button
                  onClick={() => verifyMutation.mutate()}
                  disabled={verifyMutation.isPending}
                  className="btn-success w-full justify-center"
                >
                  <CheckIcon className="h-5 w-5 mr-2" />
                  Verify Report
                </button>
              )}

              {isRadiologist && reportData?.is_verified && reportData?.status !== 'sent' && reportData?.status !== 'acknowledged' && (
                <button
                  onClick={() => setShowSendModal(true)}
                  className="btn-primary w-full justify-center"
                >
                  <PaperAirplaneIcon className="h-5 w-5 mr-2" />
                  Send to Doctor
                </button>
              )}

              {/* Doctor actions */}
              {isDoctor && reportData?.status === 'sent' && (
                <button
                  onClick={() => acknowledgeMutation.mutate()}
                  disabled={acknowledgeMutation.isPending}
                  className="btn-success w-full justify-center"
                >
                  <CheckIcon className="h-5 w-5 mr-2" />
                  Acknowledge Receipt
                </button>
              )}

              {/* PDF */}
              <button
                onClick={() => generatePdfMutation.mutate()}
                disabled={generatePdfMutation.isPending}
                className="btn-secondary w-full justify-center"
              >
                <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                {generatePdfMutation.isPending ? 'Generating...' : 'Download PDF'}
              </button>
            </div>
          </Card>
        </div>
      </div>

      {/* Send Modal */}
      <Modal isOpen={showSendModal} onClose={() => setShowSendModal(false)} title="Send Report to Doctor">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Select Doctor</label>
            <select
              value={selectedDoctor}
              onChange={(e) => setSelectedDoctor(e.target.value)}
              className="select mt-1"
            >
              <option value="">Choose a doctor...</option>
              {doctors?.data?.map((doctor) => (
                <option key={doctor.id} value={doctor.id}>
                  {doctor.full_name} - {doctor.specialty || doctor.department || 'General'}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-3">
            <button onClick={() => setShowSendModal(false)} className="btn-secondary">
              Cancel
            </button>
            <button
              onClick={() => sendMutation.mutate(parseInt(selectedDoctor))}
              disabled={!selectedDoctor || sendMutation.isPending}
              className="btn-primary"
            >
              {sendMutation.isPending ? 'Sending...' : 'Send Report'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
