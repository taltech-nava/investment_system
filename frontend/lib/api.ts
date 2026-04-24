// Server-side direct URL (Node.js only). Never exposed to the browser.
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

// Client-side proxy path. Next.js rewrites /backend/:path* → BACKEND_URL/:path*
// so the browser stays on the same origin and CORS never applies.
const BACKEND_PROXY = '/backend';

export interface PydanticFieldError {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: unknown;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly detail?: PydanticFieldError[] | string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function doFetch<T>(base: string, path: string, options?: RequestInit): Promise<T> {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = `${base}${normalizedPath}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    let message = res.statusText;
    let detail: PydanticFieldError[] | string | undefined;
    try {
      const body = await res.json();
      detail = body.detail;
      if (typeof body.detail === 'string') {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = [...new Set((body.detail as PydanticFieldError[]).map((e) => e.msg))].join('. ');
      }
    } catch {
      message = await res.text().catch(() => res.statusText);
    }
    throw new ApiError(res.status, message, detail);
  }

  return res.json() as Promise<T>;
}

/**
 * For Server Components only. Calls the backend directly via BACKEND_URL.
 */
export function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  return doFetch<T>(BACKEND_URL, path, options);
}

/**
 * For Client Components only. Routes through the /backend Next.js proxy
 * so the browser never makes a cross-origin request.
 */
export function clientApiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  return doFetch<T>(BACKEND_PROXY, path, options);
}
