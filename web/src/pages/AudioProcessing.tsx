import { useState } from 'react'
import { 
  Upload, 
  Play, 
  Pause, 
  Square, 
  Settings, 
  Download,
  FileAudio,
  Zap,
  Clock,
  CheckCircle
} from 'lucide-react'

export function AudioProcessing() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [processingQueue, setProcessingQueue] = useState([
    {
      id: 1,
      name: 'voice_sample_01.wav',
      status: 'completed',
      progress: 100,
      duration: '2m 34s'
    },
    {
      id: 2,
      name: 'background_music.mp3',
      status: 'processing',
      progress: 65,
      duration: '1m 12s'
    },
    {
      id: 3,
      name: 'sound_effect_01.wav',
      status: 'pending',
      progress: 0,
      duration: '45s'
    }
  ])

  const effects = [
    { name: 'Voice Enhancement', enabled: true, description: 'Improve voice clarity and reduce noise' },
    { name: 'Background Music Mix', enabled: true, description: 'Balance background music with voice' },
    { name: 'Sound Effects', enabled: false, description: 'Add ambient sound effects' },
    { name: 'Compression', enabled: true, description: 'Normalize audio levels' },
    { name: 'EQ Adjustment', enabled: false, description: 'Fine-tune frequency response' }
  ]

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleStartProcessing = () => {
    setIsProcessing(true)
    // Simulate processing
    setTimeout(() => {
      setIsProcessing(false)
    }, 5000)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'processing':
        return <Zap className="h-5 w-5 text-blue-500" />
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audio Processing</h1>
        <p className="mt-1 text-sm text-gray-500">
          Process your audio files with automated effects and enhancements
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* File Upload */}
        <div className="card">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Upload Audio File</h3>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <FileAudio className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <label htmlFor="file-upload" className="btn btn-primary cursor-pointer">
                  <Upload className="h-5 w-5 mr-2" />
                  Choose File
                </label>
                <input
                  id="file-upload"
                  type="file"
                  accept="audio/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <p className="mt-2 text-sm text-gray-500">
                  or drag and drop audio files here
                </p>
              </div>
            </div>

            {selectedFile && (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            )}

            <div className="mt-6 flex space-x-3">
              <button 
                onClick={handleStartProcessing}
                disabled={!selectedFile || isProcessing}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isProcessing ? (
                  <>
                    <Zap className="h-5 w-5 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 mr-2" />
                    Start Processing
                  </>
                )}
              </button>
              <button className="btn btn-secondary">
                <Settings className="h-5 w-5 mr-2" />
                Settings
              </button>
            </div>
          </div>
        </div>

        {/* Effects Configuration */}
        <div className="card">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Effects Configuration</h3>
            
            <div className="space-y-3">
              {effects.map((effect, index) => (
                <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={effect.enabled}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label className="ml-3 text-sm font-medium text-gray-900">
                        {effect.name}
                      </label>
                    </div>
                    <p className="ml-7 text-sm text-gray-500">{effect.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Processing Queue */}
      <div className="card">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Processing Queue</h3>
          
          <div className="space-y-4">
            {processingQueue.map((item) => (
              <div key={item.id} className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg">
                <div className="flex-shrink-0">
                  {getStatusIcon(item.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {item.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    Duration: {item.duration}
                  </p>
                </div>
                <div className="flex-shrink-0 w-32">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{item.progress}%</p>
                </div>
                <div className="flex-shrink-0">
                  {item.status === 'completed' && (
                    <button className="btn btn-secondary text-sm">
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
