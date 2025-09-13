import { 
  FileAudio, 
  Zap, 
  Clock, 
  CheckCircle,
  AlertCircle,
  Play
} from 'lucide-react'

export function Dashboard() {
  const stats = [
    { name: 'Total Projects', value: '12', icon: FileAudio, change: '+2', changeType: 'positive' },
    { name: 'Processing Jobs', value: '8', icon: Zap, change: '+3', changeType: 'positive' },
    { name: 'Completed Today', value: '24', icon: CheckCircle, change: '+12%', changeType: 'positive' },
    { name: 'Active Jobs', value: '3', icon: Clock, change: '-1', changeType: 'negative' },
  ]

  const recentJobs = [
    { id: 1, name: 'Drama Episode 1 - Voice Processing', status: 'completed', duration: '2m 34s' },
    { id: 2, name: 'Background Music Mix', status: 'processing', duration: '1m 12s' },
    { id: 3, name: 'Sound Effects Library', status: 'pending', duration: '-' },
    { id: 4, name: 'Podcast Intro Processing', status: 'completed', duration: '45s' },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'processing':
        return <Play className="h-5 w-5 text-blue-500" />
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-100'
      case 'processing':
        return 'text-blue-700 bg-blue-100'
      case 'pending':
        return 'text-yellow-700 bg-yellow-100'
      case 'error':
        return 'text-red-700 bg-red-100'
      default:
        return 'text-gray-700 bg-gray-100'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your audio processing projects and jobs
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <stat.icon className="h-8 w-8 text-primary-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stat.value}
                    </div>
                    <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                      stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.change}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Jobs */}
      <div className="card">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Processing Jobs</h3>
          <div className="flow-root">
            <ul className="-my-5 divide-y divide-gray-200">
              {recentJobs.map((job) => (
                <li key={job.id} className="py-4">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {getStatusIcon(job.status)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {job.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        Duration: {job.duration}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <button className="btn btn-primary">
              <FileAudio className="h-5 w-5 mr-2" />
              New Project
            </button>
            <button className="btn btn-secondary">
              <Zap className="h-5 w-5 mr-2" />
              Process Audio
            </button>
            <button className="btn btn-secondary">
              <Settings className="h-5 w-5 mr-2" />
              Configure Effects
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
