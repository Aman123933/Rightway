import React from 'react'

export default function StatusChip({ status, isSimulated }) {
  let label = 'Current'
  let colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-200'

  if (status === 'needs_recheck') {
    label = 'Needs recheck'
    colorClasses = 'bg-amber-50 text-amber-800 border-amber-200'
  } else if (status === 'changed') {
    label = isSimulated ? 'Changed (Simulated)' : 'Changed'
    colorClasses = 'bg-red-50 text-red-800 border-red-200'
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colorClasses}`}
    >
      {label}
    </span>
  )
}
