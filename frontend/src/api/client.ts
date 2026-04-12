/**
 * Axios API client with interceptors for auth and error handling
 */
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiError } from '@/types';

// Custom ApiError class
export class ApiErrorClass extends Error implements ApiError {
  status: number;
  code: string;
  details?: Record<string, unknown>;

  constructor(message: string, status: number, code: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - attach auth token
apiClient.interceptors.request.use(
  (config) => {
    // Get token from localStorage (Zustand persist)
    const authStore = localStorage.getItem('auth-storage');
    if (authStore) {
      try {
        const { state } = JSON.parse(authStore);
        if (state?.token) {
          config.headers.Authorization = `Bearer ${state.token}`;
        }
      } catch (error) {
        console.error('Failed to parse auth storage:', error);
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError<{ message?: string; error_code?: string; details?: Record<string, unknown> }>) => {
    // Handle 401 - Unauthorized
    if (error.response?.status === 401) {
      // Clear auth store
      localStorage.removeItem('auth-storage');
      // Redirect to login
      window.location.href = '/login';
      return Promise.reject(
        new ApiErrorClass('Unauthorized', 401, 'UNAUTHORIZED', {
          message: 'Your session has expired. Please login again.',
        })
      );
    }

    // Handle 5xx - Server errors
    if (error.response?.status && error.response.status >= 500) {
      const errorData = error.response.data;
      return Promise.reject(
        new ApiErrorClass(
          errorData?.message || 'Internal server error',
          error.response.status,
          errorData?.error_code || 'SERVER_ERROR',
          errorData?.details
        )
      );
    }

    // Handle 4xx - Client errors
    if (error.response?.status && error.response.status >= 400) {
      const errorData = error.response.data;
      return Promise.reject(
        new ApiErrorClass(
          errorData?.message || 'Request failed',
          error.response.status,
          errorData?.error_code || 'CLIENT_ERROR',
          errorData?.details
        )
      );
    }

    // Handle network errors
    if (error.message === 'Network Error') {
      return Promise.reject(
        new ApiErrorClass(
          'Network error. Please check your connection.',
          0,
          'NETWORK_ERROR'
        )
      );
    }

    // Handle timeout
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(
        new ApiErrorClass('Request timeout. Please try again.', 0, 'TIMEOUT')
      );
    }

    // Generic error
    return Promise.reject(
      new ApiErrorClass(
        error.message || 'An unexpected error occurred',
        0,
        'UNKNOWN_ERROR'
      )
    );
  }
);

// Typed API wrapper functions
export const api = {
  get: async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.get<T>(url, config);
    return response.data;
  },

  post: async <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.post<T>(url, data, config);
    return response.data;
  },

  put: async <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.put<T>(url, data, config);
    return response.data;
  },

  patch: async <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.patch<T>(url, data, config);
    return response.data;
  },

  delete: async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.delete<T>(url, config);
    return response.data;
  },
};

export default apiClient;
