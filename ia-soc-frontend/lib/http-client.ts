const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8787').replace(/\/+$/, '');

function buildUrl(endpoint: string): string {
  return `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
}

function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('ia_soc_auth_token') || process.env.NEXT_PUBLIC_API_AUTH_TOKEN || null;
}

interface RequestOptions extends RequestInit {
  retries?: number;
  retryDelay?: number;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errorBody = await response.json();
      if (errorBody && (errorBody.message || errorBody.error)) {
        errorMessage = errorBody.message || errorBody.error;
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

export const httpClient = {
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = buildUrl(endpoint);
    const retries = options?.retries ?? 2;
    const retryDelay = options?.retryDelay ?? 1000;

    let lastError: any;
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const res = await fetch(url, { ...options, method: 'GET', headers });
        return await handleResponse<T>(res);
      } catch (err) {
        lastError = err;
        if (attempt < retries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(2, attempt)));
        }
      }
    }
    throw lastError || new Error(`Network request failed for GET ${endpoint}`);
  },

  async post<T>(endpoint: string, body?: any, options?: RequestOptions): Promise<T> {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = buildUrl(endpoint);
    const res = await fetch(url, {
      ...options,
      method: 'POST',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
  },

  async put<T>(endpoint: string, body?: any, options?: RequestOptions): Promise<T> {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = buildUrl(endpoint);
    const res = await fetch(url, {
      ...options,
      method: 'PUT',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
  },

  async patch<T>(endpoint: string, body?: any, options?: RequestOptions): Promise<T> {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = buildUrl(endpoint);
    const res = await fetch(url, {
      ...options,
      method: 'PATCH',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
  },

  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = buildUrl(endpoint);
    const res = await fetch(url, { ...options, method: 'DELETE', headers });
    return handleResponse<T>(res);
  },

  /**
   * Stream agent chat response via Server-Sent Events (SSE)
   */
  async streamChat(
    endpoint: string,
    body: any,
    onMessage: (eventData: any) => void,
    onError?: (error: any) => void,
    onComplete?: () => void
  ): Promise<void> {
    const token = getAuthToken();
    const url = buildUrl(endpoint);

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(body)
      });

      if (!res.ok || !res.body) {
        throw new Error(`Failed to establish SSE stream: ${res.statusText}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            const jsonStr = trimmed.replace('data:', '').trim();
            if (jsonStr === '[DONE]') {
              onComplete?.();
              return;
            }
            try {
              const parsed = JSON.parse(jsonStr);
              onMessage(parsed);
            } catch {
              // ignore non-json SSE comments
            }
          }
        }
      }
      onComplete?.();
    } catch (err) {
      onError?.(err);
    }
  }
};
