import type { ChatResponse, IngestResponse, Message, Session } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // ignore JSON parsing failures
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; vector_backend: string; indexed_chunks: number }>('/health'),

  createSession: (payload: { tenant_id: string; user_id: string; title?: string }) =>
    request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listSessions: (tenantId: string, userId: string) =>
    request<Session[]>(`/sessions?tenant_id=${encodeURIComponent(tenantId)}&user_id=${encodeURIComponent(userId)}`),

  getMessages: (sessionId: string, limit = 50) =>
    request<Message[]>(`/sessions/${sessionId}/messages?limit=${limit}`),

  ingestDocument: (payload: { document_id: string; tenant_id: string; acl: string[]; text: string }) =>
    request<IngestResponse>('/documents/ingest', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  chat: (payload: {
    tenant_id: string;
    user_id: string;
    roles: string[];
    session_id?: string;
    query: string;
  }) =>
    request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
