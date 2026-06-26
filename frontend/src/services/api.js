const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';


async function request(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    ...options,
  };

  // Don't set Content-Type for FormData
  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  const response = await fetch(`${API_BASE}${endpoint}`, config);

  if (response.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('Session expired. Please log in again.');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || error.message || 'Request failed');
  }

  if (response.status === 204) return null;
  return response.json();
}

// Auth
export const auth = {
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  me: () => request('/auth/me'),
};

// Dashboard
export const dashboard = {
  getStats: () => request('/dashboard/stats'),
  getPipeline: () => request('/dashboard/pipeline'),
  getDisputeMetrics: () => request('/dashboard/dispute-metrics'),
  getRecentActivity: () => request('/dashboard/recent-activity'),
};

// Clients
export const clients = {
  list: (params = '') => request(`/clients${params ? `?${params}` : ''}`),
  get: (id) => request(`/clients/${id}`),
  create: (data) => request('/clients', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/clients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`/clients/${id}`, { method: 'DELETE' }),
  getTimeline: (id) => request(`/clients/${id}/timeline`),
};

// Credit Reports
export const creditReports = {
  upload: (formData) => request('/credit-reports/upload', { method: 'POST', body: formData }),
  parse: (id) => request(`/credit-reports/${id}/parse`, { method: 'POST' }),
  getItems: (id) => request(`/credit-reports/${id}/items`),
  getByClient: (clientId) => request(`/clients/${clientId}/reports`),
};

// Disputes
export const disputes = {
  list: (params = '') => request(`/disputes${params ? `?${params}` : ''}`),
  get: (id) => request(`/disputes/${id}`),
  create: (data) => request('/disputes', { method: 'POST', body: JSON.stringify(data) }),
  generateLetter: (id) => request(`/disputes/${id}/generate-letter`, { method: 'POST' }),
  checkCompliance: (id) => request(`/disputes/${id}/check-compliance`, { method: 'POST' }),
};

// Documents
export const documents = {
  upload: (formData) => request('/documents/upload', { method: 'POST', body: formData }),
  getByClient: (clientId) => request(`/clients/${clientId}/documents`),
};

// Mailing
export const mailing = {
  dispatch: (data) => request('/mailing/dispatch', { method: 'POST', body: JSON.stringify(data) }),
  getLogs: (params = '') => request(`/mailing/logs${params ? `?${params}` : ''}`),
};

// Client
export const client = {
  getStatus: () => request('/client/status'),
  upload: (formData) => request('/client/upload', { method: 'POST', body: formData }),
};

// Billing
export const billing = {
  getAgencyBilling: () => request('/agency/billing'),
  getClientBilling: () => request('/client/billing'),
};

export default {
  auth,
  dashboard,
  clients,
  client,
  creditReports,
  disputes,
  documents,
  mailing,
  billing,
};
