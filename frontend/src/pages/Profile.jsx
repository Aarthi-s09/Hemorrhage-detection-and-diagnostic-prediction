import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { PageHeader, Card } from '../components/ui'
import toast from 'react-hot-toast'
import api from '../services/api'

export default function Profile() {
  const { user, updateProfile } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    specialty: user?.specialty || '',
    department: user?.department || '',
    phone: user?.phone || '',
  })
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [isLoading, setIsLoading] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handlePasswordChange = (e) => {
    const { name, value } = e.target
    setPasswordData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    const success = await updateProfile(formData)
    setIsLoading(false)
    if (success) {
      setIsEditing(false)
    }
  }

  const handlePasswordSubmit = async (e) => {
    e.preventDefault()
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('Passwords do not match')
      return
    }

    if (passwordData.new_password.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }

    setIsLoading(true)
    try {
      await api.post('/auth/change-password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      })
      toast.success('Password changed successfully')
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' })
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to change password')
    }
    setIsLoading(false)
  }

  return (
    <div>
      <PageHeader title="Profile" subtitle="Manage your account settings" />

      <div className="max-w-2xl mx-auto space-y-6">
        {/* Profile Info */}
        <Card>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Profile Information</h3>
            {!isEditing && (
              <button onClick={() => setIsEditing(true)} className="btn-secondary">
                Edit
              </button>
            )}
          </div>

          {isEditing ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Full Name</label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  className="input mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Specialty</label>
                <input
                  type="text"
                  name="specialty"
                  value={formData.specialty}
                  onChange={handleChange}
                  className="input mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Department</label>
                <input
                  type="text"
                  name="department"
                  value={formData.department}
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
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" disabled={isLoading} className="btn-primary">
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          ) : (
            <dl className="space-y-4">
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Email</dt>
                <dd className="text-sm font-medium text-gray-900">{user?.email}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Full Name</dt>
                <dd className="text-sm font-medium text-gray-900">{user?.full_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Role</dt>
                <dd className="text-sm font-medium text-gray-900 capitalize">{user?.role}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Specialty</dt>
                <dd className="text-sm font-medium text-gray-900">{user?.specialty || '-'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Department</dt>
                <dd className="text-sm font-medium text-gray-900">{user?.department || '-'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500">Phone</dt>
                <dd className="text-sm font-medium text-gray-900">{user?.phone || '-'}</dd>
              </div>
            </dl>
          )}
        </Card>

        {/* Change Password */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Change Password</h3>
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Current Password</label>
              <input
                type="password"
                name="current_password"
                value={passwordData.current_password}
                onChange={handlePasswordChange}
                className="input mt-1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">New Password</label>
              <input
                type="password"
                name="new_password"
                value={passwordData.new_password}
                onChange={handlePasswordChange}
                className="input mt-1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
              <input
                type="password"
                name="confirm_password"
                value={passwordData.confirm_password}
                onChange={handlePasswordChange}
                className="input mt-1"
              />
            </div>
            <div className="flex justify-end pt-4">
              <button type="submit" disabled={isLoading} className="btn-primary">
                {isLoading ? 'Changing...' : 'Change Password'}
              </button>
            </div>
          </form>
        </Card>

        {/* Account Info */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Status</h3>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Account Status</dt>
              <dd>
                {user?.is_active ? (
                  <span className="badge badge-success">Active</span>
                ) : (
                  <span className="badge badge-danger">Inactive</span>
                )}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Verification</dt>
              <dd>
                {user?.is_verified ? (
                  <span className="badge badge-success">Verified</span>
                ) : (
                  <span className="badge badge-warning">Pending</span>
                )}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Member Since</dt>
              <dd className="text-sm font-medium text-gray-900">
                {new Date(user?.created_at).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        </Card>
      </div>
    </div>
  )
}
