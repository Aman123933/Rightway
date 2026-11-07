import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { api } from '../api'

vi.mock('../api', () => ({
  api: {
    getHealth: vi.fn(),
    getEmergency: vi.fn(),
    ask: vi.fn(),
    draft: vi.fn(),
    getLibrary: vi.fn(),
    recheck: vi.fn(),
  },
  setSlowServerListener: vi.fn(),
}))

describe('Step 1: App Shell and Emergency Panel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.getLibrary.mockResolvedValue([])
  })

  it('renders "Need help now?" emergency button on all 5 routes', async () => {
    const routes = ['/', '/answer', '/draft', '/sources', '/about']

    for (const route of routes) {
      const { unmount } = render(
        <MemoryRouter initialEntries={[route]}>
          <App />
        </MemoryRouter>
      )

      const helpButtons = screen.getAllByRole('button', { name: /Need help now\?/i })
      expect(helpButtons.length).toBeGreaterThan(0)
      unmount()
    }
  })

  it('opens emergency panel with contacts from getEmergency', async () => {
    api.getEmergency.mockResolvedValueOnce({
      contacts: [
        {
          label: 'National Anti-Ragging Helpline',
          phone: '1800-180-5522',
          email: 'helpline@antiragging.in',
          hours: '24x7',
          url: 'https://antiragging.in',
          source_id: 'anti-ragging-doc',
        },
      ],
      note: "If you are in immediate danger, call 112 (India's emergency number).",
    })

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    )

    const helpButton = screen.getAllByRole('button', { name: /Need help now\?/i })[0]
    fireEvent.click(helpButton)

    // Check emergency dialog appears
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    // 112 note
    expect(screen.getByText(/If you are in immediate danger/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Call 112 Now/i })).toBeInTheDocument()

    // Contacts loaded
    await waitFor(() => {
      expect(screen.getByText('National Anti-Ragging Helpline')).toBeInTheDocument()
      expect(screen.getByText('1800-180-5522')).toBeInTheDocument()
      expect(screen.getByText('helpline@antiragging.in')).toBeInTheDocument()
    })

    // Close modal
    fireEvent.click(screen.getByLabelText(/Close emergency panel/i))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('shows 112 note even when emergency API call fails', async () => {
    api.getEmergency.mockRejectedValueOnce(new Error('Network error'))

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    )

    const helpButton = screen.getAllByRole('button', { name: /Need help now\?/i })[0]
    fireEvent.click(helpButton)

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText(/If you are in immediate danger, call 112/i)).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Call 112 Now/i })).toBeInTheDocument()
    })
  })
})
