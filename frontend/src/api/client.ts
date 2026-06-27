import axios from 'axios'

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 60000
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sales_ai_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use((response) => {
  const body = response.data as ApiResponse<unknown>
  if (body.code !== 0) {
    return Promise.reject(new Error(body.message || '请求失败'))
  }
  return response
})

export async function getData<T>(url: string, params?: Record<string, string>) {
  const response = await api.get<ApiResponse<T>>(url, { params })
  return response.data.data
}

export async function postData<T>(url: string, data?: unknown) {
  const response = await api.post<ApiResponse<T>>(url, data)
  return response.data.data
}

export async function postFormData<T>(url: string, data: FormData) {
  const response = await api.post<ApiResponse<T>>(url, data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data.data
}
