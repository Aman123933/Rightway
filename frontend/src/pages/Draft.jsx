import React, { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { api } from '../api'
import { FileText, Copy, Download, AlertCircle, Check, Loader2, Sparkles } from 'lucide-react'

export default function Draft() {
  const location = useLocation()
  const initialCategory = location.state?.category || 'fee_refund'
  const initialRecordIds = location.state?.record_ids || []
  const initialSummary = location.state?.initialSummary || ''

  const [category, setCategory] = useState(initialCategory)
  const [details, setDetails] = useState(initialSummary ? `Summary: ${initialSummary}\n\nDetails: ` : '')
  const [draftResult, setDraftResult] = useState(null)
  const [editableDraft, setEditableDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  const maxChars = 1500
  const charCount = details.length

  const handleGenerate = async (e) => {
    e?.preventDefault()
    if (!details.trim() || loading) return

    setLoading(true)
    setError(null)
    setCopied(false)

    try {
      const resp = await api.draft(category, details.trim(), initialRecordIds)
      setDraftResult(resp)
      setEditableDraft(resp.draft || '')
    } catch (err) {
      setError(err.message || 'Failed to generate complaint draft.')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    if (!editableDraft) return
    try {
      await navigator.clipboard.writeText(editableDraft)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch {
      // Fallback if clipboard API fails
      setCopied(false)
    }
  }

  const handleDownload = () => {
    if (!editableDraft) return
    const element = document.createElement('a')
    const file = new Blob([editableDraft], { type: 'text/plain;charset=utf-8' })
    element.href = URL.createObjectURL(file)
    element.download = `complaint_draft_${category}.txt`
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
          Draft a Formal Complaint
        </h1>
        <p className="mt-2 text-sm text-gray-600">
          Prepare a structured grievance letter referencing official regulations.
        </p>
      </div>

      {/* Input details form */}
      <form onSubmit={handleGenerate} className="bg-white border border-gray-200 rounded p-6 shadow-sm mb-8">
        <div className="mb-4">
          <label htmlFor="draft-category" className="block text-sm font-semibold text-gray-800 mb-1">
            Grievance Category
          </label>
          <select
            id="draft-category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full sm:w-72 p-2.5 text-sm bg-white border border-gray-300 rounded focus:border-primary-600 focus:ring-1 focus:ring-primary-600"
          >
            <option value="ragging">Ragging</option>
            <option value="harassment">Harassment</option>
            <option value="fee_refund">Fee refund</option>
            <option value="scholarship">Scholarship</option>
            <option value="exam_evaluation">Exam or evaluation</option>
            <option value="attendance">Attendance</option>
            <option value="hostel">Hostel</option>
            <option value="discrimination">Discrimination</option>
            <option value="admission">Admission</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="mb-4">
          <div className="flex justify-between items-center mb-1.5">
            <label htmlFor="incident-details" className="block text-sm font-semibold text-gray-800">
              What happened and when?
            </label>
            <span
              className={`text-xs ${
                charCount > maxChars ? 'text-red-600 font-bold' : 'text-gray-700'
              }`}
            >
              {charCount} / {maxChars} characters
            </span>
          </div>
          <textarea
            id="incident-details"
            rows={5}
            maxLength={maxChars}
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            placeholder="Include specific dates, offices approached, receipts, and responses received..."
            className="w-full p-3 border border-gray-300 rounded text-sm text-gray-900 focus:border-primary-600 focus:ring-1 focus:ring-primary-600"
            required
          />
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-800 flex items-center justify-between">
            <span>{error}</span>
            <button
              type="button"
              onClick={handleGenerate}
              className="px-2.5 py-1 bg-red-700 text-white rounded font-medium hover:bg-red-800 ml-3 shrink-0"
            >
              Retry
            </button>
          </div>
        )}

        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-gray-700">
            RightWay does not send anything. All drafts are for you to review and submit yourself.
          </p>
          <button
            type="submit"
            disabled={loading || !details.trim() || charCount > maxChars}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-800 text-white font-medium text-sm rounded hover:bg-primary-900 focus:ring-2 focus:ring-primary-600 disabled:opacity-50 transition-colors shrink-0"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating draft...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate draft</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Generated draft display */}
      {draftResult && (
        <div className="bg-white border border-gray-200 rounded p-6 shadow-sm space-y-4">
          {/* Banner */}
          <div
            className={`p-3.5 rounded border text-xs font-medium flex items-center gap-2 ${
              draftResult.ai_used
                ? 'bg-primary-50 text-primary-900 border-primary-200'
                : 'bg-gray-100 text-gray-800 border-gray-300'
            }`}
          >
            <FileText className="w-4 h-4 shrink-0 text-primary-700" />
            <span>
              {draftResult.ai_used
                ? (draftResult.label || 'AI-assisted draft. Review and edit before sending.')
                : 'Template draft (no AI used)'}
            </span>
          </div>

          {/* Placeholder Reminder */}
          <div className="p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Important checklist before sending:</span>
              <p className="mt-0.5">
                Placeholders such as [Your Name], [Roll No], [Institution Name], and [Date] are deliberately left empty. You must fill them in with your real details before sending.
              </p>
            </div>
          </div>

          {/* Editable draft textarea */}
          <div>
            <label htmlFor="generated-draft" className="block text-sm font-semibold text-gray-800 mb-1.5">
              Editable Complaint Letter
            </label>
            <textarea
              id="generated-draft"
              rows={16}
              value={editableDraft}
              onChange={(e) => setEditableDraft(e.target.value)}
              className="w-full p-4 border border-gray-300 rounded font-mono text-xs leading-relaxed text-gray-900 bg-white focus:border-primary-600 focus:ring-1 focus:ring-primary-600"
            />
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <span className="text-xs text-gray-700">
              RightWay does not send anything.
            </span>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleCopy}
                className="inline-flex items-center gap-1.5 px-4 py-2 border border-gray-300 bg-white text-gray-700 text-sm font-medium rounded hover:bg-gray-50 focus:ring-2 focus:ring-primary-600"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-600" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Copy</span>
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={handleDownload}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary-800 text-white text-sm font-medium rounded hover:bg-primary-900 focus:ring-2 focus:ring-primary-600"
              >
                <Download className="w-4 h-4" />
                <span>Download .txt</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
