import { http, HttpResponse } from 'msw';

export const mockInvoices = [
  {
    id: 'inv-001',
    invoiceNumber: 'INV-2024-001',
    supplierName: 'Acme Corp',
    date: '2024-01-15',
    totalAmount: 1250.0,
    currency: 'USD',
    status: 'Pending' as const,
  },
  {
    id: 'inv-002',
    invoiceNumber: 'INV-2024-002',
    supplierName: 'Globex Inc',
    date: '2024-01-20',
    totalAmount: 3400.5,
    currency: 'EUR',
    status: 'Approved' as const,
  },
];

export const approvalDashboardHandlers = [
  http.get('http://localhost:8000/api/invoices', () => {
    return HttpResponse.json(mockInvoices);
  }),
  http.patch('http://localhost:8000/api/invoices/:id/approve', ({ params }) => {
    return HttpResponse.json({ id: params.id, status: 'Approved' });
  }),
];
