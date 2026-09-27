/**
 * Typed API client with JWT handling.
 *
 * - Attaches the access token to every request.
 * - On 401, performs a single-flight refresh and retries once.
 * - Normalizes backend errors into ApiError (code + user-safe message).
 */
import type { TokenPair } from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ACCESS_KEY = "acc_token";
const REFRESH_KEY = "ref_token";

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export const tokenStore = {
  get access(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(ACCESS_KEY);
  },
  get refresh(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(REFRESH_KEY);
  },
  set(tokens: TokenPair) {
    window.localStorage.setItem(ACCESS_KEY, tokens.access_token);
    window.localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  },
  clear() {
    window.localStorage.removeItem(ACCESS_KEY);
    window.localStorage.removeItem(REFRESH_KEY);
  },
};

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refresh = tokenStore.refresh;
      if (!refresh) return false;
      try {
        const response = await fetch(`${API_URL}/api/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
        });
        if (!response.ok) return false;
        tokenStore.set((await response.json()) as TokenPair);
        return true;
      } catch {
        return false;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as { code?: string; message?: string };
    return new ApiError(
      body.code ?? "unknown_error",
      body.message ?? "Something went wrong. Please try again.",
      response.status,
    );
  } catch {
    return new ApiError("unknown_error", "Something went wrong.", response.status);
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  formData?: FormData;
  retried?: boolean;
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const access = tokenStore.access;
  if (access) headers.Authorization = `Bearer ${access}`;
  if (options.body !== undefined) headers["Content-Type"] = "application/json";

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.formData ?? (options.body !== undefined ? JSON.stringify(options.body) : undefined),
    });
  } catch {
    throw new ApiError("network_error", "Cannot reach the server. Is the API running?", 0);
  }

  if (response.status === 401 && !options.retried && !path.startsWith("/api/auth/login")) {
    const refreshed = await tryRefresh();
    if (refreshed) return api<T>(path, { ...options, retried: true });
    tokenStore.clear();
    if (typeof window !== "undefined" && window.location.pathname !== "/auth/login") {
      window.location.href = "/auth/login";
    }
  }

  if (!response.ok) throw await parseError(response);
  return (await response.json()) as T;
}

export { API_URL };
