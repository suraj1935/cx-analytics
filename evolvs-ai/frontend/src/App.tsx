import { useState, useEffect } from 'react'
import { apiClient } from '@/services/api'
import Layout from '@/components/Layout/Layout'
import DashboardPage from '@/components/Dashboard/DashboardPage'
import AudioPage from '@/components/Audio/AudioPage'
import LoginPage from '@/components/Auth/LoginPage'

type PageType = 'dashboard' | 'audio'

export default function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard')
  const [apiHealthy, setApiHealthy] = useState(true)
  const [loading, setLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('evolvs_auth') === 'true'
  })

  useEffect(() => {
    const checkHealth = async () => {
      const healthy = await apiClient.healthCheck()
      setApiHealthy(healthy)
      setLoading(false)
    }

    checkHealth()
  }, [])

  const handleLoginSuccess = () => {
    localStorage.setItem('evolvs_auth', 'true')
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('evolvs_auth')
    setIsAuthenticated(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading EvolvS AI...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />
  }

  return (
    <Layout currentPage={currentPage} onPageChange={setCurrentPage} onLogout={handleLogout}>
      {!apiHealthy && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-red-800">⚠️ Cannot connect to API</p>
        </div>
      )}

      {currentPage === 'dashboard' && <DashboardPage />}
      {currentPage === 'audio' && <AudioPage />}
    </Layout>
  )
}
