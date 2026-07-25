import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { fetchPredictionDetail, getHeatmapUrl } from '../api';

function ProbBars({ probabilities }) {
  if (!probabilities) return null;
  const entries = Object.entries(probabilities).sort(([,a],[,b]) => b - a);
  return (
    <div className="prob-section">
      <div className="section-label">Class Probabilities</div>
      {entries.map(([cls, prob]) => {
        const key = cls.toLowerCase();
        return (
          <div className="prob-row" key={cls}>
            <span className={`prob-name ${key}`}>{cls}</span>
            <div className="prob-track">
              <div className={`prob-fill ${key}`} style={{ width: `${(prob*100).toFixed(1)}%` }} />
            </div>
            <span className={`prob-pct ${key}`}>{(prob*100).toFixed(1)}%</span>
          </div>
        );
      })}
    </div>
  );
}

export default function DetailModal({ predictionId, onClose }) {
  const [detail,  setDetail]  = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetchPredictionDetail(predictionId)
      .then(d => { if (!cancelled) setDetail(d); })
      .catch(e => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [predictionId]);

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const cls = detail?.predicted_class?.toLowerCase() ?? 'default';

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>

        <div className="modal-top">
          <h2>Prediction #{predictionId}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {loading && (
          <div className="loading-state">
            <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3, borderTopColor: 'var(--cyan)', borderColor: 'rgba(6,182,212,0.15)' }} />
            <p>Loading…</p>
          </div>
        )}

        {error && (
          <div className="card-body">
            <div className="alert alert-error">{error}</div>
          </div>
        )}

        {detail && !loading && (
          <div className="result-wrap">

            <div className="result-header">
              <span className={`class-badge ${cls}`}>
                {detail.predicted_class === 'NORMAL' ? '✓' : '⚠'} {detail.predicted_class}
              </span>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {(detail.confidence * 100).toFixed(1)}% confidence
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {detail.image_filename} · {new Date(detail.created_at).toLocaleString()}
                </div>
              </div>
            </div>

            <ProbBars probabilities={detail.probabilities} />

            {detail.heatmap_path && (
              <div className="heatmap-section">
                <div className="section-label">Grad-CAM Attention Map</div>
                <div className="heatmap-img">
                  <img src={getHeatmapUrl(detail.heatmap_path)} alt="Grad-CAM heatmap" />
                </div>
              </div>
            )}

            {detail.report_text && (
              <div className="report-section">
                <div className="section-label">AI Clinical Report</div>
                <div className="report-body">
                  <ReactMarkdown>{detail.report_text}</ReactMarkdown>
                </div>
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  );
}
