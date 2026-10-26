/**
 * api.js — Servicio centralizado para comunicarse con la API de Virtual World.
 * Gestiona autenticación, tokens y todas las peticiones al backend.
 */

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

/** Token JWT almacenado en memoria */
let authToken = localStorage.getItem('vw_admin_token') || '';

/** Entorno visto actualmente en el dashboard */
let viewedWorkspaceId = localStorage.getItem('vw_admin_workspace')
  ? Number(localStorage.getItem('vw_admin_workspace'))
  : null;

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

/** Configurar entorno que se está viendo */
export function setViewedWorkspace(id) {
  if (id !== null && id !== undefined && id !== '') {
    viewedWorkspaceId = Number(id);
    localStorage.setItem('vw_admin_workspace', String(id));
  } else {
    viewedWorkspaceId = null;
    localStorage.removeItem('vw_admin_workspace');
  }
}

/** Obtener id del entorno que se está viendo */
export function getViewedWorkspace() {
  return viewedWorkspaceId;
}

/** Headers con autenticación y entorno visto */
function authHeaders() {
  return {
    'Content-Type': 'application/json',
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    ...(viewedWorkspaceId !== null ? { 'X-Workspace-Id': String(viewedWorkspaceId) } : {}),
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
    window.location.href = '/dashboard/login';
    throw new Error('Sesión expirada');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
    if (response.status === 404 && error.detail === 'WORKSPACE_NOT_FOUND') {
      window.dispatchEvent(new Event('vw:workspace-missing'));
    }
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // 204 (p. ej. al eliminar un entorno) no trae cuerpo.
  if (response.status === 204) return null;
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
    body: JSON.stringify({ typology, confirm_email: confirmEmail, confirm_delete: true }),
  });
}

export async function resetAllProgress(playerId, confirmEmail) {
  return apiFetch(`/admin/players/${playerId}/reset/all`, {
    method: 'POST',
    body: JSON.stringify({ confirm_email: confirmEmail, confirm_delete: true }),
  });
}

// ── Gestión de Slots ─────────────────────────────────────────────────────────

export async function getPlayerSlots(playerId) {
  return apiFetch(`/admin/players/${playerId}/slots`);
}

export async function createPlayerSlot(playerId, label) {
  return apiFetch(`/admin/players/${playerId}/slots`, {
    method: 'POST',
    body: JSON.stringify({ label }),
  });
}

export async function activatePlayerSlot(playerId, slotNumber) {
  return apiFetch(`/admin/players/${playerId}/slots/${slotNumber}/activate`, {
    method: 'PUT',
  });
}

// ── Restablecer Contraseña ──────────────────────────────────────────────────

export async function resetPlayerPassword(playerId) {
  return apiFetch(`/admin/players/${playerId}/reset-password`, {
    method: 'POST',
  });
}

// ── Catálogo de Logros y Medallas ───────────────────────────────────────────

export async function getAchievementsCatalog() {
  return apiFetch('/achievements/catalog');
}

