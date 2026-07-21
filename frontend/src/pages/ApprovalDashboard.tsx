import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';

interface Invoice {
  id: string;
  invoiceNumber: string;
  supplierName: string;
  date: string;
  totalAmount: number;
  currency: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  fileUrl: string | null;
}

type StatusFilter = 'All' | 'Pending' | 'Approved' | 'Rejected';
type SortKey = 'date' | 'amount';
type SortDir = 'asc' | 'desc';

interface SortConfig {
  key: SortKey;
  direction: SortDir;
}

const PAGE_SIZE = 15;

const ApprovalDashboard: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: invoices = [], isLoading: loading } = useQuery<Invoice[]>({
    queryKey: ['invoices'],
    queryFn: async () => {
      const response = await apiClient.get('/invoices');
      return response.data as Invoice[];
    },
  });
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'date', direction: 'desc' });
  const [page, setPage] = useState(1);

  // Reset to page 1 when filter, search, or sort changes
  useEffect(() => {
    setPage(1);
  }, [statusFilter, searchQuery, sortConfig]);

  const handleSort = (key: SortKey) => {
    setSortConfig(prev => {
      if (prev?.key === key) {
        // Toggle direction on same column
        return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' };
      }
      // Start ascending on new column
      return { key, direction: 'asc' };
    });
  };

  const handleStatusChange = async (id: string, status: 'Approved' | 'Rejected') => {
    try {
      await apiClient.patch(`/invoices/${id}/approve`, { status });
      await queryClient.invalidateQueries({ queryKey: ['invoices'] });
    } catch (error) {
      console.error('Failed to update status', error);
      alert('Error updating invoice status');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this invoice?')) return;
    try {
      await apiClient.delete(`/invoices/${id}`);
      await queryClient.invalidateQueries({ queryKey: ['invoices'] });
    } catch (error) {
      console.error('Failed to delete invoice', error);
      alert('Error deleting invoice');
    }
  };

  const handleViewPdf = (fileUrl: string) => {
    window.open(fileUrl, '_blank');
  };

  const counts = {
    Pending: invoices.filter(i => i.status === 'Pending').length,
    Approved: invoices.filter(i => i.status === 'Approved').length,
    Rejected: invoices.filter(i => i.status === 'Rejected').length,
  };

  const visibleInvoices = statusFilter === 'All'
    ? invoices
    : invoices.filter(i => i.status === statusFilter);

  const query = searchQuery.toLowerCase().trim();
  const filteredInvoices = query
    ? visibleInvoices.filter(inv =>
        inv.invoiceNumber.toLowerCase().includes(query) ||
        inv.supplierName.toLowerCase().includes(query) ||
        inv.date.includes(query) ||
        inv.currency.toLowerCase().includes(query) ||
        inv.status.toLowerCase().includes(query) ||
        inv.totalAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).includes(query)
      )
    : visibleInvoices;

  // Apply sort (if configured) before pagination
  const sortedInvoices = [...filteredInvoices].sort((a, b) => {
    if (!sortConfig) return 0;
    const dir = sortConfig.direction === 'asc' ? 1 : -1;
    if (sortConfig.key === 'date') {
      return (new Date(a.date).getTime() - new Date(b.date).getTime()) * dir;
    }
    // amount
    return (a.totalAmount - b.totalAmount) * dir;
  });

  const totalPages = Math.max(1, Math.ceil(sortedInvoices.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * PAGE_SIZE;
  const pageEnd = Math.min(pageStart + PAGE_SIZE, sortedInvoices.length);
  const pageInvoices = sortedInvoices.slice(pageStart, pageEnd);

  const cardClass = (filter: StatusFilter, color: string) =>
    `cursor-pointer p-4 rounded-lg shadow-sm border-2 transition-all ${
      statusFilter === filter
        ? `border-${color}-500 bg-${color}-50`
        : 'border-slate-200 bg-white hover:border-slate-300'
    }`;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6 text-slate-800">Approval Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div
          data-testid="filter-all"
          onClick={() => setStatusFilter('All')}
          className={`cursor-pointer p-4 rounded-lg shadow-sm border-2 transition-all ${
            statusFilter === 'All'
              ? 'border-blue-500 bg-blue-50'
              : 'border-slate-200 bg-white hover:border-slate-300'
          }`}
        >
          <p className="text-xs font-bold text-slate-500 uppercase">All Invoices</p>
          <p className="text-3xl font-bold text-blue-500">{invoices.length}</p>
        </div>
        <div
          data-testid="summary-pending"
          onClick={() => setStatusFilter('Pending')}
          className={cardClass('Pending', 'orange')}
        >
          <p className="text-xs font-bold text-slate-500 uppercase">Pending Review</p>
          <p className="text-3xl font-bold text-orange-500">{counts.Pending}</p>
        </div>
        <div
          data-testid="summary-approved"
          onClick={() => setStatusFilter('Approved')}
          className={cardClass('Approved', 'green')}
        >
          <p className="text-xs font-bold text-slate-500 uppercase">Total Approved</p>
          <p className="text-3xl font-bold text-green-500">{counts.Approved}</p>
        </div>
        <div
          data-testid="summary-rejected"
          onClick={() => setStatusFilter('Rejected')}
          className={cardClass('Rejected', 'red')}
        >
          <p className="text-xs font-bold text-slate-500 uppercase">Total Rejected</p>
          <p className="text-3xl font-bold text-red-500">{counts.Rejected}</p>
        </div>
      </div>

      {/* Search bar */}
      <div className="mb-4">
        <input
          data-testid="search-input"
          type="text"
          placeholder="Search invoices by any field..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="w-full p-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-shadow"
        />
      </div>

      {/* Top pagination bar */}
      {!loading && filteredInvoices.length > 0 && (
        <PaginationBar
          page={safePage}
          totalPages={totalPages}
          pageStart={pageStart + 1}
          pageEnd={pageEnd}
          total={filteredInvoices.length}
          onPrev={() => setPage(safePage - 1)}
          onNext={() => setPage(safePage + 1)}
        />
      )}

      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600 uppercase text-xs">
            <tr>
              <th className="p-4 font-semibold">Invoice #</th>
              <th className="p-4 font-semibold">Supplier</th>
              <th
                data-testid="sort-date"
                onClick={() => handleSort('date')}
                className="p-4 font-semibold cursor-pointer hover:text-slate-900 select-none"
                aria-sort={sortConfig?.key === 'date' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : undefined}
              >
                Date <span className="text-xs ml-0.5">
                  <span className={sortConfig?.key === 'date' && sortConfig.direction === 'asc' ? 'text-blue-600' : 'text-slate-300'}>▲</span>
                  <span className={sortConfig?.key === 'date' && sortConfig.direction === 'desc' ? 'text-blue-600' : 'text-slate-300'}>▼</span>
                </span>
              </th>
              <th
                data-testid="sort-amount"
                onClick={() => handleSort('amount')}
                className="p-4 font-semibold cursor-pointer hover:text-slate-900 select-none"
                aria-sort={sortConfig?.key === 'amount' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : undefined}
              >
                Amount <span className="text-xs ml-0.5">
                  <span className={sortConfig?.key === 'amount' && sortConfig.direction === 'asc' ? 'text-blue-600' : 'text-slate-300'}>▲</span>
                  <span className={sortConfig?.key === 'amount' && sortConfig.direction === 'desc' ? 'text-blue-600' : 'text-slate-300'}>▼</span>
                </span>
              </th>
              <th className="p-4 font-semibold">Status</th>
              <th className="p-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr><td data-testid="loading-indicator" colSpan={6} className="p-8 text-center text-slate-400 italic">Loading invoices...</td></tr>
            ) : pageInvoices.map(inv => (
              <tr key={inv.id} data-testid={`invoice-row-${inv.id}`} className="hover:bg-slate-50 transition-colors">
                <td className="p-4 font-medium text-slate-800">{inv.invoiceNumber}</td>
                <td className="p-4 text-slate-600">{inv.supplierName}</td>
                <td className="p-4 text-slate-600">{inv.date}</td>
                <td className="p-4 font-semibold">{inv.currency} {inv.totalAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                    inv.status === 'Approved' ? 'bg-green-100 text-green-700' :
                    inv.status === 'Rejected' ? 'bg-red-100 text-red-700' :
                    'bg-orange-100 text-orange-700'
                  }`}>
                    {inv.status}
                  </span>
                </td>
                <td className="p-4 text-right">
                  <div className="flex justify-end items-center gap-2">
                    {inv.status === 'Pending' && (
                      <>
                        <button
                          data-testid={`reject-btn-${inv.id}`}
                          onClick={() => handleStatusChange(inv.id, 'Rejected')}
                          className="bg-red-50 hover:bg-red-100 text-red-600 px-3 py-1 rounded text-xs font-bold transition-colors"
                        >
                          Reject
                        </button>
                        <button
                          data-testid={`approve-btn-${inv.id}`}
                          onClick={() => handleStatusChange(inv.id, 'Approved')}
                          className="bg-green-50 hover:bg-green-100 text-green-600 px-3 py-1 rounded text-xs font-bold transition-colors"
                        >
                          Approve
                        </button>
                      </>
                    )}
                    {inv.fileUrl && !inv.fileUrl.startsWith('/uploads/') && (
                      <button
                        data-testid={`view-pdf-btn-${inv.id}`}
                        onClick={() => handleViewPdf(inv.fileUrl as string)}
                        className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title="View PDF"
                        aria-label="View PDF"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                          <line x1="16" y1="13" x2="8" y2="13" />
                          <line x1="16" y1="17" x2="8" y2="17" />
                        </svg>
                      </button>
                    )}
                    <button
                      data-testid={`delete-btn-${inv.id}`}
                      onClick={() => handleDelete(inv.id)}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Delete invoice"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                        <path d="M10 11v6" />
                        <path d="M14 11v6" />
                        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {!loading && filteredInvoices.length === 0 && visibleInvoices.length > 0 && (
              <tr><td colSpan={6} className="p-8 text-center text-slate-400 italic">
                No invoices match &ldquo;{searchQuery}&rdquo;.
              </td></tr>
            )}
            {!loading && visibleInvoices.length === 0 && (
              <tr><td data-testid="empty-state" colSpan={6} className="p-8 text-center text-slate-400 italic">
                {statusFilter === 'All' ? 'No invoices found.' : `No ${statusFilter.toLowerCase()} invoices.`}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Bottom pagination bar */}
      {!loading && filteredInvoices.length > 0 && (
        <PaginationBar
          page={safePage}
          totalPages={totalPages}
          pageStart={pageStart + 1}
          pageEnd={pageEnd}
          total={filteredInvoices.length}
          onPrev={() => setPage(safePage - 1)}
          onNext={() => setPage(safePage + 1)}
        />
      )}

      {statusFilter !== 'All' && (
        <div className="mt-4 text-center">
          <button
            onClick={() => setStatusFilter('All')}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
          >
            ← Show all invoices
          </button>
        </div>
      )}
    </div>
  );
};

/* ── Pagination sub-component ── */
interface PaginationBarProps {
  page: number;
  totalPages: number;
  pageStart: number;
  pageEnd: number;
  total: number;
  onPrev: () => void;
  onNext: () => void;
}

const PaginationBar: React.FC<PaginationBarProps> = ({
  page,
  totalPages,
  pageStart,
  pageEnd,
  total,
  onPrev,
  onNext,
}) => (
  <div className="flex items-center justify-between py-3 px-1 text-sm text-slate-500">
    <span>
      Showing <strong>{pageStart}–{pageEnd}</strong> of <strong>{total}</strong> invoices
    </span>
    <div className="flex gap-2">
      <button
        onClick={onPrev}
        disabled={page <= 1}
        className="px-3 py-1.5 rounded border border-slate-300 text-slate-600 text-xs font-semibold transition-colors hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        ← Previous
      </button>
      <button
        onClick={onNext}
        disabled={page >= totalPages}
        className="px-3 py-1.5 rounded border border-slate-300 text-slate-600 text-xs font-semibold transition-colors hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Next →
      </button>
    </div>
  </div>
);

export default ApprovalDashboard;
