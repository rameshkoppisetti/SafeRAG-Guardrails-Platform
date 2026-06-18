export type Citation = {
  document_id: string;
  chunk_id: string;
  score: number;
};

export type ChatResponse = {
  session_id: string;
  answer: string;
  citations: Citation[];
};

export type ChatStreamEvent =
  | { type: 'session'; session_id: string }
  | { type: 'delta'; text: string }
  | { type: 'citations'; citations: Citation[] }
  | { type: 'done' }
  | { type: 'error'; detail: string };

export type Session = {
  session_id: string;
  tenant_id: string;
  user_id: string;
  title?: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type Message = {
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
};

export type IngestResponse = {
  document_id: string;
  accepted_chunks: number;
  blocked_chunks: number;
};
