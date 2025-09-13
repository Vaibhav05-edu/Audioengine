import { useState } from 'react'
import { 
  Save, 
  Upload, 
  Download, 
  Trash2,
  Key,
  Database,
  Bell,
  Monitor
} from 'lucide-react'

export function Settings() {
  const [settings, setSettings] = useState({
    apiKey: '',
    databaseUrl: 'postgresql+psycopg2://app:app@localhost:5432/fx',
    redisUrl: 'redis://localhost:6379/0',
    notifications: {
      email: true,
      browser: false,
      processingComplete: true,
      errors: true
    },
    processing: {
      maxConcurrentJobs: 4,
      defaultQuality: 'high',
      autoDeleteTempFiles: true,
      outputFormat: 'wav'
    },
    ui: {
      theme: 'light',
      language: 'en',
      showAdvancedOptions: false
    }
  })

  const handleSave = () => {
    // Save settings logic here
    console.log('Saving settings:', settings)
  }

  const handleExport = () => {
    const dataStr = JSON.stringify(settings, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'audio-drama-fx-settings.json'
    link.click()
  }

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const importedSettings = JSON.parse(e.target?.result as string)
          setSettings(importedSettings)
        } catch (error) {
          console.error('Error importing settings:', error)
        }
      }
      reader.readAsText(file)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="mt-1 text-sm text-gray-500">
            Configure your audio processing preferences and system settings
          </p>
        </div>
        <div className="flex space-x-3">
          <button className="btn btn-secondary">
            <Download className="h-5 w-5 mr-2" />
            Export
          </button>
          <label className="btn btn-secondary cursor-pointer">
            <Upload className="h-5 w-5 mr-2" />
            Import
            <input
              type="file"
              accept=".json"
              onChange={handleImport}
              className="hidden"
            />
          </label>
          <button onClick={handleSave} className="btn btn-primary">
            <Save className="h-5 w-5 mr-2" />
            Save Settings
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Configuration */}
        <div className="card">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center mb-4">
              <Key className="h-5 w-5 text-primary-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">API Configuration</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  ElevenLabs API Key
                </label>
                <input
                  type="password"
                  value={settings.apiKey}
                  onChange={(e) => setSettings({ ...settings, apiKey: e.target.value })}
                  className="input mt-1"
                  placeholder="Enter your API key"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Database Configuration */}
        <div className="card">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center mb-4">
              <Database className="h-5 w-5 text-primary-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">Database Configuration</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Database URL
                </label>
                <input
                  type="text"
                  value={settings.databaseUrl}
                  onChange={(e) => setSettings({ ...settings, databaseUrl: e.target.value })}
                  className="input mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Redis URL
                </label>
                <input
                  type="text"
                  value={settings.redisUrl}
                  onChange={(e) => setSettings({ ...settings, redisUrl: e.target.value })}
                  className="input mt-1"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center mb-4">
              <Bell className="h-5 w-5 text-primary-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">Notifications</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Email Notifications</label>
                  <p className="text-sm text-gray-500">Receive notifications via email</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.email}
                  onChange={(e) => setSettings({
                    ...settings,
                    notifications: { ...settings.notifications, email: e.target.checked }
                  })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Browser Notifications</label>
                  <p className="text-sm text-gray-500">Show browser notifications</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.browser}
                  onChange={(e) => setSettings({
                    ...settings,
                    notifications: { ...settings.notifications, browser: e.target.checked }
                  })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Processing Complete</label>
                  <p className="text-sm text-gray-500">Notify when processing is complete</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.processingComplete}
                  onChange={(e) => setSettings({
                    ...settings,
                    notifications: { ...settings.notifications, processingComplete: e.target.checked }
                  })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Processing Settings */}
        <div className="card">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center mb-4">
              <Monitor className="h-5 w-5 text-primary-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">Processing Settings</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Max Concurrent Jobs
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={settings.processing.maxConcurrentJobs}
                  onChange={(e) => setSettings({
                    ...settings,
                    processing: { ...settings.processing, maxConcurrentJobs: parseInt(e.target.value) }
                  })}
                  className="input mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Default Quality
                </label>
                <select
                  value={settings.processing.defaultQuality}
                  onChange={(e) => setSettings({
                    ...settings,
                    processing: { ...settings.processing, defaultQuality: e.target.value }
                  })}
                  className="input mt-1"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="ultra">Ultra</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Output Format
                </label>
                <select
                  value={settings.processing.outputFormat}
                  onChange={(e) => setSettings({
                    ...settings,
                    processing: { ...settings.processing, outputFormat: e.target.value }
                  })}
                  className="input mt-1"
                >
                  <option value="wav">WAV</option>
                  <option value="mp3">MP3</option>
                  <option value="flac">FLAC</option>
                  <option value="m4a">M4A</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="card border-red-200">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-red-900 mb-4">Danger Zone</h3>
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-red-900">Reset All Settings</h4>
              <p className="text-sm text-red-600">This will reset all settings to their default values</p>
            </div>
            <button className="btn bg-red-600 text-white hover:bg-red-700">
              <Trash2 className="h-5 w-5 mr-2" />
              Reset Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
