import { BarChart3 } from 'lucide-react'
import type { User } from '@supabase/supabase-js'

interface HeaderProps {
  user: User | null
}

export default function Header({ user }: HeaderProps) {
  const displayName = user?.email ?? 'Signed in'
  const authMode = user?.is_anonymous ? 'Anonymous session' : 'Supabase Auth'

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">EvolvS AI</h1>
            <p className="text-xs text-gray-500">QA Automation</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-900">{displayName}</p>
          <p className="text-xs text-gray-500">{authMode}</p>
        </div>
      </div>
    </header>
  )
}
