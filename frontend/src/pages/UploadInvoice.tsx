import React, { useState } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../hooks/useAuth';

interface LineItem {
  description: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
}

interface InvoiceData {
  id?: string;
  invoiceNumber: string;
  date: string;
  totalAmount: number;
  currency: string;
  supplierName: string;
  lineItems: LineItem[];
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

const UploadInvoice: React.FC = () => {
  const { hasRole } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [extractedData, setExtractedData] = useState<InvoiceData | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  const canUpload = hasRole('Approver') || hasRole('Admin');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setValidationError(null);
      setServerError(null);
    }
  };

  const validateFile = (file: File): string | null => {
    if (file.type !== 'application/pdf') {
      return 'Only PDF files are accepted';
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'File size must be less than 10MB';
    }
    return null;
  };

  const handleUpload = async () => {
    if (!file) return;

    const error = validateFile(file);
    if (error) {
      setValidationError(error);
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post('/invoices/upload', formData);

      // Map backend snake_case response to camelCase InvoiceData
      const extraction = response.data.extracted_data || response.data;
      setExtractedData({
        id: response.data.invoice_id,
        invoiceNumber: extraction.invoice_number || '',
        date: extraction.date || '',
        totalAmount: extraction.total_amount || 0,
        currency: extraction.currency || 'USD',
        supplierName: extraction.supplier_name || '',
        lineItems: (extraction.line_items || []).map((item: any) => ({
          description: item.description || '',
          quantity: item.quantity || 0,
          unitPrice: item.unit_price || 0,
          totalPrice: item.total_price || 0,
        })),
      });
    } catch (error: any) {
      console.error('Upload failed', error);
      const status = error?.response?.status;
      if (status === 409) {
        const msg = error?.response?.data?.detail || 'Duplicate invoice number for this supplier.';
        setServerError(msg);
      } else {
        setServerError('Error uploading invoice. Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleSave = () => {
    if (!extractedData) return;
    setExtractedData(null);
    setFile(null);
    alert('Invoice saved as Pending. Review and approve it from the Approval Dashboard.');
  };

  if (!canUpload) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6 text-slate-800">Upload New Invoice</h1>
        <div className="bg-white p-8 rounded-lg shadow-sm border border-slate-200">
          <p className="text-slate-600" data-testid="restricted-message">You do not have permission to upload invoices.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6 text-slate-800">Upload New Invoice</h1>
      
      {!extractedData ? (
        <div className="bg-white p-8 rounded-lg shadow-sm border border-slate-200 flex flex-col items-center justify-center gap-6 border-dashed border-2">
          <div className="text-center">
            <p className="text-slate-600 mb-2">Select a PDF invoice to extract data</p>
            <input 
              type="file" 
              accept="application/pdf" 
              onChange={handleFileChange}
              data-testid="file-input"
              className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {validationError && (
              <p className="text-red-500 text-sm mt-1" data-testid="validation-error">{validationError}</p>
            )}
            {serverError && (
              <p className="text-red-600 text-sm mt-2 font-medium" data-testid="server-error">{serverError}</p>
            )}
          </div>
          <button 
            onClick={handleUpload}
            disabled={!file || uploading}
            data-testid="upload-button"
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium disabled:bg-slate-300 transition-colors"
          >
            {uploading ? 'Processing AI Extraction...' : 'Upload & Analyze'}
          </button>
        </div>
      ) : (
        <div className="bg-white p-8 rounded-lg shadow-sm border border-slate-200">
          <h2 className="text-xl font-semibold mb-6 border-b pb-2">Review Extracted Data</h2>
          
          <div className="grid grid-cols-2 gap-6 mb-8">
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Supplier</label>
              <input 
                type="text" 
                value={extractedData.supplierName} 
                onChange={(e) => setExtractedData({...extractedData, supplierName: e.target.value})}
                className="w-full p-2 border rounded bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Invoice #</label>
              <input 
                type="text" 
                value={extractedData.invoiceNumber} 
                onChange={(e) => setExtractedData({...extractedData, invoiceNumber: e.target.value})}
                className="w-full p-2 border rounded bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Date</label>
              <input 
                type="date" 
                value={extractedData.date} 
                onChange={(e) => setExtractedData({...extractedData, date: e.target.value})}
                className="w-full p-2 border rounded bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Total Amount</label>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={extractedData.currency} 
                  onChange={(e) => setExtractedData({...extractedData, currency: e.target.value})}
                  className="w-20 p-2 border rounded bg-slate-50"
                />
                <input 
                  type="number" 
                  value={extractedData.totalAmount} 
                  onChange={(e) => setExtractedData({...extractedData, totalAmount: parseFloat(e.target.value)})}
                  className="flex-1 p-2 border rounded bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
          </div>

          <h3 className="font-semibold mb-3 text-slate-700">Line Items</h3>
          <div className="overflow-x-auto mb-8">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-100 text-slate-600 uppercase text-xs">
                <tr>
                  <th className="p-2">Description</th>
                  <th className="p-2 w-20">Qty</th>
                  <th className="p-2 w-32">Unit Price</th>
                  <th className="p-2 w-32">Total</th>
                </tr>
              </thead>
              <tbody>
                {extractedData.lineItems.map((item, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-2">
                      <input 
                        type="text" 
                        value={item.description} 
                        onChange={(e) => {
                          const newItems = [...extractedData.lineItems];
                          newItems[idx].description = e.target.value;
                          setExtractedData({...extractedData, lineItems: newItems});
                        }}
                        className="w-full p-1 border-transparent hover:border-slate-300 focus:border-blue-500 outline-none rounded"
                      />
                    </td>
                    <td className="p-2">
                      <input 
                        type="number" 
                        value={item.quantity} 
                        onChange={(e) => {
                          const newItems = [...extractedData.lineItems];
                          newItems[idx].quantity = parseFloat(e.target.value);
                          setExtractedData({...extractedData, lineItems: newItems});
                        }}
                        className="w-full p-1 border-transparent hover:border-slate-300 focus:border-blue-500 outline-none rounded"
                      />
                    </td>
                    <td className="p-2">
                      <input 
                        type="number" 
                        value={item.unitPrice} 
                        onChange={(e) => {
                          const newItems = [...extractedData.lineItems];
                          newItems[idx].unitPrice = parseFloat(e.target.value);
                          setExtractedData({...extractedData, lineItems: newItems});
                        }}
                        className="w-full p-1 border-transparent hover:border-slate-300 focus:border-blue-500 outline-none rounded"
                      />
                    </td>
                    <td className="p-2 font-medium">
                      {(item.quantity * item.unitPrice).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end gap-4">
            <button 
              onClick={() => { setExtractedData(null); setServerError(null); }}
              className="px-4 py-2 text-slate-600 hover:text-slate-800 font-medium transition-colors"
            >
              Cancel
            </button>
            <button 
              onClick={handleSave}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
            >
              Save as Pending
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadInvoice;
