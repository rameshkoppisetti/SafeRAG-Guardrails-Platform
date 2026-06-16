import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from './api/client';
import { Header } from './components/Header';
import { IdentityPanel } from './components/IdentityPanel';
import { SessionSidebar } from './components/SessionSidebar';
import { IngestionPanel } from './components/IngestionPanel';
import { ChatPanel } from './components/ChatPanel';
import type { Session } from './types/api';
import './styles/app.css';

export default function App() {
  const [tenantId, setTenantId] = useState('tenant_123');
  const [userId, setUserId] = useState('user_1');
  const [rolesText, setRolesText] = useState('support,employee');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>();
  const [health, setHealth] = useState<{ status: string; vector_backend: string; indexed_chunks: number }>();

  const roles = useMemo(
    () => rolesText.split(',').map((role) => role.trim()).filter(Boolean),
    [rolesText],
  );

  const refreshHealth = useCallback(async () => {
    try {
      setHealth(await api.health());
    } catch {
      setHealth(undefined);
    }
  }, []);

  const refreshSessions = useCallback(async () => {
    if (!tenantId || !userId) return;
    try {
      const result = await api.listSessions(tenantId, userId);
      setSessions(result);
    } catch {
      setSessions([]);
    }
  }, [tenantId, userId]);

  useEffect(() => {
    refreshHealth();
  }, [refreshHealth]);

  useEffect(() => {
    refreshSessions();
    setActiveSessionId(undefined);
  }, [tenantId, userId, refreshSessions]);

  async function createSession() {
    const session = await api.createSession({
      tenant_id: tenantId,
      user_id: userId,
      title: `Session ${new Date().toLocaleString()}`,
    });
    setActiveSessionId(session.session_id);
    await refreshSessions();
  }

  return (
    <div className="app-shell">
      <Header health={health} />

      <main className="main-grid">
        <aside className="left-column">
          <IdentityPanel
            tenantId={tenantId}
            userId={userId}
            roles={rolesText}
            onTenantIdChange={setTenantId}
            onUserIdChange={setUserId}
            onRolesChange={setRolesText}
          />
          <SessionSidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            onCreateSession={createSession}
            onSelectSession={setActiveSessionId}
          />
        </aside>

        <ChatPanel
          tenantId={tenantId}
          userId={userId}
          roles={roles}
          sessionId={activeSessionId}
          onSessionResolved={setActiveSessionId}
          refreshSessions={refreshSessions}
        />

        <aside className="right-column">
          <IngestionPanel tenantId={tenantId} roles={roles} onIngested={refreshHealth} />
        </aside>
      </main>
    </div>
  );
}
