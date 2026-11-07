import React, { useState } from 'react'
import { NavLink, Link } from 'react-router-dom'
import { ShieldAlert, Menu, X } from 'lucide-react'

export default function Navbar({ onOpenEmergency }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navLinks = [
    { to: '/', label: 'Home' },
    { to: '/answer', label: 'Answer' },
    { to: '/draft', label: 'Draft' },
    { to: '/sources', label: 'Sources' },
    { to: '/about', label: 'About & Limits' },
  ]

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo / Brand */}
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2 text-primary-900 font-bold text-lg tracking-tight">
              <span>RightWay</span>
              <span className="text-xs font-normal text-gray-700 px-2 py-0.5 bg-gray-100 rounded border border-gray-200">
                Student Rights
              </span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-1" aria-label="Main Navigation">
              {navLinks.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    `px-3 py-2 rounded text-sm font-medium transition-colors ${
                      isActive
                        ? 'text-primary-800 bg-primary-50 font-semibold'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`
                  }
                >
                  {link.label}
                </NavLink>
              ))}
            </nav>
          </div>

          {/* Emergency Help Button (visible on all screens) & Mobile Toggle */}
          <div className="flex items-center gap-3">
            <button
              onClick={onOpenEmergency}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-red-700 text-white text-sm font-semibold rounded hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2 transition-colors"
              aria-label="Need help now? Emergency assistance"
            >
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>Need help now?</span>
            </button>

            {/* Mobile menu button */}
            <button
              type="button"
              className="md:hidden p-2 rounded text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-600"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white px-4 pt-2 pb-3 space-y-1">
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                `block px-3 py-2 rounded text-base font-medium ${
                  isActive
                    ? 'text-primary-800 bg-primary-50 font-semibold'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      )}
    </header>
  )
}
