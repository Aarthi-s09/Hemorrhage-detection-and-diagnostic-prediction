import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    // Check if user is logged in
    const isAuthenticated = localStorage.getItem('isAuthenticated')
    const userRole = localStorage.getItem('userRole')
    const userName = localStorage.getItem('userName')
    
    if (isAuthenticated === 'true' && userRole) {
      setUser({
        role: userRole,
        full_name: userName,
        email: `${userRole}@hemdetect.com`
      })
    }
    setIsLoading(false)
  }, [])

  const login = (role, userName) => {
    // Set localStorage
    localStorage.setItem('userRole', role)
    localStorage.setItem('userName', userName)
    localStorage.setItem('isAuthenticated', 'true')
    
    // Update state
    setUser({
      role: role,
      full_name: userName,
      email: `${role}@hemdetect.com`
    })
    
    // Navigate to dashboard
    toast.success(`Welcome ${role === 'doctor' ? 'Doctor' : 'Radiologist'}!`)
    navigate('/dashboard')
  }

  const logout = () => {
    localStorage.clear()
    setUser(null)
    toast.success('Logged out successfully')
    navigate('/login')
  }

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    isRadiologist: user?.role === 'radiologist',
    isDoctor: user?.role === 'doctor',
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
