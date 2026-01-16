'use client'

import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { Upload, FileText, Loader2, Trash2, Download } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface Project {
  id: number
  name: string
}

interface Document {
  id: number
  filename: string
  original_filename: string
  status: string
  document_type: string
  page_count?: number
  created_at: string
  indexed_at?: string
}

interface DocumentListProps {
  project: Project
}

export default function DocumentList({ project }: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)
  const [chunks, setChunks] = useState<any[]>([])

  useEffect(() => {
    loadDocuments()
    // Poll for status updates
    const interval = setInterval(loadDocuments, 5000)
    return () => clearInterval(interval)
  }, [project.id])

  const loadDocuments = async () => {
    try {
      const response = await api.get('/documents', {
        params: { project_id: project.id },
      })
      setDocuments(response.data)
    } catch (error) {
      console.error('Error loading documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', project.id.toString())

    try {
      await api.post('/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      loadDocuments()
    } catch (error: any) {
      console.error('Error uploading document:', error)
      alert(error.response?.data?.detail || 'Failed to upload document')
    } finally {
      setUploading(false)
      e.target.value = '' // Reset input
    }
  }

  const handleDelete = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return
    try {
      await api.delete(`/documents/${docId}`)
      loadDocuments()
      if (selectedDoc?.id === docId) {
        setSelectedDoc(null)
        setChunks([])
      }
    } catch (error) {
      console.error('Error deleting document:', error)
      alert('Failed to delete document')
    }
  }

  const loadChunks = async (docId: number) => {
    try {
      const response = await api.get(`/documents/${docId}/chunks`)
      setChunks(response.data)
    } catch (error) {
      console.error('Error loading chunks:', error)
    }
  }

  const handleExport = async (format: 'markdown' | 'bibtex') => {
    try {
      const response = await api.get(`/export/summary/${project.id}?format=${format}`, {
        responseType: 'blob',
      })
      const blob = new Blob([response.data], {
        type: format === 'markdown' ? 'text/markdown' : 'text/x-bibtex',
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${project.name}_${format === 'markdown' ? 'summary' : 'references'}.${format === 'markdown' ? 'md' : 'bib'}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error exporting:', error)
      alert('Failed to export')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'indexed':
        return 'bg-green-100 text-green-800'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b flex justify-between items-center">
        <h2 className="text-lg font-semibold">Documents</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => handleExport('markdown')}
            className="px-3 py-1 text-sm text-primary-600 hover:bg-primary-50 rounded"
            title="Export Markdown"
          >
            Export MD
          </button>
          <button
            onClick={() => handleExport('bibtex')}
            className="px-3 py-1 text-sm text-primary-600 hover:bg-primary-50 rounded"
            title="Export BibTeX"
          >
            Export BibTeX
          </button>
          <label className="px-3 py-1 text-sm text-white bg-primary-600 hover:bg-primary-700 rounded cursor-pointer flex items-center space-x-1">
            <Upload size={16} />
            <span>Upload</span>
            <input
              type="file"
              accept=".pdf,.html,.md,.txt"
              onChange={handleUpload}
              className="hidden"
              disabled={uploading}
            />
          </label>
        </div>
      </div>

      {uploading && (
        <div className="p-4 bg-yellow-50 border-b flex items-center space-x-2">
          <Loader2 className="animate-spin" size={16} />
          <span className="text-sm text-yellow-800">Uploading and processing...</span>
        </div>
      )}

      <div className="divide-y max-h-[600px] overflow-y-auto">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className={`p-4 hover:bg-gray-50 cursor-pointer ${
              selectedDoc?.id === doc.id ? 'bg-primary-50' : ''
            }`}
            onClick={() => {
              setSelectedDoc(doc)
              if (doc.status === 'indexed') {
                loadChunks(doc.id)
              }
            }}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <FileText size={18} className="text-gray-400" />
                  <h3 className="font-medium text-gray-900">{doc.original_filename}</h3>
                </div>
                <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                  <span className={`px-2 py-1 rounded text-xs ${getStatusColor(doc.status)}`}>
                    {doc.status}
                  </span>
                  {doc.page_count && <span>{doc.page_count} pages</span>}
                  <span>{doc.document_type.toUpperCase()}</span>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDelete(doc.id)
                }}
                className="ml-2 p-1 text-red-600 hover:bg-red-50 rounded"
                title="Delete Document"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
        {documents.length === 0 && !loading && (
          <div className="p-8 text-center text-gray-500">
            No documents yet. Upload a document to get started!
          </div>
        )}
      </div>

      {selectedDoc && (
        <div className="border-t p-4 bg-gray-50">
          <h3 className="font-semibold mb-2">Document Chunks ({chunks.length})</h3>
          <div className="max-h-[300px] overflow-y-auto space-y-2">
            {chunks.slice(0, 10).map((chunk, idx) => (
              <div key={chunk.id} className="p-2 bg-white rounded border text-sm">
                <div className="text-xs text-gray-500 mb-1">
                  Chunk {chunk.chunk_index}
                  {chunk.page_number && ` | Page ${chunk.page_number}`}
                  {chunk.paragraph_number && ` | Paragraph ${chunk.paragraph_number}`}
                </div>
                <div className="text-gray-700 line-clamp-3">{chunk.content}</div>
              </div>
            ))}
            {chunks.length > 10 && (
              <div className="text-sm text-gray-500 text-center">
                ... and {chunks.length - 10} more chunks
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

