import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, tokenStore } from "./api";

function mockFetchOnce(status: number, body: unknown) {
  (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response);
}

describe("api client", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
    tokenStore.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns parsed JSON on success", async () => {
    mockFetchOnce(200, { hello: "world" });
    const result = await api<{ hello: string }>("/api/test");
    expect(result.hello).toBe("world");
  });

  it("normalizes backend errors into ApiError", async () => {
    mockFetchOnce(409, { code: "conflict", message: "Already exists." });
    await expect(api("/api/test", { method: "POST", body: {} })).rejects.toMatchObject({
      code: "conflict",
      message: "Already exists.",
      status: 409,
    });
  });

  it("throws a friendly network error when fetch fails", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error("boom"));
    await expect(api("/api/test")).rejects.toBeInstanceOf(ApiError);
  });

  it("attaches the bearer token when present", async () => {
    tokenStore.set({ access_token: "abc", refresh_token: "def", token_type: "bearer" });
    mockFetchOnce(200, {});
    await api("/api/test");
    const [, options] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect((options.headers as Record<string, string>).Authorization).toBe("Bearer abc");
  });

  it("refreshes once on 401 and retries the request", async () => {
    tokenStore.set({ access_token: "old", refresh_token: "ref", token_type: "bearer" });
    mockFetchOnce(401, { code: "authentication_failed", message: "expired" });
    mockFetchOnce(200, { access_token: "new", refresh_token: "ref2", token_type: "bearer" });
    mockFetchOnce(200, { ok: true });

    const result = await api<{ ok: boolean }>("/api/protected");
    expect(result.ok).toBe(true);
    expect(tokenStore.access).toBe("new");
    expect(global.fetch).toHaveBeenCalledTimes(3);
  });
});
