import type { Config } from '../types/config';
import type { Session } from '../types/session';

const params = new URLSearchParams(window.location.search);
const flaskPort = params.get('port');

// In production (pywebview loads Flask directly), same origin.
// In dev mode (Vite dev server), port is passed as query param.
export const API_BASE = flaskPort ? `http://localhost:${flaskPort}` : '';

export async function fetchSessions(): Promise<Session[]> {
  const resp = await fetch(`${API_BASE}/api/sessions`);
  return resp.json();
}

export async function fetchSession(id: string): Promise<Session> {
  const resp = await fetch(`${API_BASE}/api/sessions/${id}`);
  return resp.json();
}

export async function startProcessing(
  filePath: string,
  targetLang: string,
): Promise<{ id: string }> {
  const resp = await fetch(`${API_BASE}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_path: filePath, target_lang: targetLang }),
  });
  return resp.json();
}

export async function deleteSession(id: string): Promise<void> {
  await fetch(`${API_BASE}/api/sessions/${id}`, { method: 'DELETE' });
}

export async function fetchConfig(): Promise<Config> {
  const resp = await fetch(`${API_BASE}/api/config`);
  return resp.json();
}

export async function updateConfig(patch: Partial<Config>): Promise<Config> {
  const resp = await fetch(`${API_BASE}/api/config`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });
  return resp.json();
}
