import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://49.235.106.26:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  
  register: (data: { username: string; email: string; password: string }) =>
    api.post('/register', data),
  
  getMe: () => api.get('/me'),
  
  updateMe: (data: { username?: string; email?: string; preferences?: object }) =>
    api.put('/me', data),
}

export const thoughtsAPI = {
  list: (params?: {
    skip?: number
    limit?: number
    category?: string
    is_favorite?: boolean
    is_archived?: boolean
    start_date?: string
    end_date?: string
    search?: string
  }) => api.get('/thoughts', { params }),
  
  get: (id: number) => api.get(`/thoughts/${id}`),
  
  create: (data: {
    content: string
    category?: string
    title?: string
    tags?: string[]
    source?: string
  }) => api.post('/thoughts', data),
  
  update: (id: number, data: {
    content?: string
    category?: string
    title?: string
    tags?: string[]
    is_favorite?: boolean
    is_archived?: boolean
  }) => api.put(`/thoughts/${id}`, data),
  
  delete: (id: number) => api.delete(`/thoughts/${id}`),
  
  expand: (id: number, expansionTypes: string[]) =>
    api.post(`/thoughts/${id}/expand`, { expansion_types: expansionTypes }),
  
  toggleFavorite: (id: number) => api.post(`/thoughts/${id}/favorite`),
  
  toggleArchive: (id: number) => api.post(`/thoughts/${id}/archive`),
}

export const categoriesAPI = {
  list: (parentId?: number) => api.get('/categories', { params: { parent_id: parentId } }),
  create: (data: { name: string; color?: string; icon?: string; parent_id?: number }) =>
    api.post('/categories', data),
  update: (id: number, data: { name?: string; color?: string; icon?: string }) =>
    api.put(`/categories/${id}`, data),
  delete: (id: number) => api.delete(`/categories/${id}`),
}

export const analyticsAPI = {
  get: (startDate?: string, endDate?: string) =>
    api.get('/analytics', { params: { start_date: startDate, end_date: endDate } }),
}

export const reviewAPI = {
  getConfigs: () => api.get('/review/configs'),
  createConfig: (data: {
    period: string
    day_of_week?: number
    day_of_month?: number
    hour?: number
    minute?: number
  }) => api.post('/review/configs', data),
  updateConfig: (id: number, data: object) => api.put(`/review/configs/${id}`, data),
  deleteConfig: (id: number) => api.delete(`/review/configs/${id}`),
  getSummaries: (period?: string, limit?: number) =>
    api.get('/review/summaries', { params: { period, limit } }),
  generate: (period: string, forceRegenerate?: boolean) =>
    api.post('/review/generate', { period, force_regenerate: forceRegenerate }),
}

export const exportAPI = {
  thoughts: (params: {
    format: 'markdown' | 'json' | 'pdf'
    start_date?: string
    end_date?: string
    category?: string
    include_expansions?: boolean
  }) => api.get('/export/thoughts', { params, responseType: 'blob' }),
  
  summaries: (format: 'markdown' | 'json') =>
    api.get('/export/summaries', { params: { format }, responseType: 'blob' }),
}

export const insightsAPI = {
  list: (insightType?: string, limit?: number) =>
    api.get('/insights', { params: { insight_type: insightType, limit } }),
  createFeedback: (data: {
    feedback_type: string
    target_id: number
    target_type: string
    rating: number
    comment?: string
  }) => api.post('/insights/feedback', data),
}

export default api
