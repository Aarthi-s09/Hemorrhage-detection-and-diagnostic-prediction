import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8082/api/v1'

// Track 401 errors to detect invalid tokens
let consecutiveAuthErrors = 0
const MAX_AUTH_ERRORS = 2

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - NO AUTH for development
api.interceptors.request.use(
  (config) => {
    // Skip adding token for now
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - disabled for development
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Just pass through errors without auth handling
    return Promise.reject(error)
  }
)

export default api

// API helper functions
export const patientApi = {
  getAll: (page = 1, size = 20, search = '') => 
    api.get(`/patients?page=${page}&size=${size}${search ? `&search=${search}` : ''}`),
  getById: (id) => api.get(`/patients/${id}`),
  create: (data) => api.post('/patients', data),
  update: (id, data) => api.put(`/patients/${id}`, data),
  delete: (id) => api.delete(`/patients/${id}`),
  search: (query) => api.get(`/patients/search?q=${query}`),
}

export const scanApi = {
  getAll: (page = 1, size = 20, status = '') => 
    api.get(`/scans?page=${page}&size=${size}${status ? `&status=${status}` : ''}`),
  getById: (id) => api.get(`/scans/${id}`),
  upload: (formData) => api.post('/scans/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getRecent: (limit = 10) => api.get(`/scans/recent?limit=${limit}`),
  getCritical: (limit = 10) => api.get(`/scans/critical?limit=${limit}`),
  getViewer: (id) => api.get(`/scans/${id}/viewer`),
  reprocess: (id) => api.post(`/scans/${id}/reprocess`),
  delete: (id) => api.delete(`/scans/${id}`),
}

export const reportApi = {
  getAll: (page = 1, size = 20, status = '') => 
    api.get(`/reports?page=${page}&size=${size}${status ? `&status=${status}` : ''}`),
  getById: (id) => api.get(`/reports/${id}`),
  create: (data) => api.post('/reports', data),
  update: (id, data) => api.put(`/reports/${id}`, data),
  verify: (id, data) => api.post(`/reports/${id}/verify`, data),
  send: (id, data) => api.post(`/reports/${id}/send`, data),
  acknowledge: (id) => api.post(`/reports/${id}/acknowledge`),
  generatePdf: (id) => api.post(`/reports/${id}/generate-pdf`),
  getPending: () => api.get('/reports/pending'),
}

export const notificationApi = {
  getAll: (unreadOnly = false) => 
    api.get(`/notifications?unread_only=${unreadOnly}`),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  getCritical: () => api.get('/notifications/critical'),
  markRead: (ids) => api.post('/notifications/mark-read', { notification_ids: ids }),
  markAllRead: () => api.post('/notifications/mark-all-read'),
  delete: (id) => api.delete(`/notifications/${id}`),
}

export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
  getRadiologist: () => api.get('/dashboard/radiologist'),
  getDoctor: () => api.get('/dashboard/doctor'),
  getSeverityDistribution: (days = 30) => 
    api.get(`/dashboard/severity-distribution?days=${days}`),
  getTrend: (days = 30) => api.get(`/dashboard/trend?days=${days}`),
}

export const authApi = {
  getDoctors: () => api.get('/auth/doctors'),
}
