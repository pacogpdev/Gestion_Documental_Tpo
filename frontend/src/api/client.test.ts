import { describe, it, expect, vi, beforeEach } from 'vitest';

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
});
