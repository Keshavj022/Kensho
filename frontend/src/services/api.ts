/**
 * API Service - Centralized API client with error handling
 */
import { API_CONFIG, getApiUrl, API_ENDPOINTS } from '../config/api'

export interface ApiError {
  message: string
  status?: number
  detail?: string
}

class ApiService {
  private getAuthToken(): string | null {
    return localStorage.getItem('auth_token')
  }

  private getHeaders(customHeaders?: Record<string, string>): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...customHeaders,
    }

    const token = this.getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return headers
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`
      let errorDetail: string | undefined

      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
        errorDetail = errorData.detail
      } catch {
        // If response is not JSON, use status text
        errorMessage = response.statusText || errorMessage
      }

      const error: ApiError = {
        message: errorMessage,
        status: response.status,
        detail: errorDetail,
      }

      // Handle authentication errors
      if (response.status === 401) {
        // Clear invalid token
        localStorage.removeItem('auth_token')
        // Could redirect to login here
      }

      throw error
    }

    // Handle empty responses
    const contentType = response.headers.get('content-type')
    if (!contentType || !contentType.includes('application/json')) {
      return {} as T
    }

    return response.json()
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    let url = getApiUrl(endpoint)

    if (params) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
      url += `?${searchParams.toString()}`
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT)

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: this.getHeaders(),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)
      return this.handleResponse<T>(response)
    } catch (error) {
      clearTimeout(timeoutId)
      if (error instanceof Error && error.name === 'AbortError') {
        throw { message: 'Request timeout', status: 408 } as ApiError
      }
      throw error
    }
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT)

    try {
      const response = await fetch(getApiUrl(endpoint), {
        method: 'POST',
        headers: this.getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)
      return this.handleResponse<T>(response)
    } catch (error) {
      clearTimeout(timeoutId)
      if (error instanceof Error && error.name === 'AbortError') {
        throw { message: 'Request timeout', status: 408 } as ApiError
      }
      throw error
    }
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT)

    try {
      const response = await fetch(getApiUrl(endpoint), {
        method: 'PUT',
        headers: this.getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)
      return this.handleResponse<T>(response)
    } catch (error) {
      clearTimeout(timeoutId)
      if (error instanceof Error && error.name === 'AbortError') {
        throw { message: 'Request timeout', status: 408 } as ApiError
      }
      throw error
    }
  }

  async delete<T>(endpoint: string): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT)

    try {
      const response = await fetch(getApiUrl(endpoint), {
        method: 'DELETE',
        headers: this.getHeaders(),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)
      return this.handleResponse<T>(response)
    } catch (error) {
      clearTimeout(timeoutId)
      if (error instanceof Error && error.name === 'AbortError') {
        throw { message: 'Request timeout', status: 408 } as ApiError
      }
      throw error
    }
  }
}

export const apiService = new ApiService()
