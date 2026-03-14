import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { scanApi, reportApi } from '../services/api'
import { PageHeader, Card, LoadingSpinner, SeverityBadge, StatusBadge, Modal } from '../components/ui'
import { ArrowLeftIcon, DocumentTextIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

export default function ScanDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isRadiologist } = useAuth()
  const queryClient = useQueryClient()
  const [currentSlice, setCurrentSlice] = useState(0)
  const [showHeatmap, setShowHeatmap] = useState(false)

  const { data: scan, isLoading, refetch } = useQuery({
    queryKey: ['scan', id],
    queryFn: () => scanApi.getById(id),
    refetchInterval: (data) => {
      // Poll while processing
      if (data?.data?.status === 'processing' || data?.data?.status === 'pending') {
        return 3000
      }
      return false
    },
  })

  const { data: viewerData } = useQuery({
    queryKey: ['scanViewer', id],
    queryFn: () => scanApi.getViewer(id),
    enabled: scan?.data?.status === 'completed',
  })

  const reprocessMutation = useMutation({
    mutationFn: () => scanApi.reprocess(id),
    onSuccess: () => {
      toast.success('Scan queued for reprocessing')
      refetch()
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const scanData = scan?.data
  const slices = viewerData?.data?.slice_urls || []
  const heatmaps = viewerData?.data?.heatmap_urls || []

  return (
    <div>
      <PageHeader
        title={`Scan: ${scanData?.scan_id}`}
        subtitle={scanData?.patient_name ? `Patient: ${scanData.patient_name}` : ''}
      >
        <Link to="/scans" className="btn-secondary">
          <ArrowLeftIcon className="h-5 w-5 mr-2" />
          Back
        </Link>
      </PageHeader>

      {/* Status Banner */}
      {scanData?.status === 'processing' && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-4">
          <LoadingSpinner size="md" />
          <div>
            <p className="font-medium text-blue-900">Analysis in Progress</p>
            <p className="text-sm text-blue-700">
              The AI model is analyzing this scan. This page will update automatically.
            </p>
          </div>
        </div>
      )}

      {scanData?.severity_level === 'severe' && scanData?.status === 'completed' && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 animate-pulse">
          <p className="font-bold text-red-900">⚠️ CRITICAL: Severe Hemorrhage Detected</p>
          <p className="text-sm text-red-700">
            Immediate medical attention required. Spread ratio: {scanData.spread_ratio?.toFixed(1)}%
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CT Viewer */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">CT Viewer</h3>
            {heatmaps.length > 0 && (
              <button
                onClick={() => setShowHeatmap(!showHeatmap)}
                className={`btn ${showHeatmap ? 'btn-primary' : 'btn-secondary'}`}
              >
                {showHeatmap ? 'Show Original' : 'Show Heatmap'}
              </button>
            )}
          </div>

          {slices.length > 0 ? (
            <div className="space-y-4">
              <div className="aspect-square bg-black rounded-lg overflow-hidden flex items-center justify-center">
                <img
                  src={showHeatmap && heatmaps[currentSlice] ? heatmaps[currentSlice] : slices[currentSlice]}
                  alt={`CT Slice ${currentSlice + 1}`}
                  className="max-w-full max-h-full object-contain"
                />
              </div>
              
              {slices.length > 1 && (
                <div>
                  <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                    <span>Slice {currentSlice + 1} of {slices.length}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={slices.length - 1}
                    value={currentSlice}
                    onChange={(e) => setCurrentSlice(Number(e.target.value))}
                    className="w-full"
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center">
              {scanData?.status === 'completed' ? (
                <p className="text-gray-500">No preview available</p>
              ) : (
                <div className="text-center">
                  <LoadingSpinner size="lg" className="mx-auto mb-4" />
                  <p className="text-gray-500">Processing scan...</p>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* Analysis Results */}
        <div className="space-y-6">
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Scan Information</h3>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Status</dt>
                <dd><StatusBadge status={scanData?.status} /></dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Scan Date</dt>
                <dd className="text-sm font-medium">
                  {new Date(scanData?.scan_date).toLocaleString()}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Scan Type</dt>
                <dd className="text-sm font-medium">{scanData?.scan_type}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Slices</dt>
                <dd className="text-sm font-medium">{scanData?.num_slices || slices.length}</dd>
              </div>
            </dl>
          </Card>

          {scanData?.status === 'completed' && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Results</h3>
              <dl className="space-y-3">
                <div className="flex justify-between items-center">
                  <dt className="text-sm text-gray-500">Detection</dt>
                  <dd>
                    {scanData.has_hemorrhage ? (
                      <span className="font-bold text-red-600">HEMORRHAGE DETECTED</span>
                    ) : (
                      <span className="font-bold text-green-600">NORMAL</span>
                    )}
                  </dd>
                </div>
                <div className="flex justify-between items-center">
                  <dt className="text-sm text-gray-500">Severity</dt>
                  <dd><SeverityBadge level={scanData.severity_level} /></dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Confidence</dt>
                  <dd className="text-sm font-medium">
                    {(scanData.confidence_score * 100).toFixed(1)}%
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Spread Ratio</dt>
                  <dd className="text-sm font-medium">
                    {scanData.spread_ratio?.toFixed(1)}%
                  </dd>
                </div>
                {scanData.hemorrhage_type && scanData.hemorrhage_type !== 'none' && (
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Type</dt>
                    <dd className="text-sm font-medium capitalize">
                      {scanData.hemorrhage_type.replace('_', ' ')}
                    </dd>
                  </div>
                )}
              </dl>

              {scanData.affected_regions?.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <dt className="text-sm text-gray-500 mb-2">Affected Regions</dt>
                  <div className="flex flex-wrap gap-2">
                    {scanData.affected_regions.map((region, i) => (
                      <span key={i} className="badge badge-info">
                        {region}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Actions */}
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions</h3>
            <div className="space-y-3">
              {scanData?.report && (
                <Link
                  to={`/reports/${scanData.report.id}`}
                  className="btn-primary w-full justify-center"
                >
                  <DocumentTextIcon className="h-5 w-5 mr-2" />
                  View Report
                </Link>
              )}
              
              {isRadiologist && scanData?.status === 'completed' && !scanData?.report && (
                <Link
                  to={`/reports?scan=${id}`}
                  className="btn-primary w-full justify-center"
                >
                  <DocumentTextIcon className="h-5 w-5 mr-2" />
                  Create Report
                </Link>
              )}

              {isRadiologist && (
                <button
                  onClick={() => reprocessMutation.mutate()}
                  disabled={reprocessMutation.isPending || scanData?.status === 'processing'}
                  className="btn-secondary w-full justify-center"
                >
                  <ArrowPathIcon className="h-5 w-5 mr-2" />
                  Reprocess Scan
                </button>
              )}
            </div>
          </Card>

          {/* Notes */}
          {scanData?.notes && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Clinical Notes</h3>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{scanData.notes}</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
