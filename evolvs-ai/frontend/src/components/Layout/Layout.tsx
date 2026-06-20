import Header from './Header'
import Sidebar from './Sidebar'
import type { User } from '@supabase/supabase-js'

type PageType = 'dashboard' | 'audio'

interface LayoutProps {
  children: React.ReactNode
  currentPage: PageType
  onPageChange: (page: PageType) => void
  onLogout: () => void
  user: User | null
}

export default function Layout({ children, currentPage, onPageChange, onLogout, user }: LayoutProps) {
  return (
    <div className="flex h-screen bg-gray-100 font-sans">
      <Sidebar currentPage={currentPage} onPageChange={onPageChange} onLogout={onLogout} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header user={user} />
        <main className="flex-1 overflow-auto">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
