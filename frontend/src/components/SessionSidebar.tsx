import type { Session } from '../types/api';

type SessionSidebarProps = {
  sessions: Session[];
  activeSessionId?: string;
  onCreateSession: () => void;
  onSelectSession: (sessionId: string) => void;
};

export function SessionSidebar({ sessions, activeSessionId, onCreateSession, onSelectSession }: SessionSidebarProps) {
  return (
    <section className="panel session-panel">
      <div className="panel-title-row">
        <h2>Sessions</h2>
        <button className="secondary-button" onClick={onCreateSession}>New</button>
      </div>

      <div className="session-list">
        {sessions.length === 0 && <p className="empty">No sessions yet.</p>}
        {sessions.map((session) => (
          <button
            key={session.session_id}
            className={`session-item ${session.session_id === activeSessionId ? 'active' : ''}`}
            onClick={() => onSelectSession(session.session_id)}
          >
            <strong>{session.title || 'Untitled session'}</strong>
            <span>{session.message_count} messages</span>
            <small>{new Date(session.updated_at).toLocaleString()}</small>
          </button>
        ))}
      </div>
    </section>
  );
}
