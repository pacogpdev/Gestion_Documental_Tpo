import { http, HttpResponse } from 'msw';

export const mockSuppliers = [
  {
    id: 'sup-001',
    name: 'Acme Corp',
    taxId: 'TAX-12345',
    email: 'billing@acme.com',
    address: '123 Main St, Springfield',
  },
  {
    id: 'sup-002',
    name: 'Globex Inc',
    taxId: 'TAX-67890',
    email: 'ap@globex.com',
    address: '456 Oak Ave, Shelbyville',
  },
  {
    id: 'sup-003',
    name: 'Initech',
    taxId: 'TAX-11111',
    email: 'payments@initech.com',
    address: '789 Pine Rd, Capital City',
  },
];

export const suppliersHandlers = [
  http.get('http://localhost:8000/api/suppliers', () => {
    return HttpResponse.json(mockSuppliers);
  }),
  http.post('http://localhost:8000/api/suppliers', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 'sup-004', ...(body as object) }, { status: 201 });
  }),
];
