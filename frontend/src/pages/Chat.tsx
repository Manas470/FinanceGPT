/** Financial Q&A — chat with your financial data */
import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { auditApi } from '../services/api'
import ReactMarkdown from 'react-markdown'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const SUGGESTIONS = [
  'What is our gross margin compared to industry benchmarks?',
  'Summarize the key financial risks identified in the last audit.',
  'Calculate our working capital ratio and explain what it means.',
  'What are the top 3 anomalies I should be concerned about?',
  'Is our current debt-to-equity ratio sustainable?',
]

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const { mutate: sendMessage, isPending } = useMutation({
    mutationFn: async (question: string) => {
      const history = messages.map((m) => ({ role: m.role, content: m.content }))
      const { data } = await auditApi.chat({ message: question, conversation_history: history })
      return data.response
    },
    onSuccess: (response) => {
      setMessages((prev) => [...prev, { role: 'assistant', content: response }])
    },
    onError: () => {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: '⚠️ Failed to get a response. Please check that documents are uploaded and processed.',
      }])
    },
  })

  const handleSend = (text: string = input) => {
    if (!text.trim() || isPending) return
    const question = text.trim()
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setInput('')
    sendMessage(question)
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isPending])

  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-8 py-4">
        <h1 className="text-xl font-bold text-gray-900">Financial Q&A</h1>
        <p className="text-sm text-gray-500">Ask questions about your financial data in plain language</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto px-8 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <div className="text-5xl mb-3">💬</div>
              <h2 className="text-lg font-semibold text-gray-800">Ask anything about your finances</h2>
              <p className="text-sm text-gray-500 mt-1">
                Powered by Claude AI — analyzes your uploaded documents
              </p>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  className="text-left px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-700 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-blue-600">FinanceGPT</span>
                </div>
              )}
              <div className={`px-4 py-3 rounded-2xl text-sm ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-sm'
                  : 'bg-white border border-gray-100 shadow-sm text-gray-800 rounded-tl-sm'
              }`}>
                {msg.role === 'user' ? (
                  <p>{msg.content}</p>
                ) : (
                  <div className="prose prose-sm max-w-none prose-headings:text-gray-800 prose-p:text-gray-700">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {isPending && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-100 shadow-sm px-4 py-3 rounded-2xl rounded-tl-sm">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
                <span className="text-xs text-gray-400">Analyzing your financial data...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-100 px-8 py-4">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask about revenue trends, risk factors, ratios, anomalies..."
            className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isPending}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isPending}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white px-5 py-3 rounded-xl text-sm font-semibold transition-colors"
          >
            →
          </button>
        </div>
        <p className="text-xs text-gray-400 text-center mt-2">
          AI responses are based on your uploaded financial documents
        </p>
      </div>
    </div>
  )
}
