import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test-utils';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';
import { useLocation } from 'react-router-dom';
import SupplierDashboard from './SupplierDashboard';
import { supplierStatsFixture, supplierStatsHandlers } from './SupplierDashboard.handlers';

const LocationProbe = () => {
  const location = useLocation();
  return <output data-testid="current-location">{location.pathname}</output>;
};

describe('SupplierDashboard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('denies dashboard access to users without the Admin or Approver role', async () => {
    server.use(...supplierStatsHandlers);

    render(<SupplierDashboard />, {
      user: { email: 'viewer@test.com', fullName: 'Viewer User', roles: ['Viewer'] },
      token: 'fake-jwt-token',
      route: '/suppliers/sup-001/dashboard',
    });

    expect(screen.getByRole('alert')).toHaveTextContent('You do not have permission');
    expect(screen.queryByTestId('dashboard-loading')).not.toBeInTheDocument();
  });

  it('loads supplier stats and renders the supplier identity, KPI values, and chart labels', async () => {
    server.use(...supplierStatsHandlers);

    render(<SupplierDashboard />, {
      user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
      token: 'fake-jwt-token',
      route: '/suppliers/sup-001/dashboard',
    });

    expect(screen.getByTestId('dashboard-loading')).toHaveTextContent('Loading...');

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Acme Corp Dashboard' })).toBeInTheDocument());

    expect(screen.getByText(/TAX-12345/)).toBeInTheDocument();
    expect(screen.getByTestId('kpi-annual-total')).toHaveTextContent('12,000');
    expect(screen.getByTestId('kpi-annual-percentage')).toHaveTextContent('40%');
    expect(screen.getByTestId('kpi-average-invoice')).toHaveTextContent('1,200');
    expect(screen.getByTestId('kpi-invoice-count')).toHaveTextContent('10');
    expect(screen.getByTestId('monthly-chart')).toHaveTextContent('Monthly billing');
    expect(screen.getByTestId('supplier-share-chart')).toHaveTextContent('Supplier share');
    expect(screen.getByTestId('status-chart')).toHaveTextContent('Status distribution');
    expect(screen.getByTestId('items-chart')).toHaveTextContent('Top 10 line items');
  });

  it('normalizes the backend response contract when annual totals use API field names', async () => {
    server.use(
      http.get('http://localhost:8000/api/suppliers/:id/stats', () =>
        HttpResponse.json({
          supplierName: 'Globex Inc',
          taxId: 'TAX-67890',
          totalInvoices: 12,
          totalAmount: 15000,
          currency: 'USD',
          monthlyAmounts: [],
          annualAccumulated: 15000,
          annualPercentage: 30,
          grandTotalAllSuppliers: 50000,
          topLineItems: [],
          statusDistribution: { Approved: 8, Rejected: 1, Pending: 3 },
          averageInvoiceAmount: 1250,
          topInvoice: { number: 'INV-100', amount: 3200 },
        }),
      ),
    );

    render(<SupplierDashboard />, {
      user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
      token: 'fake-jwt-token',
      route: '/suppliers/sup-002/dashboard',
    });

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Globex Inc Dashboard' })).toBeInTheDocument());

    expect(screen.getByTestId('kpi-annual-total')).toHaveTextContent('15,000');
    expect(screen.getByTestId('kpi-annual-percentage')).toHaveTextContent('30%');
    expect(screen.getByTestId('kpi-invoice-count')).toHaveTextContent('12');
  });

  it('renders zero KPIs and labelled empty chart states for a supplier without invoices', async () => {
    server.use(
      http.get('http://localhost:8000/api/suppliers/:id/stats', () =>
        HttpResponse.json({
          ...supplierStatsFixture,
          totalInvoices: 0,
          annualTotal: 0,
          annualPercentage: 0,
          averageInvoiceAmount: 0,
          monthlyAmounts: [],
          topLineItems: [],
          statusDistribution: { Approved: 0, Rejected: 0, Pending: 0 },
          topInvoice: null,
        }),
      ),
    );

    render(<SupplierDashboard />, {
      user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
      token: 'fake-jwt-token',
      route: '/suppliers/sup-empty/dashboard',
    });

    await waitFor(() => expect(screen.getByTestId('kpi-invoice-count')).toHaveTextContent('0'));

    expect(screen.getByTestId('kpi-annual-total')).toHaveTextContent('0');
    expect(screen.getByTestId('kpi-annual-percentage')).toHaveTextContent('0%');
    expect(screen.getByTestId('monthly-empty')).toHaveTextContent('No monthly billing data');
    expect(screen.getByTestId('items-empty')).toHaveTextContent('No line item data');
  });

  it('shows a useful error when the stats request fails', async () => {
    server.use(
      http.get('http://localhost:8000/api/suppliers/:id/stats', () =>
        HttpResponse.json({ detail: 'Stats service unavailable' }, { status: 500 }),
      ),
    );

    render(<SupplierDashboard />, {
      user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
      token: 'fake-jwt-token',
      route: '/suppliers/sup-001/dashboard',
    });

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Stats service unavailable'));
  });

  it('shows the not-found response for an unknown supplier', async () => {
    server.use(
      http.get('http://localhost:8000/api/suppliers/:id/stats', () =>
        HttpResponse.json({ detail: 'Supplier not found' }, { status: 404 }),
      ),
    );

    render(<SupplierDashboard />, {
      user: { email: 'approver@test.com', fullName: 'Approver User', roles: ['Approver'] },
      token: 'fake-jwt-token',
      route: '/suppliers/unknown/dashboard',
    });

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Supplier not found'));
  });

  it('navigates back to the suppliers page', async () => {
    server.use(...supplierStatsHandlers);

    render(
      <>
        <SupplierDashboard />
        <LocationProbe />
      </>,
      {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/suppliers/sup-001/dashboard',
      },
    );

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Acme Corp Dashboard' })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Back to Suppliers' }));

    expect(screen.getByTestId('current-location')).toHaveTextContent('/suppliers');
  });
});
