import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test-utils';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';
import Suppliers from './Suppliers';
import { suppliersHandlers, mockSuppliers } from './Suppliers.handlers';

describe('Suppliers', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('3.2 — Supplier list renders on mount', () => {
    it('displays supplier name, tax ID, and email columns from GET response', async () => {
      server.use(...suppliersHandlers);

      render(<Suppliers />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/suppliers',
      });

      // Wait for supplier rows to render
      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      });

      expect(screen.getByText('Globex Inc')).toBeInTheDocument();
      expect(screen.getByText('Initech')).toBeInTheDocument();

      // Verify tax IDs and emails
      expect(screen.getByText('TAX-12345')).toBeInTheDocument();
      expect(screen.getByText('billing@acme.com')).toBeInTheDocument();
      expect(screen.getByText('ap@globex.com')).toBeInTheDocument();
    });
  });

  describe('3.3 — Role access: Admin-only Add Supplier button', () => {
    it('shows Add Supplier button for Admin role', async () => {
      server.use(...suppliersHandlers);

      render(<Suppliers />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/suppliers',
      });

      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      });

      expect(screen.getByTestId('add-supplier-btn')).toBeInTheDocument();
    });

    it('hides Add Supplier button for Viewer role', async () => {
      server.use(...suppliersHandlers);

      render(<Suppliers />, {
        user: { email: 'viewer@test.com', fullName: 'Viewer User', roles: ['Viewer'] },
        token: 'fake-jwt-token',
        route: '/suppliers',
      });

      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      });

      expect(screen.queryByTestId('add-supplier-btn')).not.toBeInTheDocument();
    });

    it('hides Add Supplier button for Approver role', async () => {
      server.use(...suppliersHandlers);

      render(<Suppliers />, {
        user: { email: 'approver@test.com', fullName: 'Approver User', roles: ['Approver'] },
        token: 'fake-jwt-token',
        route: '/suppliers',
      });

      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      });

      expect(screen.queryByTestId('add-supplier-btn')).not.toBeInTheDocument();
    });
  });

  describe('3.4 — Search/Filter: dynamic filtering of supplier list', () => {
    it('filters suppliers by name, tax ID, and email as user types', async () => {
      server.use(...suppliersHandlers);

      render(<Suppliers />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/suppliers',
      });

      // Wait for all suppliers to render
      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
        expect(screen.getByText('Globex Inc')).toBeInTheDocument();
        expect(screen.getByText('Initech')).toBeInTheDocument();
      });

      const searchInput = screen.getByTestId('supplier-search');

      // Filter by name
      fireEvent.change(searchInput, { target: { value: 'Acme' } });
      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
        expect(screen.queryByText('Globex Inc')).not.toBeInTheDocument();
        expect(screen.queryByText('Initech')).not.toBeInTheDocument();
      });

      // Filter by tax ID
      fireEvent.change(searchInput, { target: { value: 'TAX-67890' } });
      await waitFor(() => {
        expect(screen.queryByText('Acme Corp')).not.toBeInTheDocument();
        expect(screen.getByText('Globex Inc')).toBeInTheDocument();
        expect(screen.queryByText('Initech')).not.toBeInTheDocument();
      });

      // Filter by email
      fireEvent.change(searchInput, { target: { value: 'payments@initech.com' } });
      await waitFor(() => {
        expect(screen.queryByText('Acme Corp')).not.toBeInTheDocument();
        expect(screen.queryByText('Globex Inc')).not.toBeInTheDocument();
        expect(screen.getByText('Initech')).toBeInTheDocument();
      });

      // Clear search — all suppliers visible again
      fireEvent.change(searchInput, { target: { value: '' } });
      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
        expect(screen.getByText('Globex Inc')).toBeInTheDocument();
        expect(screen.getByText('Initech')).toBeInTheDocument();
      });
    });

    it('shows empty state when search matches no suppliers', async () => {
      server.use(...suppliersHandlers);

      render(<Suppliers />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/suppliers',
      });

      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      });

      const searchInput = screen.getByTestId('supplier-search');
      fireEvent.change(searchInput, { target: { value: 'ZZZNoMatch' } });

      await waitFor(() => {
        expect(screen.getByText('No suppliers found.')).toBeInTheDocument();
      });
    });
  });

  describe('3.5 — Admin supplier deletion', () => {
    it('renders a delete button for Admin users', async () => {
      server.use(...suppliersHandlers);

      render(<Suppliers />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/suppliers',
      });

      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      });

      expect(screen.getByTestId('delete-supplier-btn-sup-001')).toBeInTheDocument();
    });

    it('calls the delete API and removes the supplier from the list', async () => {
      let currentSuppliers = [...mockSuppliers];
      const deleteSupplier = vi.fn((request: Request) => {
        const supplierId = request.url.split('/').pop();
        currentSuppliers = currentSuppliers.filter((supplier) => supplier.id !== supplierId);
        return HttpResponse.json({ status: 'success', deleted_id: supplierId });
      });

      server.use(
        http.get('http://localhost:8000/api/suppliers', () => HttpResponse.json(currentSuppliers)),
        http.delete('http://localhost:8000/api/suppliers/:id', ({ request }) => {
          const response = deleteSupplier(request);
          return response;
        }),
      );
      vi.spyOn(window, 'confirm').mockReturnValue(true);

      render(<Suppliers />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/suppliers',
      });

      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId('delete-supplier-btn-sup-001'));

      await waitFor(() => {
        expect(deleteSupplier).toHaveBeenCalledTimes(1);
        expect(screen.queryByText('Acme Corp')).not.toBeInTheDocument();
      });
    });

    it('shows the API detail when deletion returns 409 Conflict', async () => {
      server.use(
        ...suppliersHandlers,
        http.delete('http://localhost:8000/api/suppliers/:id', () =>
          HttpResponse.json(
            { detail: 'Cannot delete supplier: 2 invoice(s) associated. Delete the invoices first.' },
            { status: 409 },
          ),
        ),
      );
      vi.spyOn(window, 'confirm').mockReturnValue(true);
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => undefined);

      render(<Suppliers />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/suppliers',
      });

      await waitFor(() => {
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId('delete-supplier-btn-sup-001'));

      await waitFor(() => {
        expect(alertSpy).toHaveBeenCalledWith(
          'Cannot delete supplier: 2 invoice(s) associated. Delete the invoices first.',
        );
      });
    });
  });
});
