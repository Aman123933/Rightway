import React, { useState, useEffect } from 'react'
import { api } from '../api'
import StatusChip from '../components/StatusChip'
import { extractDomain, formatDate } from '../components/SourceCard'
import { ExternalLink, RefreshCw, AlertCircle, PlayCircle, Loader2 } from 'lucide-react'

export default function Sources() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCategory, setSelectedCategory] = useState('all')

  // In-memory token ONLY (never stored in localStorage or sessionStorage)
  const [adminToken, setAdminToken] = useState('')
  const [recheckMessage, setRecheckMessage] = useState(null)
  const [recheckError, setRecheckError] = useState(null)
  const [actionInProgress, setActionInProgress] = useState(null) // 'all', 'simulate', or record_id

  useEffect(() => {
    fetchLibrary()
  }, [])

  const fetchLibrary = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getLibrary()
      setRecords(data || [])
    } catch (err) {
      setError(err.message || 'Failed to load official sources library.')
    } finally {
      setLoading(false)
    }
  }

  // Handle recheck
  const handleRecheck = async ({ recordId, all, simulateChange }) => {
    setRecheckMessage(null)
    setRecheckError(null)

    if (!adminToken) {
      setRecheckError('The admin token was not accepted.')
      return
    }

    const actionKey = simulateChange ? 'simulate' : (recordId || 'all')
    setActionInProgress(actionKey)

    try {
      const response = await api.recheck(adminToken, {
        record_id: recordId,
        all: all,
        simulate_change: simulateChange,
      })

      const results = response?.results || []
      setRecords((prev) =>
        prev.map((r) => {
          const res = results.find((resItem) => resItem.id === r.id)
          if (!res) return r
          return {
            ...r,
            status: res.status,
            simulated: res.simulated,
            recheck_error: res.error || null,
          }
        })
      )

      if (simulateChange) {
        setRecheckMessage('Simulated change applied successfully for demo purposes.')
      } else {
        setRecheckMessage(`Recheck completed for ${results.length} record(s).`)
      }
    } catch (err) {
      if (err.status === 401) {
        setRecheckError('The admin token was not accepted.')
      } else {
        setRecheckError(err.message || 'Recheck request failed.')
      }
    } finally {
      setActionInProgress(null)
    }
  }

  // Categories list for filter
  const categoryOptions = [
    { label: 'All categories', value: 'all' },
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

  const filteredRecords = records.filter((r) => {
    if (selectedCategory === 'all') return true
    const cats = Array.isArray(r.category) ? r.category : [r.category]
    return cats.includes(selectedCategory)
  })

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
          Official Information Library
        </h1>
        <p className="mt-2 text-sm text-gray-600">
          Public regulatory documents, university statutes, and grievance procedures tracked by RightWay.
        </p>
      </div>

      {/* Admin Recheck Controls */}
      <div className="bg-white border border-gray-200 rounded p-5 mb-8 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">
          Source Recheck & Verification Controls
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 items-end">
          <div className="lg:col-span-2">
            <label htmlFor="admin-token-input" className="block text-xs font-medium text-gray-700 mb-1">
              Admin Token (in-memory only)
            </label>
            <input
              id="admin-token-input"
              type="password"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
              placeholder="Enter admin token..."
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:border-primary-600 focus:ring-1 focus:ring-primary-600"
            />
          </div>

          <div>
            <button
              type="button"
              onClick={() => handleRecheck({ all: true })}
              disabled={Boolean(actionInProgress)}
              className="w-full inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-primary-800 text-white text-xs font-semibold rounded hover:bg-primary-900 disabled:opacity-50"
            >
              {actionInProgress === 'all' ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              <span>Recheck all sources</span>
            </button>
          </div>

          <div>
            <button
              type="button"
              onClick={() => handleRecheck({ simulateChange: true })}
              disabled={Boolean(actionInProgress)}
              className="w-full inline-flex items-center justify-center gap-1.5 px-4 py-2 border border-amber-600 text-amber-900 bg-amber-50 text-xs font-semibold rounded hover:bg-amber-100 disabled:opacity-50"
            >
              {actionInProgress === 'simulate' ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <PlayCircle className="w-4 h-4 text-amber-700" />
              )}
              <span>Simulate a change (demo only)</span>
            </button>
          </div>
        </div>

        {recheckError && (
          <div className="mt-3 p-2.5 bg-red-50 border border-red-200 rounded text-xs text-red-800 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
            <span>{recheckError}</span>
          </div>
        )}

        {recheckMessage && (
          <div className="mt-3 p-2.5 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800">
            {recheckMessage}
          </div>
        )}
      </div>

      {/* Library Top Bar: Count & Category Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div className="text-sm font-medium text-gray-700" data-testid="library-count">
          Showing {filteredRecords.length} of {records.length} verified sources
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="sources-category-filter" className="text-xs font-medium text-gray-600">
            Filter by category:
          </label>
          <select
            id="sources-category-filter"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1.5 text-xs bg-white border border-gray-300 rounded focus:border-primary-600 focus:ring-1 focus:ring-primary-600"
          >
            {categoryOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="bg-white border border-gray-200 rounded p-12 text-center text-gray-500 text-sm">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-primary-700" />
          Loading sources library...
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded p-6 text-center text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Empty library state */}
      {!loading && !error && records.length === 0 && (
        <div className="bg-white border border-gray-200 rounded p-12 text-center">
          <p className="text-sm text-gray-600 font-medium">
            No sources loaded yet. Ask the team to run the library build.
          </p>
        </div>
      )}

      {/* Non-empty records view */}
      {!loading && !error && records.length > 0 && (
        <>
          {/* Desktop Table View */}
          <div className="hidden md:block bg-white border border-gray-200 rounded overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-gray-200 text-left text-xs">
              <thead className="bg-gray-50 text-gray-700 font-semibold uppercase tracking-wider">
                <tr>
                  <th scope="col" className="px-4 py-3">Document Title</th>
                  <th scope="col" className="px-4 py-3">Type</th>
                  <th scope="col" className="px-4 py-3">Category</th>
                  <th scope="col" className="px-4 py-3">Domain / URL</th>
                  <th scope="col" className="px-4 py-3">Last Checked</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {filteredRecords.map((r) => {
                  const domain = extractDomain(r.source_url)
                  const cats = Array.isArray(r.category) ? r.category : [r.category]
                  const isCurrentAction = actionInProgress === r.id

                  return (
                    <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3.5 font-medium text-gray-900 max-w-xs">
                        <div>{r.title}</div>
                        {r.recheck_error && (
                          <div className="text-[11px] text-red-600 mt-1">
                            Recheck note: {r.recheck_error}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3.5 text-gray-600 uppercase text-[11px]">
                        {r.type}
                      </td>
                      <td className="px-4 py-3.5 text-gray-600">
                        <div className="flex flex-wrap gap-1">
                          {cats.map((c, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-gray-100 rounded text-[10px]">
                              {c.replace('_', ' ')}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <a
                          href={r.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-700 hover:underline font-mono inline-flex items-center gap-1 text-[11px]"
                        >
                          <span>{domain}</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </td>
                      <td className="px-4 py-3.5 text-gray-700 whitespace-nowrap">
                        {formatDate(r.fetched_at)}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <StatusChip status={r.status} isSimulated={r.simulated} />
                      </td>
                      <td className="px-4 py-3.5 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => handleRecheck({ recordId: r.id })}
                          disabled={Boolean(actionInProgress)}
                          className="px-2.5 py-1 border border-gray-300 text-gray-700 rounded hover:bg-gray-100 text-[11px] font-medium disabled:opacity-50"
                        >
                          {isCurrentAction ? 'Checking...' : 'Recheck this page'}
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile Card View */}
          <div className="md:hidden space-y-4">
            {filteredRecords.map((r) => {
              const domain = extractDomain(r.source_url)
              const cats = Array.isArray(r.category) ? r.category : [r.category]
              const isCurrentAction = actionInProgress === r.id

              return (
                <div key={r.id} className="bg-white border border-gray-200 rounded p-4 shadow-sm text-xs space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-gray-900 text-sm">{r.title}</h3>
                    <StatusChip status={r.status} isSimulated={r.simulated} />
                  </div>

                  <div className="flex flex-wrap gap-1">
                    {cats.map((c, i) => (
                      <span key={i} className="px-1.5 py-0.5 bg-gray-100 rounded text-[10px]">
                        {c.replace('_', ' ')}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center justify-between text-gray-600 pt-1">
                    <a
                      href={r.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-700 hover:underline font-mono inline-flex items-center gap-1"
                    >
                      <span>{domain}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                    <span>Checked {formatDate(r.fetched_at)}</span>
                  </div>

                  {r.recheck_error && (
                    <div className="text-[11px] text-red-600 bg-red-50 p-2 rounded">
                      Recheck error: {r.recheck_error}
                    </div>
                  )}

                  <div className="pt-2 border-t border-gray-100 flex justify-end">
                    <button
                      type="button"
                      onClick={() => handleRecheck({ recordId: r.id })}
                      disabled={Boolean(actionInProgress)}
                      className="px-3 py-1.5 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 font-medium disabled:opacity-50"
                    >
                      {isCurrentAction ? 'Checking...' : 'Recheck this page'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Small Note Under Table */}
          <div className="mt-4 text-xs text-gray-700">
            Note: Recheck results can reset when the free server restarts.
          </div>
        </>
      )}
    </div>
  )
}
