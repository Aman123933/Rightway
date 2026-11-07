import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Home from '../pages/Home'
import Answer from '../pages/Answer'
import { api } from '../api'

vi.mock('../api', () => ({
  api: {
    ask: vi.fn(),
  },
  setSlowServerListener: vi.fn(),
}))

describe('Step 2: Home and Answer Pages', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('enforces 1000-character limit and shows character count on Home page', () => {
    render(
      <MemoryRouter>
        <Home onOpenEmergency={vi.fn()} />
      </MemoryRouter>
    )

    const textarea = screen.getByLabelText(/Describe what happened/i)
    expect(textarea).toHaveAttribute('maxLength', '1000')

    fireEvent.change(textarea, { target: { value: 'Hello' } })
    expect(screen.getByText('5 / 1000 characters')).toBeInTheDocument()
  })

  it('sends category choice in request when chip is selected', async () => {
    api.ask.mockResolvedValueOnce({
      safety: { triggered: false, categories: [], message: '', contacts: [] },
      category: 'fee_refund',
      not_found: false,
      answer: { summary: 'Fee refund steps', office: null, steps: [], time_limits: [], documents: [] },
      sources: [],
    })

    render(
      <MemoryRouter>
        <Home onOpenEmergency={vi.fn()} />
      </MemoryRouter>
    )

    const feeChip = screen.getByRole('button', { name: 'Fee refund' })
    fireEvent.click(feeChip)

    const textarea = screen.getByLabelText(/Describe what happened/i)
    fireEvent.change(textarea, { target: { value: 'Need refund for cancelled admission' } })

    const submitBtn = screen.getByRole('button', { name: /Find my route/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(api.ask).toHaveBeenCalledWith('Need refund for cancelled admission', 'fee_refund')
    })
  })

  it('omits category when no chip is selected', async () => {
    api.ask.mockResolvedValueOnce({
      safety: { triggered: false, categories: [], message: '', contacts: [] },
      category: 'other',
      not_found: false,
      answer: { summary: 'General grievance steps', office: null, steps: [], time_limits: [], documents: [] },
      sources: [],
    })

    render(
      <MemoryRouter>
        <Home onOpenEmergency={vi.fn()} />
      </MemoryRouter>
    )

    const textarea = screen.getByLabelText(/Describe what happened/i)
    fireEvent.change(textarea, { target: { value: 'General grievance query' } })

    const submitBtn = screen.getByRole('button', { name: /Find my route/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(api.ask).toHaveBeenCalledWith('General grievance query', undefined)
    })
  })

  it('shows error with a Retry button on Home page if request fails', async () => {
    api.ask.mockRejectedValueOnce(new Error('Backend offline'))

    render(
      <MemoryRouter>
        <Home onOpenEmergency={vi.fn()} />
      </MemoryRouter>
    )

    const textarea = screen.getByLabelText(/Describe what happened/i)
    fireEvent.change(textarea, { target: { value: 'Fee query' } })

    const submitBtn = screen.getByRole('button', { name: /Find my route/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText('Backend offline')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument()
    })
  })

  it('renders safety panel FIRST before answer cards when safety is triggered', () => {
    const mockSafetyResult = {
      safety: {
        triggered: true,
        categories: ['ragging'],
        message: 'Urgent safety alert. If you are in immediate danger, call 112.',
        contacts: [
          {
            label: 'Anti-Ragging Squad',
            phone: '18001805522',
            email: 'squad@example.com',
            hours: '24 Hours',
            url: null,
            source_id: 'src-1',
          },
        ],
      },
      category: 'ragging',
      not_found: false,
      answer: {
        summary: 'Emergency protocol initiated.',
        office: null,
        steps: ['Contact squad', 'Inform warden'],
        time_limits: ['Immediate'],
        documents: [],
      },
      sources: [
        {
          id: 'src-1',
          title: 'Anti-Ragging Regulation',
          url: 'https://antiragging.in/rules',
          quote: 'Ragging is strictly prohibited in any form.',
          fetched_at: '2026-11-07T12:00:00Z',
          status: 'current',
        },
      ],
    }

    render(
      <MemoryRouter initialEntries={[{ pathname: '/answer', state: { result: mockSafetyResult } }]}>
        <Answer onOpenEmergency={vi.fn()} />
      </MemoryRouter>
    )

    const safetyHeading = screen.getByRole('heading', { name: /Immediate Safety Alert/i })
    expect(safetyHeading).toBeInTheDocument()

    // Safety panel contains 112
    expect(screen.getByRole('link', { name: /Emergency 112/i })).toBeInTheDocument()
    expect(screen.getByText('Anti-Ragging Squad')).toBeInTheDocument()
  })

  it('displays every card with date, domain and status chip', () => {
    const mockResult = {
      safety: { triggered: false, categories: [], message: '', contacts: [] },
      category: 'fee_refund',
      not_found: false,
      answer: {
        summary: 'Full refund within 15 days of withdrawal.',
        office: {
          label: 'Registrar Office',
          phone: '011-23232323',
          email: 'registrar@institution.edu.in',
          hours: '10am-5pm',
          url: 'https://institution.edu.in',
          source_id: 'src-1',
        },
        steps: ['Submit application', 'Return library cards'],
        time_limits: ['15 days from notice'],
        documents: ['Admission receipt'],
        portal_url: 'https://samarth.edu.in',
      },
      sources: [
        {
          id: 'src-1',
          title: 'UGC Fee Refund Norms 2023',
          url: 'https://ugc.gov.in/fee-refund-notification.pdf',
          quote: 'Higher education institutions shall refund the full fee upon withdrawal.',
          fetched_at: '2026-11-07T12:00:00Z',
          status: 'current',
        },
      ],
    }

    render(
      <MemoryRouter initialEntries={[{ pathname: '/answer', state: { result: mockResult } }]}>
        <Answer onOpenEmergency={vi.fn()} />
      </MemoryRouter>
    )

    // Check Cards
    expect(screen.getByRole('heading', { name: /What applies/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Where to go/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Steps to follow/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Prescribed time limits/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Documents to prepare/i })).toBeInTheDocument()

    // Domain extracted
    expect(screen.getAllByText('(ugc.gov.in)').length).toBeGreaterThan(0)

    // Date formatted
    expect(screen.getAllByText(/Checked 7 Nov 2026/i).length).toBeGreaterThan(0)

    // Status chip
    expect(screen.getAllByText('Current').length).toBeGreaterThan(0)

    // Expandable quote
    const quoteButton = screen.getAllByRole('button', { name: /See the source text/i })[0]
    expect(quoteButton).toBeInTheDocument()
    fireEvent.click(quoteButton)
    expect(screen.getByText(/Higher education institutions shall refund the full fee upon withdrawal/i)).toBeInTheDocument()
  })

  it('renders not_found state cleanly without empty cards and links to Sources', () => {
    const mockNotFoundResult = {
      safety: { triggered: false, categories: [], message: '', contacts: [] },
      category: 'other',
      not_found: true,
      answer: { summary: '', office: null, steps: [], time_limits: [], documents: [] },
      sources: [],
      fallback: "Contact your institution's grievance cell.",
    }

    render(
      <MemoryRouter initialEntries={[{ pathname: '/answer', state: { result: mockNotFoundResult } }]}>
        <Answer onOpenEmergency={vi.fn()} />
      </MemoryRouter>
    )

    expect(screen.getByText(/No matching institutional rule found/i)).toBeInTheDocument()
    expect(screen.getByText(/Contact your institution's grievance cell./i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /See which pages RightWay has read/i })).toBeInTheDocument()

    // Ensure no empty cards are shown
    expect(screen.queryByRole('heading', { name: /^What applies$/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /^Where to go$/i })).not.toBeInTheDocument()
  })
})
