'use client'

import { useState } from 'react'
import api from '@/lib/api'
import { Plus, Folder, Trash2 } from 'lucide-react'

interface Project {
  id: number
  name: string
  description?: string
  created_at: string
}

interface ProjectListProps {
  projects: Project[]
  selectedProject: Project | null
  onSelectProject: (project: Project) => void
  onProjectsChange: () => void
}

export default function ProjectList({
  projects,
  selectedProject,
  onSelectProject,
  onProjectsChange,
}: ProjectListProps) {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({ name: '', description: '' })

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await api.post('/projects', formData)
      onProjectsChange()
      onSelectProject(response.data)
      setShowCreateModal(false)
      setFormData({ name: '', description: '' })
    } catch (error) {
      console.error('Error creating project:', error)
      alert('Failed to create project')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (projectId: number) => {
    if (!confirm('Are you sure you want to delete this project?')) return
    try {
      await api.delete(`/projects/${projectId}`)
      onProjectsChange()
      if (selectedProject?.id === projectId) {
        onSelectProject(projects.find((p) => p.id !== projectId) || projects[0] || null)
      }
    } catch (error) {
      console.error('Error deleting project:', error)
      alert('Failed to delete project')
    }
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b flex justify-between items-center">
        <h2 className="text-lg font-semibold">Projects</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="p-2 text-primary-600 hover:bg-primary-50 rounded"
          title="Create Project"
        >
          <Plus size={20} />
        </button>
      </div>

      <div className="divide-y">
        {projects.map((project) => (
          <div
            key={project.id}
            onClick={() => onSelectProject(project)}
            className={`p-4 cursor-pointer hover:bg-gray-50 flex items-start justify-between ${
              selectedProject?.id === project.id ? 'bg-primary-50 border-l-4 border-primary-600' : ''
            }`}
          >
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <Folder size={18} className="text-gray-400" />
                <h3 className="font-medium text-gray-900">{project.name}</h3>
              </div>
              {project.description && (
                <p className="text-sm text-gray-500 mt-1">{project.description}</p>
              )}
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleDelete(project.id)
              }}
              className="ml-2 p-1 text-red-600 hover:bg-red-50 rounded"
              title="Delete Project"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
        {projects.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            No projects yet. Create one to get started!
          </div>
        )}
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Create New Project</h3>
            <form onSubmit={handleCreate}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Project Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (optional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

