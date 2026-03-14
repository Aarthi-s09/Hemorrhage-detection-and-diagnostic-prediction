import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { patientApi } from '../services/api'
import { PageHeader, Card, LoadingSpinner, EmptyState, Modal } from '../components/ui'
import { UserGroupIcon, PlusIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

const priorityColors = {
  low: 'bg-gray-100 text-gray-800',
  normal: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800 animate-pulse',
}

const PriorityBadge = ({ priority }) => (
  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${priorityColors[priority] || priorityColors.normal}`}>
    {priority?.toUpperCase()}
  </span>
)

export default function Patients() {
  const { user, isDoctor, isRadiologist } = useAuth()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['patients', page, search],
    queryFn: () => patientApi.getAll(page, 20, search),
  })

  const createMutation = useMutation({
    mutationFn: patientApi.create,
    onSuccess: () => {
      toast.success('Patient created successfully')
      queryClient.invalidateQueries(['patients'])
      setIsModalOpen(false)
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create patient')
    },
  })

  const patients = data?.data?.patients || []
  const total = data?.data?.total || 0
  const totalPages = Math.ceil(total / 20)

  // Only doctors can add patients
  const canAddPatient = isDoctor

  return (
    <div>
      <PageHeader title="Patients" subtitle={`${total} registered patients`}>
        {canAddPatient && (
          <button onClick={() => setIsModalOpen(true)} className="btn-primary">
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Patient
          </button>
        )}
      </PageHeader>

      {/* Search */}
      <Card className="mb-6">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search patients by name or ID..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            className="input pl-10"
          />
        </div>
      </Card>

      {/* Patient List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      ) : patients.length === 0 ? (
        <EmptyState
          icon={UserGroupIcon}
          title="No patients found"
          description={search ? "Try a different search term" : (canAddPatient ? "Add your first patient to get started" : "No patients have been added yet")}
          action={
            canAddPatient && (
              <button onClick={() => setIsModalOpen(true)} className="btn-primary">
                <PlusIcon className="h-5 w-5 mr-2" />
                Add Patient
              </button>
            )
          }
        />
      ) : (
        <Card padding={false}>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Priority</th>
                  <th>Patient ID</th>
                  <th>Name</th>
                  <th>Date of Birth</th>
                  <th>Gender</th>
                  <th>Added By</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {patients.map((patient) => (
                  <tr key={patient.id} className={patient.priority === 'urgent' ? 'bg-red-50' : patient.priority === 'high' ? 'bg-orange-50' : ''}>
                    <td><PriorityBadge priority={patient.priority} /></td>
                    <td className="font-medium">{patient.patient_id}</td>
                    <td>{patient.first_name} {patient.last_name}</td>
                    <td>{new Date(patient.date_of_birth).toLocaleDateString()}</td>
                    <td className="capitalize">{patient.gender}</td>
                    <td>
                      {patient.created_by_name ? (
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 text-xs rounded ${patient.created_by_role === 'doctor' ? 'bg-green-100 text-green-800' : 'bg-purple-100 text-purple-800'}`}>
                            {patient.created_by_role === 'doctor' ? 'Dr.' : 'Rad.'}
                          </span>
                          <span className="text-sm">{patient.created_by_name}</span>
                        </div>
                      ) : '-'}
                    </td>
                    <td>
                      <Link
                        to={`/patients/${patient.id}`}
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

          {/* Pagination */}
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

      {/* Add Patient Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Add New Patient" size="lg">
        <PatientForm 
          onSubmit={(data) => createMutation.mutate(data)} 
          isLoading={createMutation.isPending}
          isDoctor={isDoctor}
        />
      </Modal>
    </div>
  )
}

function PatientForm({ onSubmit, isLoading, initialData, isDoctor }) {
  const [formData, setFormData] = useState(initialData || {
    patient_id: '',
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'male',
    phone: '',
    email: '',
    address: '',
    medical_history: '',
    emergency_contact: '',
    emergency_phone: '',
    priority: 'normal',
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Priority Selection for Doctors */}
      {isDoctor && (
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <label className="block text-sm font-medium text-blue-900 mb-2">Case Priority</label>
          <div className="flex gap-4">
            {['low', 'normal', 'high', 'urgent'].map((p) => (
              <label key={p} className="flex items-center">
                <input
                  type="radio"
                  name="priority"
                  value={p}
                  checked={formData.priority === p}
                  onChange={handleChange}
                  className="mr-2"
                />
                <span className={`px-2 py-1 text-xs font-semibold rounded ${
                  p === 'low' ? 'bg-gray-100 text-gray-800' :
                  p === 'normal' ? 'bg-blue-100 text-blue-800' :
                  p === 'high' ? 'bg-orange-100 text-orange-800' :
                  'bg-red-100 text-red-800'
                }`}>{p.toUpperCase()}</span>
              </label>
            ))}
          </div>
          <p className="mt-2 text-xs text-blue-700">Urgent cases will be prioritized by radiologists</p>
        </div>
      )}
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Patient ID *</label>
          <input
            type="text"
            name="patient_id"
            required
            value={formData.patient_id}
            onChange={handleChange}
            className="input mt-1"
            placeholder="PAT-001"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Gender *</label>
          <select
            name="gender"
            required
            value={formData.gender}
            onChange={handleChange}
            className="select mt-1"
          >
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">First Name *</label>
          <input
            type="text"
            name="first_name"
            required
            value={formData.first_name}
            onChange={handleChange}
            className="input mt-1"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Last Name *</label>
          <input
            type="text"
            name="last_name"
            required
            value={formData.last_name}
            onChange={handleChange}
            className="input mt-1"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Date of Birth *</label>
          <input
            type="date"
            name="date_of_birth"
            required
            value={formData.date_of_birth}
            onChange={handleChange}
            className="input mt-1"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Phone</label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className="input mt-1"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className="input mt-1"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Emergency Contact</label>
          <input
            type="text"
            name="emergency_contact"
            value={formData.emergency_contact}
            onChange={handleChange}
            className="input mt-1"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Address</label>
        <input
          type="text"
          name="address"
          value={formData.address}
          onChange={handleChange}
          className="input mt-1"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Medical History</label>
        <textarea
          name="medical_history"
          rows={3}
          value={formData.medical_history}
          onChange={handleChange}
          className="input mt-1"
          placeholder="Previous conditions, allergies, medications..."
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? 'Saving...' : 'Save Patient'}
        </button>
      </div>
    </form>
  )
}
