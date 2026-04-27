const rawBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const BASE_URL = String(rawBase).replace(/\/$/, '')

function authHeaders() {
  const token = localStorage.getItem('authToken')
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Token ${token}`
  return headers
}

function authHeadersMultipart() {
  const token = localStorage.getItem('authToken')
  const headers = {}
  if (token) headers.Authorization = `Token ${token}`
  return headers
}

/**
 * @param {string} method
 * @param {string} path - e.g. "/subjects/" (leading slash, no base)
 * @param {object} [options]
 * @param {object} [options.body]
 * @param {Record<string, string|number|undefined>} [options.query]
 */
async function request(method, path, { body, query, signal } = {}) {
  let url = `${BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
  if (query && Object.keys(query).length) {
    const q = new URLSearchParams()
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null) q.set(k, String(v))
    }
    url += `?${q.toString()}`
  }
  const isFormData = body instanceof FormData
  const init = { method, headers: isFormData ? authHeadersMultipart() : authHeaders() }
  if (signal) init.signal = signal
  if (body !== undefined && method !== 'GET' && method !== 'HEAD') {
    init.body = isFormData ? body : JSON.stringify(body)
  }
  const res = await fetch(url, init)
  const text = await res.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }
  if (!res.ok) {
    const err = new Error(
      typeof data?.detail === 'string'
        ? data.detail
        : Array.isArray(data?.detail)
          ? data.detail.map((d) => d.msg || d).join(', ')
          : data?.message || res.statusText || 'Request failed',
    )
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

/** Flatten DRF field errors to a short string for alerts. */
export function formatApiError(err) {
  if (!err?.data || typeof err.data !== 'object') return err?.message || 'Something went wrong'
  const d = err.data
  if (typeof d.detail === 'string') return d.detail
  if (Array.isArray(d.detail)) return d.detail.map((x) => (typeof x === 'string' ? x : x.msg || JSON.stringify(x))).join(', ')
  const parts = []
  for (const [key, val] of Object.entries(d)) {
    if (key === 'detail') continue
    if (Array.isArray(val)) parts.push(`${key}: ${val.join(', ')}`)
    else if (typeof val === 'object' && val !== null) parts.push(`${key}: ${JSON.stringify(val)}`)
    else parts.push(`${key}: ${val}`)
  }
  return parts.join(' · ') || err.message
}

export default {
  register(payload) {
    return request('POST', '/auth/users/', { body: payload })
  },

  login(payload) {
    return request('POST', '/auth/token/login/', { body: payload })
  },

  logout() {
    return request('POST', '/auth/token/logout/', {})
  },

  getSubjects(scope = 'enrolled') {
    return request('GET', '/subjects/', { query: { scope } })
  },

  getSubject(id) {
    return request('GET', `/subjects/${id}/`)
  },

  getSubjectProgress(subjectId) {
    return request('GET', `/subjects/${subjectId}/progress/`)
  },

  createSubject(data) {
    return request('POST', '/subjects/', { body: data })
  },

  getTopics(subjectId) {
    return request('GET', '/topics/', { query: { subject: subjectId } })
  },

  getTopic(id) {
    return request('GET', `/topics/${id}/`)
  },

  createTopic(data) {
    return request('POST', '/topics/', { body: data })
  },

  getEnrollments() {
    return request('GET', '/enrollments/')
  },

  enroll(subjectId) {
    return request('POST', '/enrollments/', { body: { subject: subjectId } })
  },

  deleteEnrollment(enrollmentId) {
    return request('DELETE', `/enrollments/${enrollmentId}/`)
  },

  completeBite(biteId) {
    return request('POST', `/bites/${biteId}/complete/`)
  },

  getQuizzes(subjectId) {
    const query = subjectId != null ? { subject: subjectId } : {}
    return request('GET', '/quizzes/', { query })
  },

  getQuiz(id) {
    return request('GET', `/quizzes/${id}/`)
  },

  createQuiz(data) {
    return request('POST', '/quizzes/', { body: data })
  },

  submitQuizAnswer(data) {
    return request('POST', '/quiz-answers/', { body: data })
  },

  getReviewDue() {
    return request('GET', '/reviews/due/')
  },

  postReviewGrade(biteId, grade) {
    return request('POST', `/reviews/${biteId}/grade/`, { body: { grade } })
  },

  getWeeklyProgress(subjectId) {
    return request('GET', `/reviews/weekly-progress/${subjectId}/`)
  },

  getSubjectGoals() {
    return request('GET', '/subject-goals/')
  },

  createSubjectGoal(data) {
    return request('POST', '/subject-goals/', { body: data })
  },

  patchSubjectGoal(id, data) {
    return request('PATCH', `/subject-goals/${id}/`, { body: data })
  },

  patchBite(biteId, data) {
    return request('PATCH', `/bites/${biteId}/`, { body: data })
  },

  regenerateTopicBites(topicId) {
    return request('POST', `/topics/${topicId}/regenerate-bites/`)
  },

  // --- Sources / Explore ---

  getDocumentCategories() {
    return request('GET', '/document-categories/')
  },

  getDocumentCategory(id) {
    return request('GET', `/document-categories/${id}/`)
  },

  createDocumentCategory(data) {
    return request('POST', '/document-categories/', { body: data })
  },

  patchDocumentCategory(id, data) {
    return request('PATCH', `/document-categories/${id}/`, { body: data })
  },

  deleteDocumentCategory(id) {
    return request('DELETE', `/document-categories/${id}/`)
  },

  getCategoryDocuments(categoryId) {
    return request('GET', `/document-categories/${categoryId}/documents/`)
  },

  createCategoryDocument(categoryId, data) {
    return request('POST', `/document-categories/${categoryId}/documents/`, { body: data })
  },

  /** Upload a file for document indexing / chat retrieval (multipart). Pass a File or Blob. */
  uploadCategoryDocument(categoryId, file, originalName) {
    const fd = new FormData()
    fd.append('file', file, originalName || file.name)
    if (originalName) fd.append('original_name', originalName)
    return request('POST', `/document-categories/${categoryId}/documents/`, { body: fd })
  },

  patchSourceDocument(id, data) {
    return request('PATCH', `/source-documents/${id}/`, { body: data })
  },

  deleteSourceDocument(id) {
    return request('DELETE', `/source-documents/${id}/`)
  },

  getCategoryChatSessions(categoryId) {
    return request('GET', `/document-categories/${categoryId}/chat-sessions/`)
  },

  createCategoryChatSession(categoryId, data) {
    return request('POST', `/document-categories/${categoryId}/chat-sessions/`, { body: data })
  },

  patchChatSession(id, data) {
    return request('PATCH', `/chat-sessions/${id}/`, { body: data })
  },

  deleteChatSession(id) {
    return request('DELETE', `/chat-sessions/${id}/`)
  },

  getChatSessionMessages(sessionId) {
    return request('GET', `/chat-sessions/${sessionId}/messages/`)
  },

  createChatSessionMessage(sessionId, data) {
    return request('POST', `/chat-sessions/${sessionId}/messages/`, { body: data })
  },

  getResearchRuns() {
    return request('GET', '/research-runs/')
  },

  createResearchRun(data) {
    const signal =
      typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function'
        ? AbortSignal.timeout(180_000)
        : undefined
    return request('POST', '/research-runs/', { body: data, signal })
  },

  getResearchRun(id) {
    return request('GET', `/research-runs/${id}/`)
  },

  patchResearchRun(id, data) {
    return request('PATCH', `/research-runs/${id}/`, { body: data })
  },

  getMcpImports() {
    return request('GET', '/mcp-imports/')
  },

  createMcpImport(data) {
    return request('POST', '/mcp-imports/', { body: data })
  },

  getMcpImport(id) {
    return request('GET', `/mcp-imports/${id}/`)
  },

  patchMcpImport(id, data) {
    return request('PATCH', `/mcp-imports/${id}/`, { body: data })
  },

  getSourcePromotions() {
    return request('GET', '/source-promotions/')
  },

  promoteToSubject(data) {
    return request('POST', '/promotions/to-subject/', { body: data })
  },
}
