import React from 'react'
import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-sm text-gray-600">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <span className="font-semibold text-gray-900">RightWay</span> — Student Rights & Grievance Navigator
            <p className="text-xs text-gray-700 mt-1">
              Information provided is for official procedural guidance and does not constitute formal legal advice.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <Link to="/about" className="hover:text-gray-900 underline">
              About & Disclaimers
            </Link>
            <Link to="/sources" className="hover:text-gray-900 underline">
              Official Sources
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
