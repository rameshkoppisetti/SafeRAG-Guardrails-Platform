import { ShieldCheck } from 'lucide-react';

type HeaderProps = {
  health?: {
    status: string;
    vector_backend: string;
    indexed_chunks: number;
  };
};

export function Header({ health }: HeaderProps) {
  return (
    <header className="header">
      <div className="brand">
        <div className="brand-icon"><ShieldCheck size={22} /></div>
        <div>
          <h1>SafeRAG Guardrails</h1>
          <p>LangChain + Bedrock Guardrails + pgvector/Pinecone</p>
        </div>
      </div>
      <div className="health-card">
        <span className="status-dot" />
        <div>
          <strong>{health?.status ?? 'checking'}</strong>
          <p>{health?.vector_backend ?? 'unknown'} · {health?.indexed_chunks ?? 0} chunks</p>
        </div>
      </div>
    </header>
  );
}
