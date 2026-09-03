import { describe, it, expect, beforeEach } from 'vitest';
import { useEffect } from 'react';
import { http, HttpResponse } from 'msw';
import { render, screen, waitFor } from '../test-utils';
import { server } from '../mocks/server';
import { supplierStatsHandlers } from '../pages/SupplierDashboard.handlers';
import SupplierDashboard from '../pages/SupplierDashboard';
import { Route, Routes } from 'react-router-dom';
import { AuthProvider } from '../hooks/useAuth';
import apiClient from '../api/client';
import { AccessDeniedNotice, RequirePermission } from './index';

const ForbiddenRequest = () => {
  useEffect(() => { void apiClient.get('/forbidden').catch(() => undefined); }, []);
  return <AccessDeniedNotice />;
};

describe('application routes', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders the supplier dashboard route', async () => {
    server.use(...supplierStatsHandlers);

    render(
      <Routes>
        <Route path="/suppliers/:id/dashboard" element={<SupplierDashboard />} />
      </Routes>,
      {
      user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
      token: 'fake-jwt-token',
      route: '/suppliers/sup-001/dashboard',
      },
    );

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Acme Corp' })).toBeInTheDocument();
    });
  });

  it('blocks a route when the server-derived permission is absent', () => {
    render(
      <AuthProvider initialUser={{ email: null, fullName: 'Viewer', roles: ['Viewer'], permissions: ['read'] }}>
        <RequirePermission permission="upload"><p>Upload allowed</p></RequirePermission>
      </AuthProvider>,
    );

    expect(screen.getByRole('alert')).toHaveTextContent('You do not have permission to access this page.');
    expect(screen.queryByText('Upload allowed')).not.toBeInTheDocument();
  });

  it('shows distinct access-denied UX after an authenticated API 403', async () => {
    server.use(http.get('http://localhost:8000/api/forbidden', () => new HttpResponse(null, { status: 403 })));
    render(<ForbiddenRequest />, { user: { email: null, fullName: 'Viewer', roles: ['Viewer'], permissions: ['read'] } });

    expect(await screen.findByTestId('access-denied')).toHaveTextContent('Access denied. You do not have permission to complete this action.');
  });
});
