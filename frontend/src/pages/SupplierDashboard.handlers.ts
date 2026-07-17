import { http, HttpResponse } from 'msw';

export const supplierStatsFixture = {
  supplierName: 'Acme Corp',
  taxId: 'TAX-12345',
  totalInvoices: 10,
  annualTotal: 12000,
  annualPercentage: 40,
  grandTotal: 30000,
  monthlyAmounts: [
    { month: '2025-07', amount: 1000 },
    { month: '2025-08', amount: 1200 },
    { month: '2025-09', amount: 800 },
    { month: '2025-10', amount: 1100 },
    { month: '2025-11', amount: 900 },
    { month: '2025-12', amount: 1400 },
    { month: '2026-01', amount: 1000 },
    { month: '2026-02', amount: 1200 },
    { month: '2026-03', amount: 800 },
    { month: '2026-04', amount: 1100 },
    { month: '2026-05', amount: 1500 },
    { month: '2026-06', amount: 2000 },
  ],
  topLineItems: [
    { description: 'Cloud hosting', totalAmount: 5000, invoiceCount: 4 },
    { description: 'Support', totalAmount: 3000, invoiceCount: 3 },
  ],
  statusDistribution: { Approved: 6, Rejected: 1, Pending: 3 },
  averageInvoiceAmount: 1200,
  topInvoice: { invoiceNumber: 'INV-009', amount: 2500 },
};

export const supplierStatsHandlers = [
  http.get('http://localhost:8000/api/suppliers/:id/stats', () => {
    return HttpResponse.json(supplierStatsFixture);
  }),
];
