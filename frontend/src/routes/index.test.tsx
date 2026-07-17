import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test-utils';
import { server } from '../mocks/server';
import { supplierStatsHandlers } from '../pages/SupplierDashboard.handlers';
import SupplierDashboard from '../pages/SupplierDashboard';
import { Route, Routes } from 'react-router-dom';

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
});
