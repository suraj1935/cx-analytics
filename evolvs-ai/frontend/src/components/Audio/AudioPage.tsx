import { useState, useRef } from 'react'
import { Card, Error } from '@/components/Common/Common'
import { useAudioUpload } from '@/hooks/useApi'
import { 
  Mic2, Upload, FileAudio, Clock, 
  FileText, Download, RotateCcw, Calendar, FileDown
} from 'lucide-react'
import { AudioTranscript } from '@/types'

interface VTTSegment {
  start: string
  end: string
  text: string
  seconds: number
}

function parseVTT(vttText: string): VTTSegment[] {
  const segments: VTTSegment[] = []
  const lines = vttText.split('\n')
  let currentSegment: Partial<VTTSegment> = {}
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (line.includes('-->')) {
      const parts = line.split('-->')
      const start = parts[0].trim()
      const end = parts[1].trim()
      
      const startParts = start.split(':')
      let seconds = 0
      if (startParts.length === 3) {
        seconds = parseFloat(startParts[0]) * 3600 + parseFloat(startParts[1]) * 60 + parseFloat(startParts[2])
      } else if (startParts.length === 2) {
        seconds = parseFloat(startParts[0]) * 60 + parseFloat(startParts[1])
      }
      
      currentSegment = { start, end, seconds }
    } else if (line && !line.startsWith('WEBVTT') && Object.keys(currentSegment).length > 0) {
      currentSegment.text = line
      segments.push(currentSegment as VTTSegment)
      currentSegment = {}
    }
  }
  return segments
}

