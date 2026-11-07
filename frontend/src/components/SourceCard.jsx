import React, { useState } from 'react'
import StatusChip from './StatusChip'
import { ExternalLink, ChevronDown, ChevronUp } from 'lucide-react'

export function extractDomain(url) {
  try {
    const parsed = new URL(url)
    return parsed.hostname.replace(/^www\./, '')
  } catch {
    return url || ''
  }
}

export function formatDate(dateStr) {
  if (!dateStr) return 'Not checked'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return d.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

export default function SourceCard({ source }) {
  const [expanded, setExpanded] = useState(false)

  if (!source) return null

  const domain = extractDomain(source.url || source.source_url)
  const formattedDate = formatDate(source.fetched_at)

  return (
    <div className="mt-3 pt-3 border-t border-gray-100 text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center flex-wrap gap-2">
          <span className="text-gray-500 font-medium">Source:</span>
          <a
            href={source.url || source.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-700 hover:underline font-medium inline-flex items-center gap-1"
          >
            <span>{source.title}</span>
            <ExternalLink className="w-3 h-3" />
          </a>
          {domain && (
            <span className="text-gray-700 font-mono text-[11px]">
              ({domain})
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-gray-700">Checked {formattedDate}</span>
          <StatusChip status={source.status} isSimulated={source.simulated} />
        </div>
      </div>

      {(source.quote || source.source_quote) && (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-800 font-medium focus:outline-none"
            aria-expanded={expanded}
          >
            <span>See the source text</span>
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          {expanded && (
            <div className="mt-2 p-2.5 bg-gray-50 border-l-2 border-primary-600 rounded-r text-gray-700 font-serif text-xs leading-relaxed italic">
              "{source.quote || source.source_quote}"
            </div>
          )}
        </div>
      )}
    </div>
  )
}
