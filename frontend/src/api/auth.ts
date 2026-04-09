import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export const getToken = () => sessionStorage.getItem('access')
export const refreshToken = () => sessionStorage.getItem('refresh')

export const setTokens = (access: string, refresh: string) => {
  sessionStorage.setItem('access', access)
  sessionStorage.setItem('refresh', refresh)
}

export const clearTokens = () => {
  sessionStorage.removeItem('access')
  sessionStorage.removeItem('refresh')
}

export async function login(username: string, password: string) {
  const { data } = await axios.post(`${BASE_URL}/api/v1/auth/login/`, { username, password })
  setTokens(data.access, data.refresh)
  window.dispatchEvent(new Event('auth-change'))
}

export async function register(username: string, email: string, password: string) {
  const { data } = await axios.post(`${BASE_URL}/api/v1/auth/register/`, { username, email, password })
  setTokens(data.access, data.refresh)
  window.dispatchEvent(new Event('auth-change'))
}