export default function AudioPage() {
  const { upload, uploading, error } = useAudioUpload()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [transcriptData, setTranscriptData] = useState<AudioTranscript | null>(null)
  const [activeTab, setActiveTab] = useState<'interactive' | 'raw' | 'text'>('interactive')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const [currentTime, setCurrentTime] = useState(0)

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
      setTranscriptData(result)
    } catch (err) {
      console.error('Audio upload failed:', err)
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleTimeClick = (seconds: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = seconds
      audioRef.current.play()
    }
  }

  const resetAll = () => {
    setSelectedFile(null)
    setTranscriptData(null)
    setCurrentTime(0)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const downloadText = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const parsedSegments = transcriptData ? parseVTT(transcriptData.vtt_content) : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Mic2 className="w-8 h-8 text-blue-600" />
            Audio Transcription
          </h1>
          <p className="text-gray-600 mt-1">
            Convert call recordings to text with automatic VTT subtitles
          </p>
        </div>
        {transcriptData && (
          <button
            onClick={resetAll}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
          >
            <RotateCcw className="w-4 h-4" />
            Transcribe New
          </button>
        )}
      </div>

      {error && <Error message={error} />}

      {!transcriptData && !uploading && (
        <div className="max-w-3xl mx-auto space-y-6">
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className="border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center hover:border-blue-500 hover:bg-blue-50/30 transition-all duration-300 shadow-sm bg-white"
          >
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <Upload className="w-8 h-8 text-blue-600 animate-bounce" />
            </div>
            <p className="text-lg text-gray-700 mb-2 font-semibold">
              Drag and drop your audio file here or click to browse
            </p>
            <p className="text-sm text-gray-500 mb-6 max-w-md mx-auto">
              Supported formats: WAV, MP3, FLAC, OGG, M4A
            </p>

            <input
              ref={fileInputRef}
              type="file"
              accept=".wav,.mp3,.flac,.ogg,.m4a"
              onChange={handleFileSelect}
              className="hidden"
              id="audio-input"
            />
            <label
              htmlFor="audio-input"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:shadow-lg transition-all cursor-pointer font-medium"
            >
              <FileAudio className="w-5 h-5" />
              Select Audio File
            </label>
          </div>

          {selectedFile && (
            <Card className="p-6 bg-gradient-to-br from-blue-50/50 to-indigo-50/50 border border-blue-100">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white rounded-xl shadow-sm">
                  <FileAudio className="w-8 h-8 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-900 truncate">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="px-4 py-2 border border-red-200 text-red-600 hover:bg-red-50 rounded-lg transition-colors font-medium"
                >
                  Remove
                </button>
              </div>

              <button
                onClick={handleUpload}
                className="w-full mt-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-semibold shadow-md shadow-blue-200 transition-all flex items-center justify-center gap-2"
              >
                <Mic2 className="w-5 h-5" />
                Start Transcription
              </button>
            </Card>
          )}
        </div>
      )}

      {uploading && (
        <Card className="p-12 text-center max-w-xl mx-auto space-y-6">
          <div className="relative w-24 h-24 mx-auto">
            <div className="absolute inset-0 rounded-full border-4 border-blue-100"></div>
            <div className="absolute inset-0 rounded-full border-4 border-blue-600 border-t-transparent animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <Mic2 className="w-8 h-8 text-blue-600 animate-pulse" />
            </div>
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-bold text-gray-900">Processing Audio File</h3>
            <p className="text-gray-500 max-w-sm mx-auto">
              Our AI engine is transcribing your file and generating VTT subtitles...
            </p>
          </div>
        </Card>
      )}

      {transcriptData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <Card className="p-6 space-y-6">
              <h3 className="text-lg font-bold text-gray-900">Audio Player</h3>
              
              <div className="bg-gray-50 rounded-2xl p-4 flex flex-col items-center justify-center border border-gray-100">
                <FileAudio className="w-16 h-16 text-blue-500/30 mb-4" />
                <audio
                  ref={audioRef}
                  src={import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL.replace('/api', '')}/data/audio/${transcriptData.id}` : `http://localhost:8000/data/audio/${transcriptData.id}`}
                  onTimeUpdate={() => audioRef.current && setCurrentTime(audioRef.current.currentTime)}
                  className="w-full mt-2"
                  controls
                />
              </div>

              <div className="space-y-4 pt-4 border-t border-gray-100 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 flex items-center gap-2">
                    <FileAudio className="w-4 h-4" /> File Name
                  </span>
                  <span className="font-semibold text-gray-900 truncate max-w-[150px]" title={transcriptData.file_name}>
                    {transcriptData.file_name}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 flex items-center gap-2">
                    <Clock className="w-4 h-4" /> Duration
                  </span>
                  <span className="font-semibold text-gray-900">
                    {transcriptData.duration.toFixed(1)}s
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 flex items-center gap-2">
                    <Calendar className="w-4 h-4" /> Date
                  </span>
                  <span className="font-semibold text-gray-900">
                    {new Date(transcriptData.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </Card>

            <Card className="p-6 space-y-4">
              <h3 className="text-lg font-bold text-gray-900">Export Options</h3>
              <button
                onClick={() => downloadText(transcriptData.transcript, `${transcriptData.file_name}.txt`)}
                className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-gray-500" />
                  <div>
                    <p className="font-medium text-gray-900 text-sm">Text Transcript</p>
                    <p className="text-xs text-gray-500">Plain text format</p>
                  </div>
                </div>
                <Download className="w-4 h-4 text-gray-400" />
              </button>
              <button
                onClick={() => downloadText(transcriptData.vtt_content, `${transcriptData.file_name}.vtt`)}
                className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <FileDown className="w-5 h-5 text-gray-500" />
                  <div>
                    <p className="font-medium text-gray-900 text-sm">VTT Subtitles</p>
                    <p className="text-xs text-gray-500">WebVTT format with timings</p>
                  </div>
                </div>
                <Download className="w-4 h-4 text-gray-400" />
              </button>
            </Card>
          </div>

          <div className="lg:col-span-2">
            <Card className="h-full flex flex-col min-h-[500px]">
              <div className="p-4 border-b border-gray-200 flex justify-between items-center flex-wrap gap-2">
                <div className="flex gap-2">
                  <button
                    onClick={() => setActiveTab('interactive')}
                    className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors ${
                      activeTab === 'interactive' 
                        ? 'bg-blue-50 text-blue-600' 
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    Interactive Transcript
                  </button>
                  <button
                    onClick={() => setActiveTab('text')}
                    className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors ${
                      activeTab === 'text' 
                        ? 'bg-blue-50 text-blue-600' 
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    Plain Text
                  </button>
                  <button
                    onClick={() => setActiveTab('raw')}
                    className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors ${
                      activeTab === 'raw' 
                        ? 'bg-blue-50 text-blue-600' 
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    Raw VTT
                  </button>
                </div>
              </div>

              <div className="flex-1 p-6 overflow-y-auto max-h-[500px]">
                {activeTab === 'interactive' && (
                  <div className="space-y-4">
                    {parsedSegments.map((segment, index) => {
                      const isActive = currentTime >= segment.seconds && 
                        (index === parsedSegments.length - 1 || currentTime < parsedSegments[index + 1].seconds)
                      return (
                        <div
                          key={index}
                          onClick={() => handleTimeClick(segment.seconds)}
                          className={`p-3 rounded-xl cursor-pointer transition-all duration-200 flex gap-4 items-start ${
                            isActive 
                              ? 'bg-blue-50 border border-blue-100 shadow-sm' 
                              : 'hover:bg-gray-50'
                          }`}
                        >
                          <span className={`px-2 py-1 rounded text-xs font-mono font-semibold ${
                            isActive ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
                          }`}>
                            {segment.start.split('.')[0]}
                          </span>
                          <p className={`text-sm flex-1 leading-relaxed ${
                            isActive ? 'text-gray-900 font-medium' : 'text-gray-700'
                          }`}>
                            {segment.text}
                          </p>
                        </div>
                      )
                    })}
                    {parsedSegments.length === 0 && (
                      <p className="text-gray-500 italic text-center py-8">
                        No timestamped segments found in VTT.
                      </p>
                    )}
                  </div>
                )}

                {activeTab === 'text' && (
                  <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                      {transcriptData.transcript}
                    </p>
                  </div>
                )}

                {activeTab === 'raw' && (
                  <pre className="bg-gray-950 text-gray-200 rounded-xl p-6 overflow-x-auto text-xs font-mono leading-relaxed">
                    {transcriptData.vtt_content}
                  </pre>
                )}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
