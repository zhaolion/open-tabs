import { API_BASE_URL } from '@shared/constants/api'
import { useAuthStore } from '@shared/stores/auth-store'

interface RequestOptions {
  requiresAuth?: boolean
}

class ApiError extends Error {
  constructor(
    public status: number,
    public data: unknown
  ) {
    super(`API Error: ${status}`)
    this.name = 'ApiError'
  }
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: unknown,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const headers = new Headers({
      'Content-Type': 'application/json',
    })

    // Add auth header if required
    if (options.requiresAuth) {
      const { access_token, isTokenExpired } = useAuthStore.getState()

      if (!access_token || isTokenExpired()) {
        throw new ApiError(401, { message: 'Not authenticated' })
      }

      headers.set('Authorization', `Bearer ${access_token}`)
    }

    const response = await fetch(url, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(response.status, errorData)
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T
    }

    return response.json()
  }

  get<T>(endpoint: string, options?: RequestOptions) {
    return this.request<T>('GET', endpoint, undefined, options)
  }

  post<T>(endpoint: string, data: unknown, options?: RequestOptions) {
    return this.request<T>('POST', endpoint, data, options)
  }

  put<T>(endpoint: string, data: unknown, options?: RequestOptions) {
    return this.request<T>('PUT', endpoint, data, options)
  }

  patch<T>(endpoint: string, data: unknown, options?: RequestOptions) {
    return this.request<T>('PATCH', endpoint, data, options)
  }

  delete<T>(endpoint: string, options?: RequestOptions) {
    return this.request<T>('DELETE', endpoint, undefined, options)
  }
}

export const apiClient = new ApiClient()
export { ApiError }
