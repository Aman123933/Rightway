import React, { useState, useEffect } from 'react'
import { api } from '../api'
import { Phone, Mail, Clock, ExternalLink, X, AlertCircle } from 'lucide-react'

export default function EmergencyModal({ isOpen, onClose }) {
  const [contacts, setContacts] = useState([])
  const [note, setNote] = useState("If you are in immediate danger, call 112 (India's emergency number).")
  const [loading, setLoading] = useState(false)
  const [fetchError, setFetchError] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setLoading(true)
      setFetchError(false)
      api.getEmergency()
        .then((data) => {
          if (data?.contacts) setContacts(data.contacts)
          if (data?.note) setNote(data.note)
        })
        .catch(() => {
          setFetchError(true)
          // Ensure note is always present
          setNote("If you are in immediate danger, call 112 (India's emergency number).")
        })
        .finally(() => {
          setLoading(false)
        })
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-labelledby="emergency-title"
    >
      <div className="relative w-full max-w-lg bg-white rounded border border-gray-200 shadow-xl overflow-hidden p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between pb-4 border-b border-gray-100">
          <div>
            <h2 id="emergency-title" className="text-xl font-semibold text-red-700">
              Emergency & Immediate Assistance
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Urgent support resources for safety, harassment, and crisis situations.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-700 rounded focus:outline-none focus:ring-2 focus:ring-primary-600"
            aria-label="Close emergency panel"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 112 Priority Banner */}
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-700 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-900">{note}</p>
              <div className="mt-2">
                <a
                  href="tel:112"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-700 text-white text-sm font-medium rounded hover:bg-red-800 focus:ring-2 focus:ring-red-600 focus:outline-none"
                >
                  <Phone className="w-4 h-4" />
                  Call 112 Now
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Emergency Contacts List */}
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">
            Official Helplines
          </h3>

          {loading ? (
            <div className="py-8 text-center text-gray-500 text-sm">
              Loading emergency contacts...
            </div>
          ) : contacts && contacts.length > 0 ? (
            <div className="space-y-3">
              {contacts.map((c, idx) => (
                <div key={idx} className="p-3 bg-gray-50 border border-gray-200 rounded">
                  <div className="font-medium text-gray-900">{c.label}</div>
                  <div className="mt-2 flex flex-wrap gap-3 text-sm">
                    {c.phone && (
                      <a
                        href={`tel:${c.phone}`}
                        className="inline-flex items-center gap-1 text-primary-700 hover:underline font-medium"
                      >
                        <Phone className="w-3.5 h-3.5" />
                        {c.phone}
                      </a>
                    )}
                    {c.email && (
                      <a
                        href={`mailto:${c.email}`}
                        className="inline-flex items-center gap-1 text-primary-700 hover:underline"
                      >
                        <Mail className="w-3.5 h-3.5" />
                        {c.email}
                      </a>
                    )}
                    {c.hours && (
                      <span className="inline-flex items-center gap-1 text-gray-600 text-xs">
                        <Clock className="w-3.5 h-3.5" />
                        {c.hours}
                      </span>
                    )}
                    {c.url && (
                      <a
                        href={c.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-primary-700 hover:underline text-xs"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Official portal
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-gray-600 py-2">
              {fetchError 
                ? "Unable to load secondary helplines at this moment. Please use 112 immediately."
                : "No secondary helplines configured in library. Please use 112."}
            </div>
          )}
        </div>

        <div className="mt-6 pt-4 border-t border-gray-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
