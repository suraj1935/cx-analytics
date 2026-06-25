import { useState } from 'react'
import { Modal } from '@/components/Common/Common'
import FileUpload from '@/components/Upload/FileUpload'
import DashboardContent from './DashboardContent'
import { Upload } from 'lucide-react'

export default function DashboardPage() {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleUploadSuccess = () => {
    setShowUploadModal(false)
    // Force DashboardContent to remount and refetch analytics data
    setRefreshKey((prev) => prev + 1)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">QA Analytics</h1>
          <p className="text-gray-600 mt-1">Real-time audit analytics and metrics</p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:shadow-lg transition-all font-medium"
        >
          <Upload className="w-5 h-5" />
          Upload Data
        </button>
      </div>

      <DashboardContent key={refreshKey} />

      <Modal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        title="Upload QA Data"
        size="lg"
      >
        <FileUpload onSuccess={handleUploadSuccess} />
      </Modal>
    </div>
  )
}
