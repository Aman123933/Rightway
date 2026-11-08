const BASE_URL = import.meta.env.VITE_API_URL || ''

let slowServerListener = null

export function setSlowServerListener(fn) {
  slowServerListener = fn
}

export async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  const makeAttempt = async () => {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 15000)

    // Trigger waking-up notice after 3.5s of waiting
    const slowTimer = setTimeout(() => {
      if (slowServerListener) {
        slowServerListener(true)
      }
    }, 3500)

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      clearTimeout(slowTimer)
      if (slowServerListener) slowServerListener(false)

      const contentType = response.headers.get('content-type') || ''
      const isJson = contentType.includes('application/json')

      if (!isJson && response.ok) {
        throw new Error(
          'Backend returned a non-JSON response. Please verify that FastAPI is running on http://127.0.0.1:8000.'
        )
      }

      const data = isJson ? await response.json() : await response.text()

      if (!response.ok) {
        const error = new Error(
          isJson && data?.detail
            ? typeof data.detail === 'string'
              ? data.detail
              : JSON.stringify(data.detail)
            : `Request failed with status ${response.status}`
        )
        error.status = response.status
        error.data = data
        throw error
      }

      return data
    } catch (err) {
      clearTimeout(timeoutId)
      clearTimeout(slowTimer)
      if (slowServerListener) slowServerListener(false)
      throw err
    }
  }

  try {
    return await makeAttempt()
  } catch (firstErr) {
    // If it's a 4xx client error (e.g. 401 unauthorized or 422 validation), do not retry
    if (firstErr.status && firstErr.status >= 400 && firstErr.status < 500) {
      throw firstErr
    }
    // Inform user of potential server wake-up before retry
    if (slowServerListener) slowServerListener(true)
    // Retry once
    try {
      const result = await makeAttempt()
      if (slowServerListener) slowServerListener(false)
      return result
    } catch (secondErr) {
      if (slowServerListener) slowServerListener(false)
      throw secondErr
    }
  }
}

export const api = {
  getHealth: () => request('/api/health'),
  getEmergency: () => request('/api/emergency'),
  ask: (message, category) => {
    const body = { message }
    if (category) body.category = category
    return request('/api/ask', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  draft: (category, details, record_ids = []) =>
    request('/api/draft', {
      method: 'POST',
      body: JSON.stringify({ category, details, record_ids }),
    }),
  getLibrary: () => request('/api/library'),
  recheck: (token, { record_id, all, simulate_change } = {}) => {
    const body = {}
    if (record_id) body.record_id = record_id
    if (all !== undefined) body.all = all
    if (simulate_change !== undefined) body.simulate_change = simulate_change

    return request('/api/recheck', {
      method: 'POST',
      headers: {
        'X-Admin-Token': token,
      },
      body: JSON.stringify(body),
    })
  },
}
