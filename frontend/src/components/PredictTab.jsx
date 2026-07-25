import { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { predictImage, getHeatmapUrl } from '../api';

const MODULE_LABELS = {
  chest_xray_pneumonia: { title: 'Chest X-Ray',   hint: 'X-Ray · Lungs'      },
  brain_tumor:          { title: 'Brain MRI',      hint: 'MRI · Brain'        },
  skin_cancer:          { title: 'Skin Dermoscopy', hint: 'Dermoscopy · Skin' },
};

// Probability bars — one per class
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

export default function PredictTab({ apiOnline, modelId, onModelChange }) {
  const [file,      setFile]      = useState(null);
  const [preview,   setPreview]   = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [result,    setResult]    = useState(null);
  const [error,     setError]     = useState(null);
  const [rejection, setRejection] = useState(null);
  const [dragOver,  setDragOver]  = useState(false);
  const inputRef = useRef();

  // Clear results when module changes
  const prevModelId = useRef(modelId);
  if (prevModelId.current !== modelId) {
    prevModelId.current = modelId;
  }

  const reset = () => {
    setFile(null); setPreview(null);
    setResult(null); setError(null); setRejection(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleFile = (f) => {
    if (!f) return;
    reset();
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f?.type.startsWith('image/')) handleFile(f);
  };

  const analyze = async () => {
    if (!file || !apiOnline) return;
    setLoading(true); setError(null); setRejection(null);
    try {
      setResult(await predictImage(file, modelId));
    } catch (err) {
      if (err.isRejection) setRejection({ message: err.message, hint: err.hint });
      else setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const cls = result?.predicted_class?.toLowerCase() ?? 'default';

  return (
    <div className="predict-tab-container">
      {/* Hero Image */}
      <div className="hero-banner" style={{ marginTop: '1rem', marginBottom: '2.5rem', borderRadius: 'var(--r-lg)', overflow: 'hidden', height: '180px', border: '1px solid var(--border)' }}>
        <img src="/hero_banner.png" alt="AI Medical Analysis" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </div>

      <div className="predict-grid">
        {/* ── Upload Panel ── */}
        <div className="card">
          <div className="card-header" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div className="card-header-icon">📤</div>
              <span className="card-title">Upload Image for Analysis</span>
            </div>
            
            <div style={{ width: '100%' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Select Scan Type
              </label>
              <select 
                value={modelId} 
                onChange={(e) => {
                  onModelChange(e.target.value);
                  reset();
                }}
                style={{
                  width: '100%',
                  padding: '0.65rem 0.8rem',
                  borderRadius: 'var(--r-md)',
                  border: '1px solid var(--border)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontFamily: 'inherit',
                  fontSize: '0.9rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="chest_xray_pneumonia">Chest X-Ray (Lungs)</option>
                <option value="brain_tumor">Brain MRI (Tumor)</option>
                <option value="skin_cancer">Skin Dermoscopy (Cancer)</option>
              </select>
            </div>
          </div>
        <div className="card-body">
          {!preview ? (
            <div
              className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
            >
              <input
                ref={inputRef}
                type="file"
                accept="image/png,image/jpeg,image/bmp,image/tiff"
                onChange={(e) => handleFile(e.target.files[0])}
              />
              <div className="upload-icon">🩻</div>
              <h3>Drop image or click to browse</h3>
              <p>PNG · JPEG · BMP · TIFF</p>
            </div>
          ) : (
            <>
              <div className="preview-wrap">
                <img src={preview} alt="Medical scan" />
                <button className="preview-remove" onClick={reset}>✕</button>
              </div>
              <button
                className="btn btn-primary"
                disabled={loading || !apiOnline}
                onClick={analyze}
              >
                {loading
                  ? <><span className="spinner" /> Analyzing...</>
                  : 'Run Analysis'}
              </button>
            </>
          )}

          {!apiOnline && apiOnline !== null && (
            <div className="alert alert-error" style={{ marginTop: '1rem' }}>
              Backend offline — start the API server first.
            </div>
          )}
        </div>
      </div>

      {/* ── Results Panel ── */}
      <div className="card">
        <div className="card-header">
          <div className="card-header-icon">📊</div>
          <span className="card-title">Analysis Results</span>
          {result && (
            <span className={`badge ${cls}`} style={{ marginLeft: 'auto' }}>
              {result.predicted_class}
            </span>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="loading-state">
            <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3, borderTopColor: 'var(--cyan)', borderColor: 'rgba(6,182,212,0.15)' }} />
            <p>Running AI analysis pipeline…</p>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="card-body">
            <div className="alert alert-error">{error}</div>
          </div>
        )}

        {/* Rejection */}
        {rejection && !loading && (
          <div className="rejection-card">
            <div className="rejection-icon">🚫</div>
            <h3>Invalid Medical Image</h3>
            <p>{rejection.message}</p>
            {rejection.hint && <p style={{ marginTop: '0.5rem' }}>{rejection.hint}</p>}
            <button className="btn btn-ghost" onClick={reset} style={{ marginTop: '1rem', width: 'auto', margin: '1rem auto 0' }}>
              Try another image
            </button>
          </div>
        )}

        {/* Empty */}
        {!loading && !result && !error && !rejection && (
          <div className="empty-state">
            <div className="empty-icon">🩺</div>
            <h3>No results yet</h3>
            <p>Upload an image and run analysis</p>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="result-wrap">

            {/* Classification */}
            <div className="result-header">
              <span className={`class-badge ${cls}`}>
                {result.predicted_class === 'NORMAL' ? '✓' : '⚠'} {result.predicted_class}
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {(result.confidence * 100).toFixed(1)}% confidence
              </span>
            </div>

            {/* Probabilities */}
            <ProbBars probabilities={result.probabilities} />

            {/* Heatmap */}
            {result.heatmap_path && (
              <div className="heatmap-section">
                <div className="section-label">Grad-CAM Attention Map</div>
                <div className="heatmap-img">
                  <img src={getHeatmapUrl(result.heatmap_path)} alt="Grad-CAM heatmap" />
                </div>
              </div>
            )}

            {/* Report */}
            {result.report_text && (
              <div className="report-section">
                <div className="section-label">AI Clinical Report</div>
                <div className="report-body">
                  <ReactMarkdown>{result.report_text}</ReactMarkdown>
                </div>
              </div>
            )}

          </div>
        )}
      </div>
    </div>
    </div>
  );
}
