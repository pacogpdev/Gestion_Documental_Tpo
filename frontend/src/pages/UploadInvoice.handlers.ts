import { http, HttpResponse } from 'msw';

const mockExtractedData = {
  status: 'success',
  invoice_id: 'inv-001',
  extracted_data: {
    supplier_name: 'Acme Corp',
    invoice_number: 'INV-2024-001',
    date: '2024-01-15',
    total_amount: 1250.0,
    currency: 'USD',
    line_items: [
      { description: 'Consulting Services', quantity: 10, unit_price: 100, total_price: 1000 },
      { description: 'Software License', quantity: 1, unit_price: 250, total_price: 250 },
    ],
  },
};

export const uploadInvoiceHandlers = [
  http.post('http://localhost:8000/api/invoices/upload', async () => {
    return HttpResponse.json(mockExtractedData);
  }),
];
