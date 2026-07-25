import { useState, useEffect } from 'react';
import { fetchHistory } from '../api';
import DetailModal from './DetailModal';

const fmt = (iso) => new Date(iso).toLocaleDateString('en-US', {
  month: 'short', day: 'numeric', year: 'numeric',
  hour: '2-digit', minute: '2-digit',
});

export default function HistoryTab() {
  const [history,    setHistory]    = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    fetchHistory()
      .then(setHistory)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="card">
      <div className="loading-state">
        <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3, borderTopColor: 'var(--cyan)', borderColor: 'rgba(6,182,212,0.15)' }} />
        <p>Loading history…</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="card card-body">
      <div className="alert alert-error">{error}</div>
    </div>
  );

  if (history.length === 0) return (
    <div className="card">
      <div className="empty-state">
        <div className="empty-icon">📭</div>
        <h3>No analyses yet</h3>
        <p>Run your first analysis to see results here</p>
      </div>
    </div>
  );

  const total     = history.length;
  const normals   = history.filter(p => p.predicted_class === 'NORMAL').length;
  const positives = total - normals;
  const avgConf   = (history.reduce((s, p) => s + p.confidence, 0) / total * 100).toFixed(0);

  return (
    <>
      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{total}</div>
          <div className="stat-label">Total Analyses</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{normals}</div>
          <div className="stat-label">Normal</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{positives}</div>
          <div className="stat-label">Positive</div>
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-wrap">
          <table className="hist-table">
            <thead>
              <tr>
                <th>#</th>
                <th>File</th>
                <th>Result</th>
                <th>Confidence</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {history.map(item => (
                <tr key={item.id} onClick={() => setSelectedId(item.id)}>
                  <td style={{ color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                    {item.id}
                  </td>
                  <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {item.image_filename}
                  </td>
                  <td>
                    <span className={`badge ${item.predicted_class.toLowerCase()}`}>
                      {item.predicted_class}
                    </span>
                  </td>
                  <td>{(item.confidence * 100).toFixed(1)}%</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{fmt(item.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedId && (
        <DetailModal predictionId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </>
  );
}
