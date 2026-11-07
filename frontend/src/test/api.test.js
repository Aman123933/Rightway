import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api, request, setSlowServerListener } from '../api'

describe('API wrapper tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    global.fetch = vi.fn()
  })

  afterEach(() => {
    setSlowServerListener(null)
  })

  it('performs JSON request and parses response', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ ok: true, library_count: 5 }),
    })

    const res = await api.getHealth()
    expect(res).toEqual({ ok: true, library_count: 5 })
    expect(global.fetch).toHaveBeenCalledTimes(1)
  })

  it('retries once on network failure', async () => {
    global.fetch
      .mockRejectedValueOnce(new Error('Network drop'))
      .mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ ok: true }),
      })

    const res = await api.getHealth()
    expect(res).toEqual({ ok: true })
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })

  it('does NOT retry on 401 Unauthorized', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      headers: { get: () => 'application/json' },
      json: async () => ({ detail: 'Unauthorized' }),
    })

    await expect(api.recheck('wrong-token', { all: true })).rejects.toThrow('Unauthorized')
    expect(global.fetch).toHaveBeenCalledTimes(1)
  })
})
