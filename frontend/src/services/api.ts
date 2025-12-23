import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type {
  AuthResponse,
  User,
  FileListResponse,
  PresignResponse,
  FileAsset,
  ChatResponse,
  Conversation,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add JWT token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token');
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
          hasToken: !!token,
          params: config.params,
        });
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        console.error('[API Request Error]', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
          status: response.status,
          data: response.data,
        });
        return response;
      },
      async (error) => {
        const originalRequest = error.config;
        console.error(`[API Error] ${originalRequest?.method?.toUpperCase()} ${originalRequest?.url}`, {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message,
        });

        // If 401 and not already retried, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
          console.log('[Auth] Token expired, attempting refresh...');
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              console.log('[Auth] Refreshing token...');
              const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
                refresh: refreshToken,
              });

              const { access } = response.data;
              localStorage.setItem('access_token', access);
              console.log('[Auth] Token refreshed successfully');

              // Retry original request with new token
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${access}`;
              }
              console.log('[Auth] Retrying original request...');
              return this.client(originalRequest);
            } else {
              console.warn('[Auth] No refresh token available');
            }
          } catch (refreshError: any) {
            console.error('[Auth] Token refresh failed:', refreshError);
            // Refresh failed, logout user
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            console.log('[Auth] Redirecting to login...');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async register(username: string, email: string, password: string, passwordConfirm: string): Promise<AuthResponse> {
    try {
      console.log('[Auth] Registering user:', { username, email });
      const response = await this.client.post('/auth/register/', {
        username,
        email,
        password,
        password_confirm: passwordConfirm,
      });
      console.log('[Auth] Registration successful');
      return response.data;
    } catch (error: any) {
      console.error('[Auth] Registration failed:', error.response?.data || error.message);
      throw error;
    }
  }

  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      console.log('[Auth] Logging in user:', username);
      const response = await this.client.post('/auth/login/', {
        username,
        password,
      });
      console.log('[Auth] Login successful');
      return response.data;
    } catch (error: any) {
      console.error('[Auth] Login failed:', error.response?.data || error.message);
      throw error;
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get('/auth/me/');
    return response.data;
  }

  // File endpoints
  async listFiles(page: number = 1, pageSize: number = 20): Promise<FileListResponse> {
    const response = await this.client.get('/files/', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async presignUpload(filename: string, fileType: string, size: number): Promise<PresignResponse> {
    try {
      console.log('[File Upload] Requesting presigned URL:', { filename, fileType, size });
      const response = await this.client.post('/files/presign/', {
        filename,
        file_type: fileType,
        size,
      });
      console.log('[File Upload] Presigned URL received');
      return response.data;
    } catch (error: any) {
      console.error('[File Upload] Presign failed:', error.response?.data || error.message);
      throw error;
    }
  }

  async finalizeUpload(s3Key: string, filename: string, fileType: string, size: number): Promise<FileAsset> {
    try {
      console.log('[File Upload] Finalizing upload:', { filename, s3Key });
      const response = await this.client.post('/files/finalize/', {
        s3_key: s3Key,
        filename,
        file_type: fileType,
        size,
      });
      console.log('[File Upload] Upload finalized:', {
        fileId: response.data.id,
        status: response.data.status,
      });
      return response.data;
    } catch (error: any) {
      console.error('[File Upload] Finalize failed:', error.response?.data || error.message);
      throw error;
    }
  }

  async deleteFile(fileId: number): Promise<void> {
    await this.client.delete(`/files/${fileId}/`);
  }

  async updateFile(fileId: number, payload: Partial<Pick<FileAsset, 'filename' | 'metadata'>>): Promise<FileAsset> {
    const response = await this.client.patch(`/files/${fileId}/update/`, payload);
    return response.data;
  }

  async retryFinalize(fileId: number): Promise<void> {
    await this.client.post(`/files/${fileId}/retry-finalize/`);
  }

  // Chat endpoints
  async sendMessage(
    message: string,
    conversationId?: number,
    fileIds?: number[]
  ): Promise<ChatResponse> {
    try {
      console.log('[Chat] Sending message:', {
        message: message.substring(0, 50) + '...',
        conversationId,
        fileIds,
      });
      const response = await this.client.post('/chat/', {
        message,
        conversation_id: conversationId,
        file_ids: fileIds || [],
      });
      console.log('[Chat] Message sent successfully:', {
        conversationId: response.data.conversation_id,
        hasCitations: response.data.citations?.length > 0,
      });
      return response.data;
    } catch (error: any) {
      console.error('[Chat] Send message failed:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
      });
      throw error;
    }
  }

  async getConversationHistory(conversationId: number): Promise<Conversation> {
    const response = await this.client.get(`/chat/history/${conversationId}/`);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await this.client.get('/health/');
    return response.data;
  }
}

export const apiClient = new ApiClient();

