'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import ProjectList from '@/components/ProjectList'
import DocumentList from '@/components/DocumentList'
import ChatInterface from '@/components/ChatInterface'

interface Project {
  id: number
  name: string
  description?: string
  created_at: string
}

export default function DashboardPage() {
  const router = useRouter()
  const { isAuthenticated, clearAuth } = useAuthStore()
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState<'projects' | 'chat'>('projects')

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    loadProjects()
  }, [isAuthenticated, router])

  const loadProjects = async () => {
    try {
      const response = await api.get('/projects')
      setProjects(response.data)
      if (response.data.length > 0 && !selectedProject) {
        setSelectedProject(response.data[0])
      }
    } catch (error) {
      console.error('Error loading projects:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    clearAuth()
    router.push('/login')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">ResearchRanger</h1>
              <p className="text-sm text-gray-500">Autonomous Research Agent with RAG</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation */}
        <div className="mb-6">
          <nav className="flex space-x-4">
            <button
              onClick={() => setActiveView('projects')}
              className={`px-4 py-2 rounded-md ${
                activeView === 'projects'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              Projects & Documents
            </button>
            <button
              onClick={() => setActiveView('chat')}
              className={`px-4 py-2 rounded-md ${
                activeView === 'chat'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              Chat & QA
            </button>
          </nav>
        </div>

        {/* Content */}
        {activeView === 'projects' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <ProjectList
                projects={projects}
                selectedProject={selectedProject}
                onSelectProject={setSelectedProject}
                onProjectsChange={loadProjects}
              />
            </div>
            <div className="lg:col-span-2">
              {selectedProject ? (
                <DocumentList project={selectedProject} />
              ) : (
                <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
                  Select a project to view documents
                </div>
              )}
            </div>
          </div>
        )}

        {activeView === 'chat' && (
          <div className="bg-white rounded-lg shadow">
            {selectedProject ? (
              <ChatInterface projectId={selectedProject.id} />
            ) : (
              <div className="p-6 text-center text-gray-500">
                Please select a project first
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

