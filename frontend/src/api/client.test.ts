import { describe, it, expect, vi, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

describe('apiClient', () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('uses VITE_API_URL when set', async () => {
    vi.stubEnv('VITE_API_URL', 'https://test.api.com');
    const { default: client } = await import('./client');
    expect(client.defaults.baseURL).toBe('https://test.api.com');
  });

  it('falls back to localhost:8000/api when VITE_API_URL is not set', async () => {
    const { default: client } = await import('./client');
    expect(client.defaults.baseURL).toBe('http://localhost:8000/api');
  });

  it('reports an API 403 as access denied without invoking the 401 session handler', async () => {
    server.use(http.get('http://localhost:8000/api/forbidden', () => new HttpResponse(null, { status: 403 })));
    const { default: client, setAccessDeniedHandler, setUnauthorizedHandler } = await import('./client');
    const accessDenied = vi.fn();
    const unauthorized = vi.fn();
    setAccessDeniedHandler(accessDenied);
    setUnauthorizedHandler(unauthorized);

    await expect(client.get('/forbidden')).rejects.toMatchObject({ response: { status: 403 } });

    expect(accessDenied).toHaveBeenCalledOnce();
    expect(unauthorized).not.toHaveBeenCalled();
  });
});
