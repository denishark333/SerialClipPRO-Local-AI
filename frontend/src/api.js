// Same-origin in production; Vite proxies these routes during development.
export const API_BASE_URL = (import.meta.env.VITE_APP_API_BASE_URL || '/api').replace(/\/$/, '');
export const MEDIA_BASE_URL = API_BASE_URL.replace(/\/api$/, '');

export async function apiFetch(path, options) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = Array.isArray(data.detail)
      ? data.detail.map(item => item.msg).join('; ')
      : data.detail;
    throw new Error(detail || `Erro HTTP ${response.status}`);
  }
  return response;
}
