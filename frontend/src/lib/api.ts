export interface ApiErrorPayload {
  detail?: string;
  message?: string;
  error?: string;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getAuthToken(): string | null {
  return localStorage.getItem('authToken');
}

export function clearAuthStorage(): void {
  localStorage.removeItem('authToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('authUser');
  localStorage.removeItem('adminActiveConsole');
}

export async function logout(): Promise<boolean> {
  const refreshToken = localStorage.getItem('refreshToken');
  if (refreshToken) {
    try {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      // Ignore errors, still clear storage
    }
  }
  clearAuthStorage();
  return true;
}

interface RefreshPayload {
  access?: string;
  access_token?: string;
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = localStorage.getItem('refreshToken');
  if (!refresh) {
    return false;
  }
  try {
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!response.ok) {
      return false;
    }
    const payload = (await response.json()) as RefreshPayload;
    const access = payload.access ?? payload.access_token;
    if (!access) {
      return false;
    }
    localStorage.setItem('authToken', access);
    return true;
  } catch {
    return false;
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const buildHeaders = () => {
    const headers = new Headers(init.headers || {});
    if (!headers.has('Content-Type') && init.body && !(init.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }
    if (!headers.has('Accept')) {
      headers.set('Accept', 'application/json');
    }
    const token = getAuthToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  };

  const performFetch = async () =>
    fetch(path, {
      ...init,
      headers: buildHeaders(),
    });

  let response = await performFetch();

  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await performFetch();
    }
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as ApiErrorPayload;
      message = String(payload.detail || payload.message || payload.error || message);
    } catch {
      // Ignore JSON parse errors.
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
