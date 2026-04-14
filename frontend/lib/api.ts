const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';
const BACKEND_PROXY = '/backend';

function getBase(): string {
  return typeof window === 'undefined' ? BACKEND_URL : BACKEND_PROXY;
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = `${getBase()}${normalizedPath}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API error ${res.status}: ${text}`);
  }

  return res.json() as Promise<T>;
}
