'use client'

import { useState, useEffect, useRef } from 'react'
import api from '@/lib/api'
import { Send, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface ChatInterfaceProps {
  projectId: number
}

interface Message {
  id: number
  question: string
  answer: string
  citations: Array<{
    source_num: number
    document_filename: string
    page_number?: number
    paragraph_number?: number
    snippet: string
  }>
  created_at: string
}

export default function ChatInterface({ projectId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadMessages()
  }, [projectId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadMessages = async () => {
    try {
      // Get latest session or create one
      const sessionsResponse = await api.get('/qa/sessions', {
        params: { project_id: projectId },
      })
      
      if (sessionsResponse.data.length > 0) {
        const sessionId = sessionsResponse.data[0].id
        const responsesResponse = await api.get(`/qa/sessions/${sessionId}/responses`)
        setMessages(responsesResponse.data)
      }
    } catch (error) {
      console.error('Error loading messages:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const question = input.trim()
    setInput('')
    setLoading(true)

    // Add user message optimistically
    const userMessage = {
      id: Date.now(),
      question,
      answer: '',
      citations: [],
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])

    try {
      const response = await api.post('/qa/ask', {
        question,
        project_id: projectId,
      })

      // Replace optimistic message with actual response
      setMessages((prev) => {
        const newMessages = [...prev]
        const lastIndex = newMessages.length - 1
        if (newMessages[lastIndex].id === userMessage.id) {
          newMessages[lastIndex] = response.data
        }
        return newMessages
      })
    } catch (error: any) {
      console.error('Error asking question:', error)
      // Remove optimistic message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id))
      alert(error.response?.data?.detail || 'Failed to get answer')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-300px)]">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            <p className="text-lg mb-2">Ask a question to get started!</p>
            <p className="text-sm">The AI will search through your documents and provide answers with citations.</p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className="space-y-4">
            {/* Question */}
            <div className="flex justify-end">
              <div className="max-w-3xl bg-primary-600 text-white rounded-lg px-4 py-2">
                <p>{message.question}</p>
              </div>
            </div>

            {/* Answer */}
            <div className="flex justify-start">
              <div className="max-w-3xl bg-gray-100 rounded-lg px-4 py-3">
                <ReactMarkdown className="prose prose-sm max-w-none">
                  {message.answer}
                </ReactMarkdown>

                {/* Citations */}
                {message.citations && message.citations.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-300">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Sources:</h4>
                    <div className="space-y-2">
                      {message.citations.map((citation, idx) => (
                        <div
                          key={idx}
                          className="text-sm bg-white p-2 rounded border border-gray-200"
                        >
                          <div className="font-medium text-gray-900">
                            [{citation.source_num}] {citation.document_filename}
                            {citation.page_number && ` - Page ${citation.page_number}`}
                            {citation.paragraph_number && `, Paragraph ${citation.paragraph_number}`}
                          </div>
                          {citation.snippet && (
                            <div className="text-gray-600 mt-1 text-xs italic">
                              "{citation.snippet.slice(0, 150)}..."
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex items-center space-x-2 text-gray-600">
                <Loader2 className="animate-spin" size={16} />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4 bg-white">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Send size={18} />
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  )
}

