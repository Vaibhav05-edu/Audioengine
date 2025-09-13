import { useState } from 'react'
import { 
  Plus, 
  FolderOpen, 
  MoreVertical, 
  Play, 
  Edit, 
  Trash2,
  Upload
} from 'lucide-react'

export function Projects() {
  const [projects] = useState([
    {
      id: 1,
      name: 'Mystery Theater Season 1',
      description: 'Complete audio drama series with voice processing and sound effects',
      files: 24,
      duration: '2h 45m',
      lastModified: '2024-01-15',
      status: 'active'
    },
    {
      id: 2,
      name: 'Podcast Intro Collection',
      description: 'Various podcast intro and outro segments',
      files: 12,
      duration: '45m',
      lastModified: '2024-01-14',
      status: 'completed'
    },
    {
      id: 3,
      name: 'Sound Effects Library',
      description: 'Collection of processed sound effects for future use',
      files: 156,
      duration: '3h 20m',
      lastModified: '2024-01-13',
      status: 'processing'
    },
    {
      id: 4,
      name: 'Voice Acting Samples',
      description: 'Test recordings for voice processing pipeline',
      files: 8,
      duration: '15m',
      lastModified: '2024-01-12',
      status: 'draft'
    }
  ])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-700 bg-green-100'
      case 'completed':
        return 'text-blue-700 bg-blue-100'
      case 'processing':
        return 'text-yellow-700 bg-yellow-100'
      case 'draft':
        return 'text-gray-700 bg-gray-100'
      default:
        return 'text-gray-700 bg-gray-100'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your audio drama projects and files
          </p>
        </div>
        <div className="flex space-x-3">
          <button className="btn btn-secondary">
            <Upload className="h-5 w-5 mr-2" />
            Upload Files
          </button>
          <button className="btn btn-primary">
            <Plus className="h-5 w-5 mr-2" />
            New Project
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <div key={project.id} className="card hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex items-center">
                <FolderOpen className="h-8 w-8 text-primary-600" />
                <div className="ml-3">
                  <h3 className="text-lg font-medium text-gray-900">
                    {project.name}
                  </h3>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                    {project.status}
                  </span>
                </div>
              </div>
              <button className="text-gray-400 hover:text-gray-600">
                <MoreVertical className="h-5 w-5" />
              </button>
            </div>
            
            <p className="mt-3 text-sm text-gray-600">
              {project.description}
            </p>
            
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Files:</span>
                <span className="ml-1 font-medium">{project.files}</span>
              </div>
              <div>
                <span className="text-gray-500">Duration:</span>
                <span className="ml-1 font-medium">{project.duration}</span>
              </div>
            </div>
            
            <div className="mt-4 text-sm text-gray-500">
              Last modified: {project.lastModified}
            </div>
            
            <div className="mt-4 flex space-x-2">
              <button className="flex-1 btn btn-secondary text-sm">
                <Play className="h-4 w-4 mr-1" />
                Open
              </button>
              <button className="btn btn-secondary text-sm">
                <Edit className="h-4 w-4" />
              </button>
              <button className="btn btn-secondary text-sm text-red-600 hover:text-red-700">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {projects.length === 0 && (
        <div className="text-center py-12">
          <FolderOpen className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No projects</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new project.
          </p>
          <div className="mt-6">
            <button className="btn btn-primary">
              <Plus className="h-5 w-5 mr-2" />
              New Project
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
