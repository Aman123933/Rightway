import React from 'react'
import { ShieldCheck, Info, AlertTriangle, FileText, Database, Lock } from 'lucide-react'

export default function About() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
          About RightWay & Limitations
        </h1>
        <p className="mt-2 text-sm text-gray-600">
          Understanding procedural scope, data sources, safety safeguards, and AI disclosures.
        </p>
      </div>

      <div className="space-y-6">
        {/* Section 1: What RightWay is & Not Legal Advice */}
        <section className="bg-white border border-gray-200 rounded p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-5 h-5 text-primary-700" />
            <h2 className="text-base font-semibold text-gray-900">What RightWay Is</h2>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed mb-3">
            RightWay is a student rights and grievance navigation platform designed to provide transparent, direct access to official university rules, statutory protections, committee procedures, and resolution timelines.
          </p>
          <div className="p-3.5 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900 font-medium leading-relaxed">
            <strong>Important Legal Disclaimer:</strong> RightWay does not provide legal advice or legal representation. The information generated reflects publicly available regulatory procedures and guidelines. For formal legal disputes, consult an advocate or legal aid clinic.
          </div>
        </section>

        {/* Section 2: How the Safety Check Works */}
        <section className="bg-white border border-gray-200 rounded p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="w-5 h-5 text-primary-700" />
            <h2 className="text-base font-semibold text-gray-900">Urgent Safety Safeguards</h2>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed mb-2">
            RightWay employs an immediate zero-AI keyword safety gate for issues involving ragging, harassment, physical assault, threats, and self-harm. When detected, the system immediately surfaces verified emergency helplines and national response numbers (such as India's 112).
          </p>
          <p className="text-xs text-gray-600 leading-relaxed">
            Because this gate looks for explicit terms and can miss indirect wording or euphemisms, the <strong>"Need help now?"</strong> button is permanently pinned on every page and accessible across all devices at all times.
          </p>
        </section>

        {/* Section 3: Official Data Sources & TinyFish Integration */}
        <section className="bg-white border border-gray-200 rounded p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Database className="w-5 h-5 text-primary-700" />
            <h2 className="text-base font-semibold text-gray-900">Where the Information Comes From</h2>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed mb-3">
            RightWay builds its library strictly from published, public documents: official institutional websites and national regulatory bodies (including the University Grants Commission - UGC, AICTE, and national anti-ragging authorities).
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mb-3">
            These documents are discovered using TinyFish Search to map official domains, fetched via TinyFish Fetch, and continuously monitored for changes using cryptographic hash comparisons. If a specific page could not be located or read, RightWay explicitly states so and directs the student to their institution's grievance cell rather than guessing or fabricating advice.
          </p>
          <div className="p-3 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700">
            <strong>Institution vs. National Rules:</strong> Specific institutional statutes or college handbooks may prescribe supplementary internal committees or formats that build upon national minimum standards. Always confirm with your institution's notified guidelines.
          </div>
        </section>

        {/* Section 4: AI Disclosure & Privacy */}
        <section className="bg-white border border-gray-200 rounded p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Lock className="w-5 h-5 text-primary-700" />
            <h2 className="text-base font-semibold text-gray-900">AI Usage & Student Privacy</h2>
          </div>
          <ul className="space-y-2 text-sm text-gray-700 list-disc list-inside">
            <li>
              <strong>Zero-AI for rules and dates:</strong> Artificial intelligence is never permitted to invent rules, deadlines, email addresses, or phone numbers. All answers are derived directly from indexed library records.
            </li>
            <li>
              <strong>Assisted drafting:</strong> Google Gemini is used solely to assist students in structuring clear, formal letters from their factual inputs and cited regulation records.
            </li>
            <li>
              <strong>Zero storage of student messages:</strong> RightWay does not store user prompts, complaint details, or contact information in any database or tracking log.
            </li>
          </ul>
        </section>
      </div>
    </div>
  )
}
