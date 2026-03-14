import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { scanApi, patientApi } from '../services/api'
import { PageHeader, Card, LoadingSpinner } from '../components/ui'
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function UploadScan() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [patientId, setPatientId] = useState('')
  const [patientSearch, setPatientSearch] = useState('')
  const [scanType, setScanType] = useState('CT Head')
  const [notes, setNotes] = useState('')
  const [dragActive, setDragActive] = useState(false)

  // Search patients
  const { data: patients } = useQuery({
    queryKey: ['patientSearch', patientSearch],
    queryFn: () => patientApi.search(patientSearch),
    enabled: patientSearch.length >= 1,
  })

  const uploadMutation = useMutation({
    mutationFn: (formData) => scanApi.upload(formData),
    onSuccess: (response) => {
      toast.success('Scan uploaded successfully! Analysis in progress...')
      navigate(`/scans/${response.data.id}`)
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to upload scan')
    },
  })

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }, [])

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!file) {
      toast.error('Please select a file')
      return
    }
    
    if (!patientId) {
      toast.error('Please select a patient')
      return
    }

    const formData = new FormData()
    formData.append('file', file)
    formData.append('patient_id', patientId)
    formData.append('scan_type', scanType)
    if (notes) formData.append('notes', notes)

    uploadMutation.mutate(formData)
  }

  return (
    <div>
      <PageHeader
        title="Upload CT Scan"
        subtitle="Upload a new CT scan for hemorrhage analysis"
      />

      <div className="max-w-3xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Patient Selection */}
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Patient Information</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Search Patient *
                </label>
                <input
                  type="text"
                  value={patientSearch}
                  onChange={(e) => setPatientSearch(e.target.value)}
                  className="input mt-1"
                  placeholder="Search by name or ID..."
                />
                
                {patients?.data?.length > 0 && (
                  <div className="mt-2 border rounded-lg divide-y max-h-48 overflow-y-auto">
                    {patients.data.map((patient) => (
                      <button
                        key={patient.id}
                        type="button"
                        onClick={() => {
                          setPatientId(patient.id)
                          setPatientSearch(patient.full_name)
                        }}
                        className={`w-full px-4 py-2 text-left hover:bg-gray-50 ${
                          patientId === patient.id ? 'bg-primary-50' : ''
                        }`}
                      >
                        <p className="font-medium">{patient.full_name}</p>
                        <p className="text-sm text-gray-500">ID: {patient.patient_id}</p>
                      </button>
                    ))}
                  </div>
                )}
                
                {patientId && (
                  <p className="mt-2 text-sm text-green-600">
                    ✓ Patient selected
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Scan Type
                </label>
                <select
                  value={scanType}
                  onChange={(e) => setScanType(e.target.value)}
                  className="select mt-1"
                >
                  <option value="CT Head">CT Head</option>
                  <option value="CT Head with Contrast">CT Head with Contrast</option>
                  <option value="CT Angiography">CT Angiography</option>
                </select>
              </div>
            </div>
          </Card>

          {/* File Upload */}
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">CT Scan File</h3>
            
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive
                  ? 'border-primary-500 bg-primary-50'
                  : file
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              {file ? (
                <div className="flex items-center justify-center gap-4">
                  <DocumentIcon className="h-12 w-12 text-green-600" />
                  <div className="text-left">
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <XMarkIcon className="h-5 w-5 text-gray-500" />
                  </button>
                </div>
              ) : (
                <>
                  <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <div className="mt-4">
                    <label className="cursor-pointer">
                      <span className="text-primary-600 hover:text-primary-500 font-medium">
                        Upload a file
                      </span>
                      <input
                        type="file"
                        className="hidden"
                        accept=".jpg,.jpeg,.png,.dcm,.dicom"
                        onChange={handleFileChange}
                      />
                    </label>
                    <span className="text-gray-500"> or drag and drop</span>
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    DICOM, JPG, JPEG, PNG up to 500MB
                  </p>
                </>
              )}
            </div>
          </Card>

          {/* Notes */}
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Notes</h3>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              className="input"
              placeholder="Clinical notes, symptoms, or additional context..."
            />
          </Card>

          {/* Submit */}
          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={() => navigate('/scans')}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploadMutation.isPending || !file || !patientId}
              className="btn-primary"
            >
              {uploadMutation.isPending ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Uploading...
                </>
              ) : (
                <>
                  <CloudArrowUpIcon className="h-5 w-5 mr-2" />
                  Upload & Analyze
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