export async function updateCatalogAchievement(achievementId, data) {
  return apiFetch(`/achievements/admin/${achievementId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function uploadMedalImage(achievementId, file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE}/achievements/admin/${achievementId}/medal-image`, {
    method: 'PUT',
    headers: {
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    },
    body: formData,
  });

  if (response.status === 401) {
    clearToken();
    window.location.href = '/dashboard/login';
    throw new Error('Sesión expirada');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al subir la imagen' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function deleteMedalImage(achievementId) {
  return apiFetch(`/achievements/admin/${achievementId}/medal-image`, {
    method: 'DELETE',
  });
}

// ── Health ───────────────────────────────────────────────────────────────────

export async function checkHealth() {
  return apiFetch('/health');
}

// ── Módulo Logros y Medallas (Dashboard Admin) ──────────────────────────────

export async function getAchievementsDashboard(filters = {}) {
  const params = new URLSearchParams();
  if (filters.q) params.set('q', filters.q);
  if (filters.category) params.set('category', filters.category);
  if (filters.tier) params.set('tier', filters.tier);
  if (filters.player_id) params.set('player_id', filters.player_id);
  if (filters.unlock_status) params.set('unlock_status', filters.unlock_status);
  if (filters.sort) params.set('sort', filters.sort);
  if (filters.order) params.set('order', filters.order);
  const qs = params.toString();
  return apiFetch(`/admin/achievements${qs ? '?' + qs : ''}`);
}

export async function getAchievementsStats() {
  return apiFetch('/admin/achievements/stats');
}

export async function getComicsResumen() {
  return apiFetch('/comics/admin/resumen');
}

export async function getComicsJugadores() {
  return apiFetch('/comics/admin/jugadores');
}

export async function getAchievementDetail(achievementId) {
  return apiFetch(`/admin/achievements/${achievementId}`);
}

export async function getAchievementPlayers(achievementId, search = '') {
  const params = search ? `?q=${encodeURIComponent(search)}` : '';
  return apiFetch(`/admin/achievements/${achievementId}/players${params}`);
}

export async function getAchievementImageHistory(achievementId) {
  return apiFetch(`/admin/achievements/${achievementId}/image-history`);
}

export async function uploadMedalImageAdmin(achievementId, file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/admin/achievements/${achievementId}/medal-image`, {
    method: 'PUT',
    headers: {
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    },
    body: formData,
  });

  if (response.status === 401) {
    clearToken();
    window.location.href = '/dashboard/login';
    throw new Error('Sesión expirada');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al subir la imagen' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function restoreMedalImage(achievementId, historyId) {
  return apiFetch(`/admin/achievements/${achievementId}/restore-image/${historyId}`, {
    method: 'POST',
  });
}

export async function deleteHistoryImage(achievementId, historyId) {
  return apiFetch(`/admin/achievements/${achievementId}/image-history/${historyId}`, {
    method: 'DELETE',
  });
}

export async function getPlayerAchievementStats(playerId) {
  return apiFetch(`/admin/achievements/players/${playerId}/stats`);
}

// ── Exportación CSV/Excel ───────────────────────────────────────────────────

export function downloadAchievementsCSV(filters = {}) {
  const params = new URLSearchParams();
  if (filters.category) params.set('category', filters.category);
  if (filters.tier) params.set('tier', filters.tier);
  const qs = params.toString();
  _downloadFile(`/admin/achievements/export/csv${qs ? '?' + qs : ''}`, 'logros_medallas.csv');
}

export function downloadAchievementsExcel(filters = {}) {
  const params = new URLSearchParams();
  if (filters.category) params.set('category', filters.category);
  if (filters.tier) params.set('tier', filters.tier);
  const qs = params.toString();
  _downloadFile(`/admin/achievements/export/excel${qs ? '?' + qs : ''}`, 'logros_medallas.xlsx');
}

export function downloadAchievementPlayersCSV(achievementId) {
  _downloadFile(`/admin/achievements/${achievementId}/players/export/csv`, `jugadores_${achievementId}.csv`);
}

export function downloadAchievementPlayersExcel(achievementId) {
  _downloadFile(`/admin/achievements/${achievementId}/players/export/excel`, `jugadores_${achievementId}.xlsx`);
}

async function _downloadFile(endpoint, defaultFilename) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...(viewedWorkspaceId !== null ? { 'X-Workspace-Id': String(viewedWorkspaceId) } : {}),
    },
  });

  if (response.status === 401) {
    clearToken();
    window.location.href = '/dashboard/login';
    throw new Error('Sesión expirada');
  }

  if (!response.ok) {
    throw new Error(`Error al descargar: HTTP ${response.status}`);
  }

  const blob = await response.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = defaultFilename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}

// ── Métricas Avanzadas ──────────────────────────────────────────────────────

function _buildMetricParams(filters = {}) {
  const params = new URLSearchParams();
  if (filters.date_from) params.set('date_from', filters.date_from);
  if (filters.date_to) params.set('date_to', filters.date_to);
  if (filters.player_id) params.set('player_id', filters.player_id);
  if (filters.typology) params.set('typology', filters.typology);
  return params;
}

export async function getMetricsReadingTime(filters = {}) {
  const params = _buildMetricParams(filters);
  const qs = params.toString();
  return apiFetch(`/admin/metrics/reading-time${qs ? '?' + qs : ''}`);
}

export async function getMetricsAnswers(filters = {}) {
  const params = _buildMetricParams(filters);
  const qs = params.toString();
  return apiFetch(`/admin/metrics/answers${qs ? '?' + qs : ''}`);
}

export async function getMetricsQuestionAttempts(filters = {}) {
  const params = _buildMetricParams(filters);
  if (filters.limit) params.set('limit', filters.limit);
  const qs = params.toString();
  return apiFetch(`/admin/metrics/question-attempts${qs ? '?' + qs : ''}`);
}

/** Lo que un jugador habló con el asistente IA (pregunta y respuesta). */
export async function getNpcConversations(playerId) {
  return apiFetch(`/admin/metrics/npc-conversations?player_id=${playerId}`);
}

export async function getMetricsNpcInteractions(filters = {}) {
  const params = _buildMetricParams(filters);
  if (filters.npc_type) params.set('npc_type', filters.npc_type);
  const qs = params.toString();
  return apiFetch(`/admin/metrics/npc-interactions${qs ? '?' + qs : ''}`);
}

export async function getMetricsToolUsage(filters = {}) {
  const params = _buildMetricParams(filters);
  const qs = params.toString();
  return apiFetch(`/admin/metrics/tool-usage${qs ? '?' + qs : ''}`);
}

export function downloadMetricsCSV(metric, filters = {}) {
  const params = _buildMetricParams(filters);
  params.set('metric', metric);
  const qs = params.toString();
  _downloadFile(`/admin/metrics/export/csv?${qs}`, `metricas_${metric}.csv`);
}

export function downloadMetricsExcel(metric, filters = {}) {
  const params = _buildMetricParams(filters);
  params.set('metric', metric);
  const qs = params.toString();
  _downloadFile(`/admin/metrics/export/excel?${qs}`, `metricas_${metric}.xlsx`);
}

// ── Leaderboard ─────────────────────────────────────────────────────────────

export async function getLeaderboard(limit = 5) {
  return apiFetch(`/leaderboard/top?limit=${limit}`);
}

// ── Entornos (Workspaces) ───────────────────────────────────────────────────

export async function getWorkspaces() {
  return apiFetch('/admin/workspaces');
}

export async function createWorkspace(name, color) {
  return apiFetch('/admin/workspaces', {
    method: 'POST',
    body: JSON.stringify({ name, color }),
  });
}

export async function updateWorkspace(id, data) {
  return apiFetch(`/admin/workspaces/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function activateWorkspace(id) {
  return apiFetch(`/admin/workspaces/${id}/activate`, {
    method: 'POST',
  });
}

export async function deactivateWorkspace(id) {
  return apiFetch(`/admin/workspaces/${id}/deactivate`, {
    method: 'POST',
  });
}

export async function deleteWorkspace(id, confirmName) {
  return apiFetch(`/admin/workspaces/${id}?confirm_name=${encodeURIComponent(confirmName)}`, {
    method: 'DELETE',
  });
}

export async function addPlayers(workspaceId, players) {
  return apiFetch(`/admin/workspaces/${workspaceId}/players`, {
    method: 'POST',
    body: JSON.stringify({ players }),
  });
}


