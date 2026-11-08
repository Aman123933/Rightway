import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { api, setSlowServerListener } from '../api'
import SourceCard from '../components/SourceCard'
import {
  AlertTriangle,
  Phone,
  Mail,
  ExternalLink,
  Clock,
  FileText,
  Building,
  CheckSquare,
  ArrowRight,
  RotateCw,
  Search,
} from 'lucide-react'

export default function Answer({ onOpenEmergency }) {
  const location = useLocation()
  const navigate = useNavigate()

  const [result, setResult] = useState(location.state?.result || null)
  const [query, setQuery] = useState(location.state?.query || '')
  const [category, setCategory] = useState(location.state?.category || null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [wakingUp, setWakingUp] = useState(false)

  useEffect(() => {
    setSlowServerListener((isSlow) => setWakingUp(isSlow))
    return () => setSlowServerListener(null)
  }, [])

  // If page was loaded directly without state, we can allow entering a query or show prompt
  const handleManualSearch = async (e) => {
    e?.preventDefault()
    if (!query.trim() || loading) return

    setLoading(true)
    setError(null)
    try {
      const resp = await api.ask(query.trim(), category || undefined)
      setResult(resp)
    } catch (err) {
      setError(err.message || 'Failed to retrieve information.')
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    handleManualSearch()
  }

  const answer = result?.answer
  const safety = result?.safety
  const sources = result?.sources || []
  const primarySource = sources[0] || null

  const handleDraftClick = () => {
    const recordIds = sources.map((s) => s.id)
    navigate('/draft', {
      state: {
        category: result?.category || category || 'other',
        record_ids: recordIds,
        initialSummary: answer?.summary || '',
      },
    })
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12">
      {/* Search / query bar if user wants to change question */}
      <div className="mb-8">
        <form onSubmit={handleManualSearch} className="flex gap-2">
          <label htmlFor="answer-search-input" className="sr-only">
            Ask a student grievance or procedural question
          </label>
          <div className="relative flex-1">
            <input
              id="answer-search-input"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search student rights, grievance rules, procedures..."
              className="w-full px-4 py-2.5 text-sm bg-white border border-gray-300 rounded focus:border-primary-600 focus:ring-1 focus:ring-primary-600"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2.5 bg-primary-800 text-white text-sm font-medium rounded hover:bg-primary-900 disabled:opacity-50 flex items-center gap-1.5 shrink-0"
          >
            <Search className="w-4 h-4" />
            <span>Search</span>
          </button>
        </form>

        {wakingUp && (
          <div className="mt-2 text-xs text-blue-800 bg-blue-50 border border-blue-200 p-2.5 rounded">
            Waking the server (about 30 seconds)... Please wait while the instance starts up.
          </div>
        )}
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-4 animate-pulse" aria-label="Loading guidance">
          <div className="h-28 bg-gray-200 rounded"></div>
          <div className="h-36 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      )}

      {/* Error state with retry */}
      {error && !loading && (
        <div className="p-6 bg-red-50 border border-red-200 rounded text-center">
          <p className="text-sm text-red-900 font-medium mb-4">{error}</p>
          <button
            onClick={handleRetry}
            className="inline-flex items-center gap-2 px-4 py-2 bg-red-700 text-white text-sm font-medium rounded hover:bg-red-800"
          >
            <RotateCw className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Answer content area */}
      {!loading && !error && result && (
        <div className="space-y-6" aria-live="polite">
          {/* 1. URGENT SAFETY PANEL (Rendered FIRST if triggered) */}
          {safety && safety.triggered && (
            <section
              className="p-6 bg-red-900 text-white rounded border-2 border-red-950 shadow-md"
              aria-label="Urgent Safety Alert"
            >
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-red-200 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h2 className="text-xl font-bold tracking-tight">
                    Immediate Safety Alert
                  </h2>
                  <p className="mt-2 text-red-100 text-sm leading-relaxed">
                    {safety.message || "Urgent safety alert. If you are in immediate danger, call 112 (India's emergency number)."}
                  </p>

                  <div className="mt-4 flex flex-wrap gap-3">
                    <a
                      href="tel:112"
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-white text-red-900 font-bold text-sm rounded hover:bg-red-50"
                    >
                      <Phone className="w-4 h-4" />
                      Emergency 112
                    </a>
                    <button
                      type="button"
                      onClick={onOpenEmergency}
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-red-800 text-white font-medium text-sm rounded border border-red-600 hover:bg-red-700"
                    >
                      View All Helplines
                    </button>
                  </div>

                  {safety.contacts && safety.contacts.length > 0 && (
                    <div className="mt-5 pt-4 border-t border-red-800 space-y-2">
                      <p className="text-xs uppercase tracking-wider text-red-300 font-semibold">
                        Emergency Contacts:
                      </p>
                      {safety.contacts.map((c, idx) => (
                        <div key={idx} className="text-sm bg-red-950/60 p-2.5 rounded border border-red-800">
                          <span className="font-semibold text-white">{c.label}</span>
                          <div className="mt-1 flex flex-wrap gap-3 text-xs text-red-200">
                            {c.phone && <a href={`tel:${c.phone}`} className="underline font-mono">{c.phone}</a>}
                            {c.email && <a href={`mailto:${c.email}`} className="underline">{c.email}</a>}
                            {c.hours && <span>{c.hours}</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* 4. NOT FOUND STATE */}
          {result.not_found ? (
            <div className="p-8 bg-white border border-gray-200 rounded text-center">
              <h2 className="text-lg font-bold text-gray-900">
                No matching institutional rule found
              </h2>
              <p className="mt-2 text-sm text-gray-600 max-w-xl mx-auto">
                We could not locate a specific official rule for this inquiry in the current library.
              </p>
              {result.fallback && (
                <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded text-sm text-amber-900 inline-block font-medium">
                  Recommendation: {result.fallback}
                </div>
              )}
              <div className="mt-6">
                <Link
                  to="/sources"
                  className="text-primary-700 hover:text-primary-900 font-medium text-sm underline"
                >
                  See which pages RightWay has read
                </Link>
              </div>
            </div>
          ) : (
            /* 2. CARDS: What applies, Where to go, Steps, Time limits, Documents to prepare */
            <div className="space-y-5">
              {/* Card 1: What applies (Summary) */}
              {answer?.summary && (
                <div className="bg-white border border-gray-200 rounded p-5 shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="w-5 h-5 text-primary-700" />
                    <h2 className="text-base font-semibold text-gray-900">What applies</h2>
                  </div>
                  <p className="text-sm text-gray-800 leading-relaxed">
                    {answer.summary}
                  </p>
                  {primarySource && <SourceCard source={primarySource} />}
                </div>
              )}

              {/* Card 2: Where to go (Office & Portal) */}
              {(answer?.office || answer?.portal_url) && (
                <div className="bg-white border border-gray-200 rounded p-5 shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <Building className="w-5 h-5 text-primary-700" />
                    <h2 className="text-base font-semibold text-gray-900">Where to go</h2>
                  </div>

                  {answer.office && (
                    <div className="bg-gray-50 border border-gray-200 rounded p-3 mb-3">
                      <div className="font-medium text-sm text-gray-900">{answer.office.label}</div>
                      <div className="mt-2 flex flex-wrap gap-4 text-xs text-gray-700">
                        {answer.office.phone && (
                          <a href={`tel:${answer.office.phone}`} className="inline-flex items-center gap-1 text-primary-700 hover:underline font-mono">
                            <Phone className="w-3.5 h-3.5" />
                            {answer.office.phone}
                          </a>
                        )}
                        {answer.office.email && (
                          <a href={`mailto:${answer.office.email}`} className="inline-flex items-center gap-1 text-primary-700 hover:underline">
                            <Mail className="w-3.5 h-3.5" />
                            {answer.office.email}
                          </a>
                        )}
                        {answer.office.hours && (
                          <span className="inline-flex items-center gap-1 text-gray-600">
                            <Clock className="w-3.5 h-3.5" />
                            {answer.office.hours}
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {answer.portal_url && (
                    <div className="mt-2">
                      <a
                        href={answer.portal_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary-800 hover:underline"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>Open official grievance submission portal</span>
                      </a>
                    </div>
                  )}

                  {sources[1] ? <SourceCard source={sources[1]} /> : primarySource && <SourceCard source={primarySource} />}
                </div>
              )}

              {/* Card 3: Steps (numbered) */}
              {answer?.steps && answer.steps.length > 0 && (
                <div className="bg-white border border-gray-200 rounded p-5 shadow-sm">
                  <div className="flex items-center gap-2 mb-3">
                    <CheckSquare className="w-5 h-5 text-primary-700" />
                    <h2 className="text-base font-semibold text-gray-900">Steps to follow</h2>
                  </div>
                  <ol className="space-y-2 text-sm text-gray-800 list-decimal list-inside pl-1">
                    {answer.steps.map((step, idx) => (
                      <li key={idx} className="leading-relaxed">
                        <span className="font-normal">{step}</span>
                      </li>
                    ))}
                  </ol>
                  {sources[0] && <SourceCard source={sources[0]} />}
                </div>
              )}

              {/* Card 4: Time limits */}
              {answer?.time_limits && answer.time_limits.length > 0 && (
                <div className="bg-white border border-gray-200 rounded p-5 shadow-sm">
                  <div className="flex items-center gap-2 mb-3">
                    <Clock className="w-5 h-5 text-primary-700" />
                    <h2 className="text-base font-semibold text-gray-900">Prescribed time limits</h2>
                  </div>
                  <ul className="space-y-1.5 text-sm text-gray-800 list-disc list-inside pl-1">
                    {answer.time_limits.map((tl, idx) => (
                      <li key={idx}>{tl}</li>
                    ))}
                  </ul>
                  {sources[0] && <SourceCard source={sources[0]} />}
                </div>
              )}

              {/* Card 5: Documents to prepare */}
              {answer?.documents && answer.documents.length > 0 && (
                <div className="bg-white border border-gray-200 rounded p-5 shadow-sm">
                  <div className="flex items-center gap-2 mb-3">
                    <FileText className="w-5 h-5 text-primary-700" />
                    <h2 className="text-base font-semibold text-gray-900">Documents to prepare</h2>
                  </div>
                  <ul className="space-y-1.5 text-sm text-gray-800 list-disc list-inside pl-1">
                    {answer.documents.map((doc, idx) => (
                      <li key={idx}>{doc}</li>
                    ))}
                  </ul>
                  {sources[0] && <SourceCard source={sources[0]} />}
                </div>
              )}

              {/* 5. DRAFT A COMPLAINT BUTTON */}
              <div className="pt-4 flex justify-end">
                <button
                  type="button"
                  onClick={handleDraftClick}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-800 text-white font-medium text-sm rounded hover:bg-primary-900 focus:ring-2 focus:ring-primary-600 shadow-sm"
                >
                  <span>Draft a complaint</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* If no result yet and not loading */}
      {!result && !loading && !error && (
        <div className="p-8 text-center bg-white border border-gray-200 rounded">
          <p className="text-sm text-gray-600">
            Please enter your grievance or question above, or visit the{' '}
            <Link to="/" className="text-primary-700 font-medium underline">
              Home page
            </Link>
            .
          </p>
        </div>
      )}
    </div>
  )
}
