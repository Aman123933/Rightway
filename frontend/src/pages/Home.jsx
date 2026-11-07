import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { ArrowRight, AlertCircle, Loader2 } from 'lucide-react'

const CATEGORIES = [
  { label: 'Ragging', value: 'ragging' },
  { label: 'Harassment', value: 'harassment' },
  { label: 'Fee refund', value: 'fee_refund' },
  { label: 'Scholarship', value: 'scholarship' },
  { label: 'Exam or evaluation', value: 'exam_evaluation' },
  { label: 'Attendance', value: 'attendance' },
  { label: 'Hostel', value: 'hostel' },
  { label: 'Discrimination', value: 'discrimination' },
  { label: 'Admission', value: 'admission' },
  { label: 'Other', value: 'other' },
]

export default function Home({ onOpenEmergency }) {
  const navigate = useNavigate()
  const [message, setMessage] = useState('')
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isWakingUp, setIsWakingUp] = useState(false)

  const maxChars = 1000
  const charCount = message.length

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!message.trim() || loading) return

    setLoading(true)
    setError(null)
    setIsWakingUp(false)

    try {
      const response = await api.ask(message.trim(), selectedCategory || undefined)
      navigate('/answer', {
        state: {
          result: response,
          query: message.trim(),
          category: selectedCategory,
        },
      })
    } catch (err) {
      setError(err.message || 'Failed to find route. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const toggleCategory = (value) => {
    setSelectedCategory((prev) => (prev === value ? null : value))
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 sm:py-12">
      <div className="text-center sm:text-left mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
          Navigate your student rights and formal grievances
        </h1>
        <p className="mt-2 text-base text-gray-600">
          Describe your situation to identify applicable regulations, responsible committees, required documents, and official resolution timelines.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded p-6 shadow-sm">
        {/* Category selection chips */}
        <div className="mb-5">
          <label className="block text-sm font-semibold text-gray-800 mb-2">
            Select a category (optional)
          </label>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Category selection">
            {CATEGORIES.map((cat) => {
              const isSelected = selectedCategory === cat.value
              return (
                <button
                  key={cat.value}
                  type="button"
                  onClick={() => toggleCategory(cat.value)}
                  className={`px-3 py-1.5 rounded text-xs font-medium border transition-colors ${
                    isSelected
                      ? 'bg-primary-800 text-white border-primary-800'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                  aria-pressed={isSelected}
                >
                  {cat.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Message Input Textarea */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-1.5">
            <label htmlFor="problem-description" className="block text-sm font-semibold text-gray-800">
              Describe what happened
            </label>
            <span
              className={`text-xs ${
                charCount > maxChars ? 'text-red-600 font-bold' : 'text-gray-700'
              }`}
              aria-live="polite"
            >
              {charCount} / {maxChars} characters
            </span>
          </div>

          <textarea
            id="problem-description"
            rows={5}
            maxLength={maxChars}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="E.g., I applied for fee refund after withdrawing admission 3 weeks ago, but the administration has not responded..."
            className="w-full p-3 border border-gray-300 rounded focus:border-primary-600 focus:ring-1 focus:ring-primary-600 text-sm text-gray-900 leading-relaxed placeholder:text-gray-400"
            required
          />
        </div>

        {/* Urgent safety note under input */}
        <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
          <div>
            <span>
              If you or someone else is facing immediate danger, violence, or ragging, do not wait.
            </span>{' '}
            <button
              type="button"
              onClick={onOpenEmergency}
              className="text-red-700 font-semibold underline hover:text-red-900"
            >
              Access Emergency Helplines
            </button>
          </div>
        </div>

        {/* Server waking up notice */}
        {isWakingUp && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded">
            The server may be waking up. This can take up to a minute.
          </div>
        )}

        {/* Error message with retry */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-800 flex items-center justify-between">
            <span>{error}</span>
            <button
              type="button"
              onClick={handleSubmit}
              className="px-2.5 py-1 bg-red-700 text-white rounded font-medium hover:bg-red-800 ml-3 shrink-0"
            >
              Retry
            </button>
          </div>
        )}

        {/* Submit button */}
        <div className="flex items-center justify-end">
          <button
            type="submit"
            disabled={loading || !message.trim() || charCount > maxChars}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-800 text-white font-medium text-sm rounded hover:bg-primary-900 focus:outline-none focus:ring-2 focus:ring-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Finding route...</span>
              </>
            ) : (
              <>
                <span>Find my route</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
