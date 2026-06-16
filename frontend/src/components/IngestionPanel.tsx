import { useState } from 'react';
import { api } from '../api/client';

type IngestionPanelProps = {
  tenantId: string;
  roles: string[];
  onIngested: () => void;
};

export function IngestionPanel({ tenantId, roles, onIngested }: IngestionPanelProps) {
  const [documentId, setDocumentId] = useState('refund-policy-v1');
  const [text, setText] = useState('Refunds are processed within 7 business days. Contact support for refund status.');
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState(false);

  async function ingest() {
    setLoading(true);
    setResult('');
    try {
      const response = await api.ingestDocument({
        document_id: documentId,
        tenant_id: tenantId,
        acl: roles.length ? roles : ['__public__'],
        text,
      });
      setResult(`Indexed ${response.accepted_chunks} chunks, blocked ${response.blocked_chunks}.`);
      onIngested();
    } catch (error) {
      setResult(error instanceof Error ? error.message : 'Failed to ingest document');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel ingestion-panel">
      <h2>Ingest Document</h2>
      <label>
        Document ID
        <input value={documentId} onChange={(e) => setDocumentId(e.target.value)} />
      </label>
      <label>
        Document Text
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={8} />
      </label>
      <button onClick={ingest} disabled={loading || !documentId || !text}>
        {loading ? 'Indexing...' : 'Ingest safely'}
      </button>
      {result && <p className="result-text">{result}</p>}
    </section>
  );
}
