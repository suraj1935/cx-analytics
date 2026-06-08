import { useState, useRef } from 'react'
import { Upload, File } from 'lucide-react'
import { useFileUpload } from '@/hooks/useApi'
import { Loading, Error } from '@/components/Common/Common'

interface FileUploadProps {
  onSuccess?: (data: any) => void
}

export default function FileUpload({ onSuccess }: FileUploadProps) {
  const { upload, uploading, error } = useFileUpload()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    try {
      const result = await upload(selectedFile)
      onSuccess?.(result)
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      console.error('Upload error:', err)
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  if (uploading) {
    return <Loading />
  }

  return (
    <div className="space-y-4">
      {error && <Error message={error} />}

      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors"
      >
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 mb-2 font-medium">
          Drag and drop your file here or click to browse
        </p>
        <p className="text-sm text-gray-500 mb-4">Accepted formats: CSV, XLSX</p>

        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileSelect}
          className="hidden"
          id="file-input"
        />
        <label
          htmlFor="file-input"
          className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer font-medium"
        >
          Select File
        </label>
      </div>

      {selectedFile && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <File className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-blue-900">{selectedFile.name}</p>
              <p className="text-sm text-blue-700 mt-1">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <button
              onClick={() => setSelectedFile(null)}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Clear
            </button>
          </div>

          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {uploading ? 'Uploading...' : 'Upload & Analyze'}
          </button>
        </div>
      )}
    </div>
  )
}
