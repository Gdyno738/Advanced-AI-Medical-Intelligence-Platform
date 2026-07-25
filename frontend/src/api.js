/**
 * API service — all backend communication goes through here.
 * Base URL is configurable via VITE_API_BASE_URL (defaults to localhost:8000).
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/** Check if the backend API is reachable. Returns full health payload or false. */
export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) return false;
    return res.json();   // returns { status, active_model }
  } catch {
    return false;
  }
}

/** Fetch the full model registry (all registered analysis modules). */
export async function fetchModels() {
  try {
    const res = await fetch(`${API_BASE}/models`, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

/**
 * Upload a medical image and run the full prediction pipeline.
 * @param {File} file
 * @returns {Promise<Object>} Prediction result with probabilities, heatmap, report.
 */
export async function predictImage(file, modelId = null) {
  const form = new FormData();
  form.append('file', file);

  const url = modelId
    ? `${API_BASE}/predict?model_id=${modelId}`
    : `${API_BASE}/predict`;

  const res = await fetch(url, { method: 'POST', body: form });

  if (!res.ok) {
    let detail;
    try { detail = await res.json(); } catch { detail = null; }
    if (detail?.detail?.message) {
      const err = new Error(detail.detail.message);
      err.hint = detail.detail.hint || null;
      err.isRejection = true;
      throw err;
    }
    const text = detail ? JSON.stringify(detail) : await res.text();
    throw new Error(`Analysis failed (${res.status}): ${text}`);
  }

  return res.json();
}

/** Fetch the full prediction history list. */
export async function fetchHistory() {
  const res = await fetch(`${API_BASE}/history`);
  if (!res.ok) throw new Error(`Failed to fetch history (${res.status})`);
  return res.json();
}

/** Fetch complete details for one prediction by ID. */
export async function fetchPredictionDetail(id) {
  const res = await fetch(`${API_BASE}/history/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch prediction ${id}`);
  return res.json();
}

/** Build the full URL for a heatmap image file. */
export function getHeatmapUrl(relativePath) {
  if (!relativePath) return null;
  return `${API_BASE}/${relativePath}`;
}
