import type { ChatResponse, ChatStreamEvent, IngestResponse, Message, Session } from '../types/api';

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

  chatStream: async (
    payload: {
      tenant_id: string;
      user_id: string;
      roles: string[];
      session_id?: string;
      query: string;
    },
    onEvent: (event: ChatStreamEvent) => void,
  ) => {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    if (!response.body) {
      throw new Error('Streaming response body is unavailable');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() || '';
      for (const frame of frames) {
        const event = parseSseFrame(frame);
        if (event) onEvent(event);
      }
    }

    buffer += decoder.decode();
    if (buffer.trim()) {
      const event = parseSseFrame(buffer);
      if (event) onEvent(event);
    }
  },
};

function parseSseFrame(frame: string): ChatStreamEvent | undefined {
  let eventType = 'message';
  const dataLines: string[] = [];

  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) {
      eventType = line.slice('event:'.length).trim();
    }
    if (line.startsWith('data:')) {
      dataLines.push(line.slice('data:'.length).trimStart());
    }
  }

  if (!dataLines.length) return undefined;
  const data = JSON.parse(dataLines.join('\n')) as Record<string, unknown>;
  return { type: eventType, ...data } as ChatStreamEvent;
}
