import axios from 'axios'
import { getToken, refreshToken, setTokens, clearTokens } from './auth'

const client = axios.create({ baseURL: '/api/v1' })

client.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refresh = refreshToken()
        if (!refresh) throw new Error('no refresh token')
        const { data } = await axios.post('/api/v1/auth/token/refresh/', { refresh })
        setTokens(data.access, refresh)
        original.headers.Authorization = `Bearer ${data.access}`
        return client(original)
      } catch {
        clearTokens()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default client
