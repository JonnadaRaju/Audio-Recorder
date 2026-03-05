const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface Recording {
  id: number;
  user_id: number;
  filename: string;
  file_size: number;
  duration: number | null;
  created_at: string;
}

export interface RecordingListItem {
  id: number;
  filename: string;
  file_size: number;
  duration: number | null;
  created_at: string;
}

export interface VideoRecording {
  id: number;
  user_id: number;
  filename: string;
  file_size: number;
  duration: number | null;
  transcript: string | null;
  summary: string | null;
  created_at: string;
}

export interface VideoListItem {
  id: number;
  filename: string;
  file_size: number;
  duration: number | null;
  transcript: string | null;
  summary: string | null;
  created_at: string;
}

export interface AgentStep {
  step: string;
  tool: string;
  input: Record<string, unknown>;
  output_preview: string;
}

export interface AgentQueryResponse {
  query: string;
  answer: string;
  steps: AgentStep[];
}

class ApiService {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  private async requestRaw(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const headers: HeadersInit = {
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    if (options.body && !(options.body instanceof FormData)) {
      (headers as Record<string, string>)['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return response;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await this.requestRaw(endpoint, options);

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  async register(email: string, password: string): Promise<User> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    return this.request<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async uploadRecording(file: File, duration?: number): Promise<Recording> {
    const formData = new FormData();
    formData.append('file', file);
    if (duration !== undefined) {
      formData.append('duration', duration.toString());
    }

    return this.request<Recording>('/recordings/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async getRecordings(): Promise<RecordingListItem[]> {
    return this.request<RecordingListItem[]>('/recordings', {
      method: 'GET',
    });
  }

  async getRecording(id: number): Promise<Recording> {
    return this.request<Recording>(`/recordings/${id}`, {
      method: 'GET',
    });
  }

  async deleteRecording(id: number): Promise<void> {
    return this.request<void>(`/recordings/${id}`, {
      method: 'DELETE',
    });
  }

  async getRecordingAudioUrl(id: number): Promise<string> {
    const response = await this.requestRaw(`/recordings/${id}/stream`, {
      method: 'GET',
    });
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  }

  async uploadVideo(file: File, duration?: number): Promise<VideoRecording> {
    const formData = new FormData();
    formData.append('file', file);
    if (duration !== undefined) {
      formData.append('duration', duration.toString());
    }

    return this.request<VideoRecording>('/videos/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async getVideos(): Promise<VideoListItem[]> {
    return this.request<VideoListItem[]>('/videos', {
      method: 'GET',
    });
  }

  async getVideo(id: number): Promise<VideoRecording> {
    return this.request<VideoRecording>(`/videos/${id}`, {
      method: 'GET',
    });
  }

  async deleteVideo(id: number): Promise<void> {
    return this.request<void>(`/videos/${id}`, {
      method: 'DELETE',
    });
  }

  async getVideoStreamUrl(id: number): Promise<string> {
    const response = await this.requestRaw(`/videos/${id}/stream`, {
      method: 'GET',
    });
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  }

  async askAgent(query: string): Promise<AgentQueryResponse> {
    return this.request<AgentQueryResponse>('/agent/query', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }
}

export const apiService = new ApiService();
