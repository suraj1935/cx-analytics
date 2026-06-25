import { useState, useEffect } from 'react'
import type { User } from '@supabase/supabase-js'
import { apiClient } from '@/services/api'
import { supabase } from '@/services/supabase'
import Layout from '@/components/Layout/Layout'
import DashboardPage from '@/components/Dashboard/DashboardPage'
import AudioPage from '@/components/Audio/AudioPage'
import LoginPage from '@/components/Auth/LoginPage'
import SettingsPage from '@/components/Settings/SettingsPage'

type PageType = 'dashboard' | 'audio' | 'settings'
const isLocalE2EBypassEnabled = () =>
  window.location.hostname === '127.0.0.1' &&
  (
    window.sessionStorage.getItem('evolvs_e2e_auth') === 'true' ||
    new URLSearchParams(window.location.search).get('e2e') === '1'
  )

// ... rest of your React component logic
export default function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('audio')
  const [apiHealthy, setApiHealthy] = useState(true)
  const [loading, setLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const initialize = async () => {
      if (isLocalE2EBypassEnabled()) {
        setIsAuthenticated(true)
        setLoading(false)
        return
      }

      const { data } = await supabase.auth.getSession()
      setIsAuthenticated(Boolean(data.session))
      setUser(data.session?.user ?? null)

      const healthy = await apiClient.healthCheck()
      setApiHealthy(healthy)
      setLoading(false)
    }

    initialize()

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (isLocalE2EBypassEnabled()) {
        setIsAuthenticated(true)
        return
      }
      setIsAuthenticated(Boolean(session))
      setUser(session?.user ?? null)
    })

    return () => {
      listener.subscription.unsubscribe()
    }
  }, [])

  const handleLoginSuccess = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = async () => {
    window.sessionStorage.removeItem('evolvs_e2e_auth')
    await supabase.auth.signOut()
    setIsAuthenticated(false)
    setUser(null)
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
    <Layout currentPage={currentPage} onPageChange={setCurrentPage} onLogout={handleLogout} user={user}>
      {!apiHealthy && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-red-800">⚠️ Cannot connect to API</p>
        </div>
      )}

      {currentPage === 'dashboard' && <DashboardPage />}
      {currentPage === 'audio' && <AudioPage />}
      {currentPage === 'settings' && <SettingsPage />}
    </Layout>
  )
}
