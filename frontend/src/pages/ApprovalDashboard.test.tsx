import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test-utils';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';
import ApprovalDashboard from './ApprovalDashboard';
import { approvalDashboardHandlers, pdfViewHandlers } from './ApprovalDashboard.handlers';

describe('ApprovalDashboard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('2.2 — Data Loading: loading state → render list', () => {
    it('shows loading indicator then renders invoice rows and summary cards', async () => {
      server.use(
        http.get('http://localhost:8000/api/invoices', async () => {
          await new Promise((r) => setTimeout(r, 50));
          return HttpResponse.json([
            {
              id: 'inv-001',
              invoiceNumber: 'INV-2024-001',
              supplierName: 'Acme Corp',
              date: '2024-01-15',
              totalAmount: 1250.0,
              currency: 'USD',
              status: 'Pending',
            },
            {
              id: 'inv-002',
              invoiceNumber: 'INV-2024-002',
              supplierName: 'Globex Inc',
              date: '2024-01-20',
              totalAmount: 3400.5,
              currency: 'EUR',
              status: 'Approved',
            },
          ]);
        })
      );

      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/approvals',
      });

      // Loading state should be visible before data resolves
      expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
      expect(screen.getByText('Loading invoices...')).toBeInTheDocument();

      // Wait for invoice data to appear
      await waitFor(() => {
        expect(screen.getByText('INV-2024-001')).toBeInTheDocument();
        expect(screen.getByText('INV-2024-002')).toBeInTheDocument();
      });

      // Loading state should be gone
      expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();

      // Supplier names render
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      expect(screen.getByText('Globex Inc')).toBeInTheDocument();

      // Summary cards show correct counts
      expect(screen.getByTestId('summary-pending')).toHaveTextContent('1');
      expect(screen.getByTestId('summary-approved')).toHaveTextContent('1');
      expect(screen.getByTestId('summary-rejected')).toHaveTextContent('0');
    });
  });

  describe('2.3 — Empty State: no pending invoices', () => {
    it('shows empty state message and zero counts in summary cards', async () => {
      server.use(
        http.get('http://localhost:8000/api/invoices', () => {
          return HttpResponse.json([]);
        })
      );

      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/approvals',
      });

      // Wait for empty state message
      await waitFor(() => {
        expect(screen.getByTestId('empty-state')).toBeInTheDocument();
        expect(screen.getByText('No invoices found.')).toBeInTheDocument();
      });

      // Summary cards show zero
      expect(screen.getByTestId('summary-pending')).toHaveTextContent('0');
      expect(screen.getByTestId('summary-approved')).toHaveTextContent('0');
      expect(screen.getByTestId('summary-rejected')).toHaveTextContent('0');
    });
  });

  describe('2.4 — Approval Action: PATCH call → update list', () => {
    it('calls PATCH with Approved status and refreshes the invoice list', async () => {
      let patchCalled = false;
      let patchStatus = '';

      server.use(
        http.get('http://localhost:8000/api/invoices', () => {
          return HttpResponse.json([
            {
              id: 'inv-001',
              invoiceNumber: 'INV-2024-001',
              supplierName: 'Acme Corp',
              date: '2024-01-15',
              totalAmount: 1250.0,
              currency: 'USD',
              status: 'Pending',
            },
          ]);
        }),
        http.patch('http://localhost:8000/api/invoices/:id/approve', async ({ request }) => {
          patchCalled = true;
          const body = (await request.json()) as { status: string };
          patchStatus = body.status;
          return HttpResponse.json({ id: 'inv-001', status: body.status });
        })
      );

      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/approvals',
      });

      // Wait for invoice to render
      await waitFor(() => {
        expect(screen.getByText('INV-2024-001')).toBeInTheDocument();
      });

      // Click Approve button
      fireEvent.click(screen.getByTestId('approve-btn-inv-001'));

      // PATCH should have been called with Approved status
      await waitFor(() => {
        expect(patchCalled).toBe(true);
        expect(patchStatus).toBe('Approved');
      });

      // List should re-render (fetchInvoices called again)
      await waitFor(() => {
        expect(screen.getByText('INV-2024-001')).toBeInTheDocument();
      });
    });
  });

  describe('2.5 — Rejection Action: PATCH call → update list', () => {
    it('calls PATCH with Rejected status and refreshes the invoice list', async () => {
      let patchCalled = false;
      let patchStatus = '';

      server.use(
        http.get('http://localhost:8000/api/invoices', () => {
          return HttpResponse.json([
            {
              id: 'inv-001',
              invoiceNumber: 'INV-2024-001',
              supplierName: 'Acme Corp',
              date: '2024-01-15',
              totalAmount: 1250.0,
              currency: 'USD',
              status: 'Pending',
            },
          ]);
        }),
        http.patch('http://localhost:8000/api/invoices/:id/approve', async ({ request }) => {
          patchCalled = true;
          const body = (await request.json()) as { status: string };
          patchStatus = body.status;
          return HttpResponse.json({ id: 'inv-001', status: body.status });
        })
      );

      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/approvals',
      });

      // Wait for invoice to render
      await waitFor(() => {
        expect(screen.getByText('INV-2024-001')).toBeInTheDocument();
      });

      // Click Reject button
      fireEvent.click(screen.getByTestId('reject-btn-inv-001'));

      // PATCH should have been called with Rejected status
      await waitFor(() => {
        expect(patchCalled).toBe(true);
        expect(patchStatus).toBe('Rejected');
      });

      // List should re-render (fetchInvoices called again)
      await waitFor(() => {
        expect(screen.getByText('INV-2024-001')).toBeInTheDocument();
      });
    });
  });

  /* ── Sorting tests (TDD) ── */

  const sortTestInvoices = [
    { id: 'inv-003', invoiceNumber: 'INV-003', supplierName: 'Zeta Ltd',   date: '2024-06-01', totalAmount: 500,    currency: 'EUR', status: 'Pending' },
    { id: 'inv-001', invoiceNumber: 'INV-001', supplierName: 'Alpha Inc',  date: '2024-01-15', totalAmount: 1250,   currency: 'USD', status: 'Approved' },
    { id: 'inv-002', invoiceNumber: 'INV-002', supplierName: 'Beta Corp',  date: '2024-03-20', totalAmount: 3400.5, currency: 'EUR', status: 'Pending' },
  ];

  describe('2.6 — Sort by Date column', () => {
    it('sorts ascending on first click (oldest first)', async () => {
      server.use(http.get('http://localhost:8000/api/invoices', () => HttpResponse.json(sortTestInvoices)));
      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token', route: '/approvals',
      });

      await waitFor(() => expect(screen.getByText('INV-003')).toBeInTheDocument());

      // Click Date header
      fireEvent.click(screen.getByTestId('sort-date'));

      // Now oldest date (2024-01-15) should be first row
      const rows = screen.getAllByTestId(/^invoice-row-/);
      await waitFor(() => {
        expect(rows[0]).toHaveTextContent('INV-001');
        expect(rows[1]).toHaveTextContent('INV-002');
        expect(rows[2]).toHaveTextContent('INV-003');
      });
    });

    it('sorts descending on second click (newest first)', async () => {
      server.use(http.get('http://localhost:8000/api/invoices', () => HttpResponse.json(sortTestInvoices)));
      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token', route: '/approvals',
      });

      await waitFor(() => expect(screen.getByText('INV-003')).toBeInTheDocument());

      // Click twice: first asc, then desc
      fireEvent.click(screen.getByTestId('sort-date'));
      fireEvent.click(screen.getByTestId('sort-date'));

      const rows = screen.getAllByTestId(/^invoice-row-/);
      await waitFor(() => {
        expect(rows[0]).toHaveTextContent('INV-003'); // newest first
        expect(rows[2]).toHaveTextContent('INV-001'); // oldest last
      });
    });
  });

  describe('2.7 — Sort by Amount column', () => {
    it('sorts ascending on first click (lowest first)', async () => {
      server.use(http.get('http://localhost:8000/api/invoices', () => HttpResponse.json(sortTestInvoices)));
      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token', route: '/approvals',
      });

      await waitFor(() => expect(screen.getByText('INV-003')).toBeInTheDocument());

      fireEvent.click(screen.getByTestId('sort-amount'));

      const rows = screen.getAllByTestId(/^invoice-row-/);
      await waitFor(() => {
        expect(rows[0]).toHaveTextContent('500.00');   // lowest
        expect(rows[2]).toHaveTextContent('3,400.50'); // highest
      });
    });

    it('sorts descending on second click (highest first)', async () => {
      server.use(http.get('http://localhost:8000/api/invoices', () => HttpResponse.json(sortTestInvoices)));
      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token', route: '/approvals',
      });

      await waitFor(() => expect(screen.getByText('INV-003')).toBeInTheDocument());

      fireEvent.click(screen.getByTestId('sort-amount'));
      fireEvent.click(screen.getByTestId('sort-amount'));

      const rows = screen.getAllByTestId(/^invoice-row-/);
      await waitFor(() => {
        expect(rows[0]).toHaveTextContent('3,400.50'); // highest first
        expect(rows[2]).toHaveTextContent('500.00');   // lowest last
      });
    });
  });

  describe('2.8 — Sort indicator and column switching', () => {
    it('shows ▲ indicator on active sorted column', async () => {
      server.use(http.get('http://localhost:8000/api/invoices', () => HttpResponse.json(sortTestInvoices)));
      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token', route: '/approvals',
      });

      await waitFor(() => expect(screen.getByText('INV-003')).toBeInTheDocument());

      // Default sort is date descending, so Date has aria-sort="descending"
      expect(screen.getByTestId('sort-date')).toHaveAttribute('aria-sort', 'descending');
      expect(screen.getByTestId('sort-amount')).not.toHaveAttribute('aria-sort');

      fireEvent.click(screen.getByTestId('sort-date'));
      expect(screen.getByTestId('sort-date')).toHaveAttribute('aria-sort', 'ascending');

      // Switch to Amount sorts asc by default on new column
      fireEvent.click(screen.getByTestId('sort-amount'));
      expect(screen.getByTestId('sort-amount')).toHaveAttribute('aria-sort', 'ascending');
      // Date should no longer be the active column
      expect(screen.getByTestId('sort-date')).not.toHaveAttribute('aria-sort');
    });

    it('shows ▼ indicator when sorting descending', async () => {
      server.use(http.get('http://localhost:8000/api/invoices', () => HttpResponse.json(sortTestInvoices)));
      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token', route: '/approvals',
      });

      await waitFor(() => expect(screen.getByText('INV-003')).toBeInTheDocument());

      // Default is date desc, click twice more: desc → asc → desc
      fireEvent.click(screen.getByTestId('sort-date'));
      fireEvent.click(screen.getByTestId('sort-date'));
      expect(screen.getByTestId('sort-date')).toHaveAttribute('aria-sort', 'descending');
    });
  });

  describe('2.9 — PDF view action', () => {
    it('renders the view control only for Azure URLs and opens the PDF in a new tab', async () => {
      server.use(...pdfViewHandlers);
      const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);

      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token', route: '/approvals',
      });

      await waitFor(() => expect(screen.getByTestId('invoice-row-inv-pdf')).toBeInTheDocument());

      const viewButton = screen.getByTestId('view-pdf-btn-inv-pdf');
      expect(viewButton).toBeEnabled();

      fireEvent.click(viewButton);

      expect(openSpy).toHaveBeenCalledWith(
        'https://storage.example/facturas-proveedores/supplier/invoice/file.pdf',
        '_blank',
      );
      openSpy.mockRestore();
    });

    it('hides the view control for legacy and missing file URLs', async () => {
      server.use(...pdfViewHandlers);

      render(<ApprovalDashboard />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token', route: '/approvals',
      });

      await waitFor(() => expect(screen.getByTestId('invoice-row-inv-missing')).toBeInTheDocument());

      expect(screen.queryByTestId('view-pdf-btn-inv-legacy')).not.toBeInTheDocument();
      expect(screen.queryByTestId('view-pdf-btn-inv-missing')).not.toBeInTheDocument();
    });
  });
});
