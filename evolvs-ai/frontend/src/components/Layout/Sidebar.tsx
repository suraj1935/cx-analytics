import { BarChart3, Mic2 } from 'lucide-react'

type PageType = 'dashboard' | 'audio'

interface SidebarProps {
  currentPage: PageType
  onPageChange: (page: PageType) => void
}

export default function Sidebar({ currentPage, onPageChange }: SidebarProps) {
  const menuItems = [
    { id: 'dashboard' as const, label: 'Dashboard', icon: BarChart3 },
    { id: 'audio' as const, label: 'Audio Transcription', icon: Mic2 },
  ]

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col shadow-lg">
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-5 h-5" />
          <div>
            <p className="font-bold">EvolvS AI</p>
            <p className="text-xs text-gray-400">v1.0</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = currentPage === item.id

          return (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              className={`w-full text-left px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${
                isActive
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium text-sm">{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <p className="text-xs text-gray-500">Zero-budget QA SaaS</p>
      </div>
    </aside>
  )
}
