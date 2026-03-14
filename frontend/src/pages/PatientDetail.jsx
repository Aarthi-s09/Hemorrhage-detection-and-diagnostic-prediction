import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { patientApi, scanApi } from '../services/api'
import { PageHeader, Card, LoadingSpinner, SeverityBadge, StatusBadge } from '../components/ui'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'

export default function PatientDetail() {
  const { id } = useParams()

  const { data: patient, isLoading } = useQuery({
    queryKey: ['patient', id],
    queryFn: () => patientApi.getById(id),
  })

  const { data: scans } = useQuery({
    queryKey: ['patientScans', id],
    queryFn: () => scanApi.getAll(1, 50, '', id),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const patientData = patient?.data

  return (
    <div>
      <PageHeader
        title={`${patientData?.first_name} ${patientData?.last_name}`}
        subtitle={`Patient ID: ${patientData?.patient_id}`}
      >
        <Link to="/patients" className="btn-secondary">
          <ArrowLeftIcon className="h-5 w-5 mr-2" />
          Back
        </Link>
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Patient Info */}
        <Card className="lg:col-span-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Patient Information</h3>
          <dl className="space-y-4">
            <div>
              <dt className="text-sm text-gray-500">Date of Birth</dt>
              <dd className="text-sm font-medium text-gray-900">
                {new Date(patientData?.date_of_birth).toLocaleDateString()}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Age</dt>
              <dd className="text-sm font-medium text-gray-900">{patientData?.age} years</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Gender</dt>
              <dd className="text-sm font-medium text-gray-900 capitalize">{patientData?.gender}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Phone</dt>
              <dd className="text-sm font-medium text-gray-900">{patientData?.phone || '-'}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Email</dt>
              <dd className="text-sm font-medium text-gray-900">{patientData?.email || '-'}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Address</dt>
              <dd className="text-sm font-medium text-gray-900">{patientData?.address || '-'}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Emergency Contact</dt>
              <dd className="text-sm font-medium text-gray-900">
                {patientData?.emergency_contact || '-'}
                {patientData?.emergency_phone && ` (${patientData.emergency_phone})`}
              </dd>
            </div>
          </dl>
        </Card>

        {/* Medical History */}
        <Card className="lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Medical History</h3>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">
            {patientData?.medical_history || 'No medical history recorded.'}
          </p>
        </Card>

        {/* CT Scans */}
        <Card className="lg:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">CT Scans</h3>
            <Link to="/scans/upload" className="btn-primary text-sm">
              Upload New Scan
            </Link>
          </div>
          
          {scans?.data?.scans?.length > 0 ? (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Scan ID</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Result</th>
                    <th>Severity</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {scans.data.scans.map((scan) => (
                    <tr key={scan.id}>
                      <td className="font-medium">{scan.scan_id}</td>
                      <td>{new Date(scan.scan_date).toLocaleDateString()}</td>
                      <td><StatusBadge status={scan.status} /></td>
                      <td>
                        {scan.has_hemorrhage ? (
                          <span className="text-red-600 font-medium">Hemorrhage Detected</span>
                        ) : scan.status === 'completed' ? (
                          <span className="text-green-600 font-medium">Normal</span>
                        ) : '-'}
                      </td>
                      <td>
                        {scan.status === 'completed' && (
                          <SeverityBadge level={scan.severity_level} />
                        )}
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
          ) : (
            <p className="text-gray-500 text-center py-8">No scans recorded for this patient.</p>
          )}
        </Card>
      </div>
    </div>
  )
}
