import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Draft from '../pages/Draft'
import { api } from '../api'

vi.mock('../api', () => ({
  api: {
    draft: vi.fn(),
  },
}))

describe('Step 3: Draft Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockImplementation(() => Promise.resolve()),
      },
    })
  })

  it('renders input with 1500 char counter and generates editable draft', async () => {
    const mockDraftText = `To,
The SGRC,
[Institution Name]
Date: [Date]
Subject: Grievance regarding fee refund
Respected Sir,
I, [Your Name], Roll No: [Roll No]...`

    api.draft.mockResolvedValueOnce({
      draft: mockDraftText,
      ai_used: true,
      label: 'AI-assisted draft. Review and edit before sending.',
    })

    render(
      <MemoryRouter initialEntries={[{ pathname: '/draft', state: { category: 'fee_refund', record_ids: ['ugc-1'] } }]}>
        <Draft />
      </MemoryRouter>
    )

    const textarea = screen.getByLabelText(/What happened and when\?/i)
    expect(textarea).toHaveAttribute('maxLength', '1500')

    fireEvent.change(textarea, { target: { value: 'Withdrew admission on 10 Aug.' } })
    expect(screen.getByText('29 / 1500 characters')).toBeInTheDocument()

    const generateBtn = screen.getByRole('button', { name: /Generate draft/i })
    fireEvent.click(generateBtn)

    await waitFor(() => {
      expect(api.draft).toHaveBeenCalledWith('fee_refund', 'Withdrew admission on 10 Aug.', ['ugc-1'])
    })

    // Banner check for AI-assisted
    expect(screen.getByText('AI-assisted draft. Review and edit before sending.')).toBeInTheDocument()

    // Placeholders are untouched and editable
    const draftTextarea = screen.getByLabelText(/Editable Complaint Letter/i)
    expect(draftTextarea.value).toContain('[Your Name]')
    expect(draftTextarea.value).toContain('[Roll No]')
    expect(draftTextarea.value).toContain('[Date]')

    // Test editing draft
    fireEvent.change(draftTextarea, { target: { value: 'Edited draft content' } })
    expect(draftTextarea.value).toBe('Edited draft content')

    // Test Copy button
    const copyBtn = screen.getByRole('button', { name: /Copy/i })
    fireEvent.click(copyBtn)
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Edited draft content')
  })

  it('shows template banner when ai_used is false', async () => {
    api.draft.mockResolvedValueOnce({
      draft: 'Template formal letter [Your Name]',
      ai_used: false,
      label: 'AI-assisted draft. Review and edit before sending.',
    })

    render(
      <MemoryRouter>
        <Draft />
      </MemoryRouter>
    )

    const textarea = screen.getByLabelText(/What happened and when\?/i)
    fireEvent.change(textarea, { target: { value: 'Problem details' } })

    const generateBtn = screen.getByRole('button', { name: /Generate draft/i })
    fireEvent.click(generateBtn)

    await waitFor(() => {
      expect(screen.getByText('Template draft (no AI used)')).toBeInTheDocument()
    })
  })

  it('handles error and retry in draft generation', async () => {
    api.draft.mockRejectedValueOnce(new Error('Drafting service timeout'))

    render(
      <MemoryRouter>
        <Draft />
      </MemoryRouter>
    )

    const textarea = screen.getByLabelText(/What happened and when\?/i)
    fireEvent.change(textarea, { target: { value: 'Problem details' } })

    const generateBtn = screen.getByRole('button', { name: /Generate draft/i })
    fireEvent.click(generateBtn)

    await waitFor(() => {
      expect(screen.getByText('Drafting service timeout')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument()
    })
  })
})
