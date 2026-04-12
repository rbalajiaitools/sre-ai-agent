/**
 * Authentication API functions
 */
import { api } from './client';
import { LoginCredentials, LoginResponse, User } from '@/types';

/**
 * Login with email and password
 */
export const loginWithCredentials = async (
  email: string,
  password: string
): Promise<LoginResponse> => {
  // Note: Adjust endpoint based on your backend auth implementation
  const response = await api.post<LoginResponse>('/auth/login', {
    email,
    password,
  });
  return response;
};

/**
 * Logout user
 */
export const logout = async (): Promise<void> => {
  // Optional: Call backend logout endpoint if needed
  // await api.post('/auth/logout');
  return Promise.resolve();
};

/**
 * Get current user profile
 */
export const getMe = async (): Promise<User> => {
  const response = await api.get<User>('/auth/me');
  return response;
};

/**
 * Refresh auth token
 */
export const refreshToken = async (token: string): Promise<{ token: string }> => {
  const response = await api.post<{ token: string }>('/auth/refresh', { token });
  return response;
};
