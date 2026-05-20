/**
 * api.js — Servicio centralizado para comunicarse con la API de Virtual World.
 * Gestiona autenticación, tokens y todas las peticiones al backend.
 */

const API_BASE = 'http://localhost:8001';

/** Token JWT almacenado en memoria */
let authToken = localStorage.getItem('vw_admin_token') || '';

/** Configurar token */
export function setToken(token) {
  authToken = token;
  localStorage.setItem('vw_admin_token', token);
}

/** Limpiar token */
export function clearToken() {
  authToken = '';
  localStorage.removeItem('vw_admin_token');
  localStorage.removeItem('vw_admin_user');
}

/** Obtener token actual */
export function getToken() {
  return authToken;
}

/** Headers con autenticación */
function authHeaders() {
  return {
    'Content-Type': 'application/json',
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
  };
}

/** Fetch genérico con manejo de errores */
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: authHeaders(),
    ...options,
  });

  if (response.status === 401) {
    clearToken();
    window.location.href = '/login';
    throw new Error('Sesión expirada');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ── Autenticación ───────────────────────────────────────────────────────────

export async function login(email, password) {
  const data = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  localStorage.setItem('vw_admin_user', JSON.stringify(data.user));
  return data;
}

export async function getMe() {
  return apiFetch('/auth/me');
}

export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('vw_admin_user'));
  } catch {
    return null;
  }
}

// ── Dashboard Admin ─────────────────────────────────────────────────────────

export async function getAdminStats() {
  return apiFetch('/admin/stats');
}

export async function getPlayers(search = '') {
  const params = search ? `?q=${encodeURIComponent(search)}` : '';
  return apiFetch(`/admin/players${params}`);
}

export async function getPlayerDetail(playerId) {
  return apiFetch(`/admin/players/${playerId}`);
}

export async function getPlayerSessions(playerId, typology = '') {
  const params = typology ? `?typology=${encodeURIComponent(typology)}` : '';
  return apiFetch(`/admin/players/${playerId}/sessions${params}`);
}

export async function getPlayerNotes(playerId) {
  return apiFetch(`/admin/players/${playerId}/notes`);
}

export async function resetTypology(playerId, typology, confirmEmail) {
  return apiFetch(`/admin/players/${playerId}/reset/typology`, {
    method: 'POST',
    body: JSON.stringify({ typology, confirm_email: confirmEmail }),
  });
}

export async function resetAllProgress(playerId, confirmEmail) {
  return apiFetch(`/admin/players/${playerId}/reset/all`, {
    method: 'POST',
    body: JSON.stringify({ confirm_email: confirmEmail }),
  });
}

// ── Health ───────────────────────────────────────────────────────────────────

export async function checkHealth() {
  return apiFetch('/health');
}
