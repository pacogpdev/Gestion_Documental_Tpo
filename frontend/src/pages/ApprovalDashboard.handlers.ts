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

export const pdfViewInvoices = [
  {
    id: 'inv-pdf',
    invoiceNumber: 'INV-PDF',
    supplierName: 'PDF Supplier',
    date: '2024-02-01',
    totalAmount: 100,
    currency: 'EUR',
    status: 'Pending' as const,
    fileUrl: 'https://storage.example/facturas-proveedores/supplier/invoice/file.pdf',
  },
  {
    id: 'inv-legacy',
    invoiceNumber: 'INV-LEGACY',
    supplierName: 'Legacy Supplier',
    date: '2024-02-02',
    totalAmount: 200,
    currency: 'EUR',
    status: 'Approved' as const,
    fileUrl: '/uploads/legacy.pdf',
  },
  {
    id: 'inv-missing',
    invoiceNumber: 'INV-MISSING',
    supplierName: 'Missing Supplier',
    date: '2024-02-03',
    totalAmount: 300,
    currency: 'EUR',
    status: 'Rejected' as const,
    fileUrl: null,
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

export const pdfViewHandlers = [
  http.get('http://localhost:8000/api/invoices', () => {
    return HttpResponse.json(pdfViewInvoices);
  }),
];
