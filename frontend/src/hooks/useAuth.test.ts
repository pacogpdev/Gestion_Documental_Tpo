import { act, renderHook, waitFor } from '../test-utils';
import { createElement, type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { server } from '../mocks/server';
import { AuthProvider, useAuth } from './useAuth';

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
    server.use(http.get('http://localhost:8000/api/users/me', () => HttpResponse.json(profile)));
  });

  const profile = { email: null, fullName: 'Test User', roles: ['Viewer'] as const, permissions: ['read', 'statistics'] as const };
  const session = () => ({ account: {} as object, acquireToken: vi.fn().mockResolvedValue('access-token'), login: vi.fn(), logout: vi.fn() });
  const wrapper = (value: ReturnType<typeof session>) => ({ children }: { children: ReactNode }) => createElement(AuthProvider, { session: value }, children);

  it('restores an MSAL session, loads the server profile, and clears obsolete storage', async () => {
    localStorage.setItem('auth_token', 'obsolete');
    localStorage.setItem('user_profile', JSON.stringify(profile));
    server.use(http.get('http://localhost:8000/api/users/me', ({ request }) => { expect(request.headers.get('authorization')).toBe('Bearer access-token'); return HttpResponse.json(profile); }));
    const { result } = renderHook(() => useAuth(), { wrapper: wrapper(session()) });

    await waitFor(() => expect(result.current.user).toEqual(profile));
    expect(result.current.can('statistics')).toBe(true);
    expect(localStorage.getItem('auth_token')).toBeNull();
  });

  it('becomes unauthenticated after a 401 response', async () => {
    const value = session();
    server.use(http.get('http://localhost:8000/api/users/me', () => new HttpResponse(null, { status: 401 })));
    const { result } = renderHook(() => useAuth(), { wrapper: wrapper(value) });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
    expect(result.current.can('read')).toBe(false);
  });

  it('delegates login and logout to the session while clearing local auth state', async () => {
    const value = session();
    const { result } = renderHook(() => useAuth(), { wrapper: wrapper(value) });

    await waitFor(() => expect(result.current.user).toEqual(profile));
    await act(async () => { await result.current.login(); await result.current.logout(); });
    expect(value.login).toHaveBeenCalledOnce();
    expect(value.logout).toHaveBeenCalledOnce();
    expect(result.current.user).toBeNull();
  });
});
