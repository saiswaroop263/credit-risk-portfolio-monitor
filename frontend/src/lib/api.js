import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const api = {
  // Health check
  health: () => axios.get(`${API}/health`),

  // Upload CSV
  upload: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return axios.post(`${API}/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // Execute pipeline
  execute: (runId) => axios.post(`${API}/runs/${runId}/execute`),

  // Run demo
  demo: () => axios.post(`${API}/demo`),

  // Get runs
  getRuns: (limit = 50, status = null) => {
    const params = { limit };
    if (status) params.status = status;
    return axios.get(`${API}/runs`, { params });
  },

  // Get specific run
  getRun: (runId) => axios.get(`${API}/runs/${runId}`),

  // Get KPIs
  getKpis: (runId = null) => {
    const params = runId ? { run_id: runId } : {};
    return axios.get(`${API}/kpis`, { params });
  },

  // Get scores
  getScores: (runId = null, riskLevel = null, limit = 100) => {
    const params = { limit };
    if (runId) params.run_id = runId;
    if (riskLevel) params.risk_level = riskLevel;
    return axios.get(`${API}/scores`, { params });
  },

  // Get DQ report
  getDq: (runId = null) => {
    const params = runId ? { run_id: runId } : {};
    return axios.get(`${API}/dq`, { params });
  },

  // Get drift report
  getDrift: (runId = null) => {
    const params = runId ? { run_id: runId } : {};
    return axios.get(`${API}/drift`, { params });
  },

  // Get model metadata
  getModels: (runId = null) => {
    const params = runId ? { run_id: runId } : {};
    return axios.get(`${API}/models`, { params });
  },
};
