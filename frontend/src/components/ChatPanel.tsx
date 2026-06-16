import { FormEvent, useEffect, useRef, useState } from 'react';
import { Send } from 'lucide-react';
import { api } from '../api/client';
import type { Citation, Message } from '../types/api';

type UiMessage = Message & { citations?: Citation[] };

type ChatPanelProps = {
  tenantId: string;
  userId: string;
  roles: string[];
  sessionId?: string;
  onSessionResolved: (sessionId: string) => void;
  refreshSessions: () => void;
};

export function ChatPanel({ tenantId, userId, roles, sessionId, onSessionResolved, refreshSessions }: ChatPanelProps) {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [query, setQuery] = useState('How long do refunds take?');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    async function loadMessages() {
      if (!sessionId) {
        setMessages([]);
        return;
      }
      const history = await api.getMessages(sessionId, 50);
      setMessages(history);
    }
    loadMessages().catch(() => setMessages([]));
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;

    setLoading(true);
    setMessages((current) => [
      ...current,
      { role: 'user', content: trimmed, created_at: new Date().toISOString() },
    ]);
    setQuery('');

    try {
      const response = await api.chat({
        tenant_id: tenantId,
        user_id: userId,
        roles,
        session_id: sessionId,
        query: trimmed,
      });
      onSessionResolved(response.session_id);
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: response.answer,
          citations: response.citations,
          created_at: new Date().toISOString(),
        },
      ]);
      refreshSessions();
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: error instanceof Error ? error.message : 'Chat request failed',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel chat-panel">
      <div className="panel-title-row">
        <h2>Chat</h2>
        <span className="session-chip">{sessionId ? `Session ${sessionId.slice(0, 8)}` : 'New session'}</span>
      </div>

      <div className="messages">
        {messages.length === 0 && (
          <div className="empty-chat">
            <strong>No messages yet.</strong>
            <p>Ask a question after indexing a document.</p>
          </div>
        )}
        {messages.map((message, index) => (
          <article key={`${message.created_at}-${index}`} className={`message ${message.role}`}>
            <div className="message-role">{message.role}</div>
            <p>{message.content}</p>
            {message.citations && message.citations.length > 0 && (
              <div className="citations">
                <strong>Citations</strong>
                {message.citations.map((citation) => (
                  <div key={citation.chunk_id} className="citation">
                    <span>{citation.document_id}</span>
                    <small>{citation.chunk_id}</small>
                    <small>score {citation.score.toFixed(3)}</small>
                  </div>
                ))}
              </div>
            )}
          </article>
        ))}
        <div ref={bottomRef} />
      </div>

      <form className="chat-form" onSubmit={submit}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about indexed documents..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          <Send size={18} />
        </button>
      </form>
    </section>
  );
}
