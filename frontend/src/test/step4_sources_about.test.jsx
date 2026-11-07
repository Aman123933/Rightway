import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Sources from '../pages/Sources'
import About from '../pages/About'
import { api } from '../api'

vi.mock('../api', () => ({
  api: {
    getLibrary: vi.fn(),
    recheck: vi.fn(),
  },
}))

describe('Step 4: Sources and About Pages', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
  })

  it('renders sources table with statuses, domains and record count', async () => {
    const mockLibrary = [
      {
        id: 'ugc-rule-1',
        title: 'UGC Fee Refund Norms',
        type: 'rule',
        category: ['fee_refund'],
        source_url: 'https://ugc.gov.in/fee-regulations.pdf',
        fetched_at: '2026-11-07T12:00:00Z',
        status: 'current',
      },
      {
        id: 'aicte-rule-2',
        title: 'AICTE Student Handbook',
        type: 'procedure',
        category: ['admission'],
        source_url: 'https://aicte-india.org/handbook.pdf',
        fetched_at: '2026-11-06T10:00:00Z',
        status: 'needs_recheck',
      },
    ]

    api.getLibrary.mockResolvedValueOnce(mockLibrary)

    render(
      <MemoryRouter>
        <Sources />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Showing 2 of 2 verified sources')).toBeInTheDocument()
      expect(screen.getAllByText('UGC Fee Refund Norms').length).toBeGreaterThan(0)
      expect(screen.getAllByText('AICTE Student Handbook').length).toBeGreaterThan(0)
      expect(screen.getAllByText('ugc.gov.in').length).toBeGreaterThan(0)
      expect(screen.getAllByText('aicte-india.org').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Current').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Needs recheck').length).toBeGreaterThan(0)
    })
  })

  it('filters sources by category', async () => {
    const mockLibrary = [
      {
        id: 'ugc-fee',
        title: 'UGC Fee Refund Norms',
        type: 'rule',
        category: ['fee_refund'],
        source_url: 'https://ugc.gov.in/fee.pdf',
        fetched_at: '2026-11-07T12:00:00Z',
        status: 'current',
      },
      {
        id: 'hostel-rules',
        title: 'Hostel Allotment Guidelines',
        type: 'rule',
        category: ['hostel'],
        source_url: 'https://institution.edu.in/hostel.pdf',
        fetched_at: '2026-11-06T10:00:00Z',
        status: 'current',
      },
    ]

    api.getLibrary.mockResolvedValueOnce(mockLibrary)

    render(
      <MemoryRouter>
        <Sources />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getAllByText('UGC Fee Refund Norms').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Hostel Allotment Guidelines').length).toBeGreaterThan(0)
    })

    const select = screen.getByLabelText(/Filter by category:/i)
    fireEvent.change(select, { target: { value: 'hostel' } })

    expect(screen.queryByText('UGC Fee Refund Norms')).not.toBeInTheDocument()
    expect(screen.getAllByText('Hostel Allotment Guidelines').length).toBeGreaterThan(0)
    expect(screen.getByText('Showing 1 of 2 verified sources')).toBeInTheDocument()
  })

  it('displays empty library message and does not show an empty table', async () => {
    api.getLibrary.mockResolvedValueOnce([])

    render(
      <MemoryRouter>
        <Sources />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(
        screen.getByText(/No sources loaded yet. Ask the team to run the library build./i)
      ).toBeInTheDocument()
      expect(screen.queryByRole('table')).not.toBeInTheDocument()
    })
  })

  it('performs single-record recheck sending record_id and updates status chip', async () => {
    const mockLibrary = [
      {
        id: 'rec-1',
        title: 'Test Rule',
        type: 'rule',
        category: ['other'],
        source_url: 'https://ugc.gov.in/test.pdf',
        fetched_at: '2026-11-07T12:00:00Z',
        status: 'needs_recheck',
      },
    ]
    api.getLibrary.mockResolvedValueOnce(mockLibrary)
    api.recheck.mockResolvedValueOnce({
      results: [{ id: 'rec-1', status: 'current', changed: false, simulated: false, error: null }],
    })

    render(
      <MemoryRouter>
        <Sources />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getAllByText('Test Rule').length).toBeGreaterThan(0)
    })

    // Enter token
    const tokenInput = screen.getByLabelText(/Admin Token/i)
    fireEvent.change(tokenInput, { target: { value: 'my-secret-token' } })

    // Verify token is NOT written to storage
    expect(localStorage.getItem('admin_token')).toBeNull()
    expect(sessionStorage.getItem('admin_token')).toBeNull()

    // Click single record recheck
    const singleRecheckBtn = screen.getAllByRole('button', { name: /Recheck this page/i })[0]
    fireEvent.click(singleRecheckBtn)

    await waitFor(() => {
      expect(api.recheck).toHaveBeenCalledWith('my-secret-token', {
        record_id: 'rec-1',
        all: undefined,
        simulate_change: undefined,
      })
      expect(screen.getAllByText('Current').length).toBeGreaterThan(0)
    })
  })

  it('displays simulated change with "Simulated" label', async () => {
    const mockLibrary = [
      {
        id: 'rec-1',
        title: 'Test Rule',
        type: 'rule',
        category: ['other'],
        source_url: 'https://ugc.gov.in/test.pdf',
        fetched_at: '2026-11-07T12:00:00Z',
        status: 'current',
      },
    ]
    api.getLibrary.mockResolvedValueOnce(mockLibrary)
    api.recheck.mockResolvedValueOnce({
      results: [{ id: 'rec-1', status: 'changed', changed: true, simulated: true, error: null }],
    })

    render(
      <MemoryRouter>
        <Sources />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getAllByText('Test Rule').length).toBeGreaterThan(0)
    })

    const tokenInput = screen.getByLabelText(/Admin Token/i)
    fireEvent.change(tokenInput, { target: { value: 'my-secret-token' } })

    const simBtn = screen.getByRole('button', { name: /Simulate a change \(demo only\)/i })
    fireEvent.click(simBtn)

    await waitFor(() => {
      expect(api.recheck).toHaveBeenCalledWith('my-secret-token', {
        record_id: undefined,
        all: undefined,
        simulate_change: true,
      })
      expect(screen.getAllByText('Changed (Simulated)').length).toBeGreaterThan(0)
    })
  })

  it('shows "The admin token was not accepted." on 401 error', async () => {
    const mockLibrary = [
      {
        id: 'rec-1',
        title: 'Test Rule',
        type: 'rule',
        category: ['other'],
        source_url: 'https://ugc.gov.in/test.pdf',
        fetched_at: '2026-11-07T12:00:00Z',
        status: 'current',
      },
    ]
    api.getLibrary.mockResolvedValueOnce(mockLibrary)
    const err401 = new Error('Unauthorized')
    err401.status = 401
    api.recheck.mockRejectedValueOnce(err401)

    render(
      <MemoryRouter>
        <Sources />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getAllByText('Test Rule').length).toBeGreaterThan(0)
    })

    const tokenInput = screen.getByLabelText(/Admin Token/i)
    fireEvent.change(tokenInput, { target: { value: 'wrong-token' } })

    const recheckAllBtn = screen.getByRole('button', { name: /Recheck all sources/i })
    fireEvent.click(recheckAllBtn)

    await waitFor(() => {
      expect(screen.getByText('The admin token was not accepted.')).toBeInTheDocument()
    })
  })

  it('renders About page with necessary disclaimers and AI disclosures', () => {
    render(
      <MemoryRouter>
        <About />
      </MemoryRouter>
    )

    expect(screen.getByText(/About RightWay & Limitations/i)).toBeInTheDocument()
    expect(screen.getByText(/Important Legal Disclaimer:/i)).toBeInTheDocument()
    expect(screen.getByText(/Urgent Safety Safeguards/i)).toBeInTheDocument()
    expect(screen.getByText(/Where the Information Comes From/i)).toBeInTheDocument()
    expect(screen.getByText(/Zero storage of student messages/i)).toBeInTheDocument()
  })
})
