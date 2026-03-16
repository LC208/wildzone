import axios from 'axios'

export const getToken = () => localStorage.getItem('access')
export const refreshToken = () => localStorage.getItem('refresh')
export const setTokens = (access: string, refresh: string) => {
  localStorage.setItem('access', access)
  localStorage.setItem('refresh', refresh)
}
export const clearTokens = () => {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
}

export async function login(username: string, password: string) {
  const { data } = await axios.post('/api/v1/auth/login/', { username, password })
  setTokens(data.access, data.refresh)
}

export async function register(username: string, email: string, password: string) {
  const { data } = await axios.post('/api/v1/auth/register/', { username, email, password })
  setTokens(data.access, data.refresh)
}
