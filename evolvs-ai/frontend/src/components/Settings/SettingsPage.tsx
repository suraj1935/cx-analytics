import { useEffect, useState } from 'react'
import { Bot, Database, HardDrive, Save } from 'lucide-react'
import { Card, Error } from '@/components/Common/Common'
import { apiClient } from '@/services/api'
import type { UserSettings } from '@/types'

const defaults: UserSettings = {
  retain_original_audio: true,
  llm_model: 'qwen3:4b',
  embedding_model: 'nomic-embed-text',
}

export default function SettingsPage() {
  const [settings, setSettings] = useState(defaults)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    apiClient.getSettings().then((value) => active && setSettings(value))
      .catch(() => active && setError('Could not load settings.'))
      .finally(() => active && setLoading(false))
    return () => { active = false }
  }, [])

  const save = async () => {
    setSaving(true); setSaved(false); setError(null)
    try {
      setSettings(await apiClient.updateSettings(settings)); setSaved(true)
    } catch { setError('Could not save settings.') } finally { setSaving(false) }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div><h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Local AI and uploaded recording controls</p></div>
      {error ? <Error message={error} /> : null}
      <Card className="p-6 space-y-6">
        <div className="flex items-start justify-between gap-6">
          <div className="flex gap-3"><HardDrive className="w-5 h-5 text-blue-600 mt-0.5" />
            <div><h2 className="font-semibold text-gray-900">Retain original audio</h2>
              <p className="text-sm text-gray-500 mt-1">Keep the uploaded file in private storage after transcription.</p></div></div>
          <button type="button" role="switch" aria-checked={settings.retain_original_audio}
            aria-label="Retain original audio" disabled={loading}
            onClick={() => setSettings((current) => ({...current, retain_original_audio: !current.retain_original_audio}))}
            className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${settings.retain_original_audio ? 'bg-blue-600' : 'bg-gray-300'} disabled:opacity-50`}>
            <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${settings.retain_original_audio ? 'translate-x-5' : 'translate-x-0.5'}`} />
          </button>
        </div>
        <div className="border-t border-gray-200 pt-6 grid sm:grid-cols-2 gap-4">
          <div className="flex gap-3"><Bot className="w-5 h-5 text-gray-500" /><div><p className="text-sm text-gray-500">Audit model</p><p className="font-medium">{settings.llm_model}</p></div></div>
          <div className="flex gap-3"><Database className="w-5 h-5 text-gray-500" /><div><p className="text-sm text-gray-500">Embedding model</p><p className="font-medium">{settings.embedding_model}</p></div></div>
        </div>
        <div className="flex items-center gap-3 border-t border-gray-200 pt-6">
          <button type="button" onClick={save} disabled={loading || saving}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">
            <Save className="w-4 h-4" />{saving ? 'Saving' : 'Save settings'}
          </button>
          {saved ? <span className="text-sm text-green-700">Settings saved</span> : null}
        </div>
      </Card>
    </div>
  )
}
