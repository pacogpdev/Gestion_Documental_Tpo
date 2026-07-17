import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import apiClient from '../api/client';
import { useAuth } from '../hooks/useAuth';

interface MonthlyAmount {
  month: string;
  amount: number;
}

interface TopLineItem {
  description: string;
  totalAmount: number;
  invoiceCount: number;
}

interface StatusDistribution {
  Approved: number;
  Rejected: number;
  Pending: number;
}

interface SupplierStats {
  supplierName: string;
  taxId: string;
  totalInvoices: number;
  annualTotal: number;
  annualPercentage: number;
  grandTotal: number;
  monthlyAmounts: MonthlyAmount[];
  topLineItems: TopLineItem[];
  statusDistribution: StatusDistribution;
  averageInvoiceAmount: number;
  topInvoice: { invoiceNumber: string; amount: number } | null;
}

interface SupplierStatsApiResponse {
  supplierName?: string;
  taxId?: string;
  totalInvoices?: number;
  totalAmount?: number;
  annualTotal?: number;
  annualAccumulated?: number;
  annualPercentage?: number;
  grandTotal?: number;
  grandTotalAllSuppliers?: number;
  monthlyAmounts?: MonthlyAmount[];
  topLineItems?: TopLineItem[];
  statusDistribution?: StatusDistribution;
  averageInvoiceAmount?: number;
  topInvoice?: { number?: string; invoiceNumber?: string; amount: number } | null;
}

const CHART_COLORS = ['#22c55e', '#ef4444', '#f59e0b'];

const formatAmount = (amount: number) =>
  amount.toLocaleString('en-US', { maximumFractionDigits: 2 });

const normalizeStats = (response: SupplierStatsApiResponse): SupplierStats => ({
  supplierName: response.supplierName || 'Supplier',
  taxId: response.taxId || '',
  totalInvoices: response.totalInvoices || 0,
  annualTotal: response.annualTotal ?? response.annualAccumulated ?? response.totalAmount ?? 0,
  annualPercentage: response.annualPercentage || 0,
  grandTotal: response.grandTotal ?? response.grandTotalAllSuppliers ?? 0,
  monthlyAmounts: response.monthlyAmounts || [],
  topLineItems: response.topLineItems || [],
  statusDistribution: response.statusDistribution || { Approved: 0, Rejected: 0, Pending: 0 },
  averageInvoiceAmount: response.averageInvoiceAmount || 0,
  topInvoice: response.topInvoice
    ? {
        invoiceNumber: response.topInvoice.invoiceNumber || response.topInvoice.number || '',
        amount: response.topInvoice.amount,
      }
    : null,
});

const SupplierDashboard: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const canViewStats = hasRole('Admin') || hasRole('Approver');
  const [stats, setStats] = useState<SupplierStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!canViewStats) {
      setLoading(false);
      return;
    }

    const fetchStats = async () => {
      try {
        const response = await apiClient.get(`/suppliers/${id}/stats`);
        setStats(normalizeStats(response.data));
      } catch (requestError: any) {
        const detail = requestError?.response?.data?.detail;
        setError(detail || 'Unable to load supplier statistics.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [id, canViewStats]);

  const statusData = useMemo(() => {
    if (!stats) return [];
    return [
      { name: 'Approved', value: stats.statusDistribution.Approved },
      { name: 'Rejected', value: stats.statusDistribution.Rejected },
      { name: 'Pending', value: stats.statusDistribution.Pending },
    ];
  }, [stats]);

  const shareData = useMemo(() => {
    if (!stats) return [];
    return [
      { name: stats.supplierName, value: Math.max(0, stats.annualPercentage) },
      { name: 'Other suppliers', value: Math.max(0, 100 - stats.annualPercentage) },
    ];
  }, [stats]);

  if (!canViewStats) {
    return <div role="alert" className="max-w-5xl mx-auto p-6 text-red-600">You do not have permission to view supplier statistics.</div>;
  }

  if (loading) {
    return <div data-testid="dashboard-loading" className="max-w-6xl mx-auto p-6 text-slate-500">Loading...</div>;
  }

  if (error || !stats) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <button
          type="button"
          onClick={() => navigate('/suppliers')}
          aria-label="Back to Suppliers"
          className="mb-6 text-blue-600 hover:text-blue-800 font-medium"
        >
          ← Back to Suppliers
        </button>
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          {error || 'Unable to load supplier statistics.'}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={() => navigate('/suppliers')}
          aria-label="Back to Suppliers"
          className="self-start text-blue-600 hover:text-blue-800 font-medium"
        >
          ← Back to Suppliers
        </button>
        <div className="sm:text-right">
          <h1 className="text-2xl font-bold text-slate-800">{stats.supplierName} Dashboard</h1>
          <p className="text-sm text-slate-500">Tax ID: {stats.taxId}</p>
        </div>
      </header>

      <section aria-label="Supplier KPIs" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard testId="kpi-annual-total" label="Annual total" value={formatAmount(stats.annualTotal)} />
        <KpiCard testId="kpi-annual-percentage" label="Share of total" value={`${formatAmount(stats.annualPercentage)}%`} />
        <KpiCard testId="kpi-average-invoice" label="Average invoice" value={formatAmount(stats.averageInvoiceAmount)} />
        <KpiCard testId="kpi-invoice-count" label="Invoice count" value={formatAmount(stats.totalInvoices)} />
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard testId="monthly-chart" title="Monthly billing">
          {stats.monthlyAmounts.length === 0 ? (
            <EmptyChart testId="monthly-empty" message="No monthly billing data" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={stats.monthlyAmounts} aria-label="Monthly billing chart">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="amount" stroke="#3b82f6" fill="#93c5fd" name="Amount" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard testId="supplier-share-chart" title="Supplier share">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart aria-label="Supplier share chart">
                <Pie data={shareData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={105} label={(entry: any) => `${entry.value.toFixed(1)}%`}>
                {shareData.map((entry, index) => <Cell key={entry.name} fill={index === 0 ? '#3b82f6' : '#cbd5e1'} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard testId="status-chart" title="Status distribution">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart aria-label="Status distribution chart">
              <Pie data={statusData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={105} label>
                {statusData.map((entry, index) => <Cell key={entry.name} fill={CHART_COLORS[index]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard testId="items-chart" title="Top 10 line items">
          {stats.topLineItems.length === 0 ? (
            <EmptyChart testId="items-empty" message="No line item data" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats.topLineItems} layout="vertical" margin={{ left: 20, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="description" width={120} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="totalAmount" fill="#22c55e" name="Amount" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>
    </div>
  );
};

const KpiCard = ({ testId, label, value }: { testId: string; label: string; value: string }) => (
  <div data-testid={testId} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
    <p className="text-xs font-bold uppercase text-slate-500">{label}</p>
    <p className="mt-2 text-2xl font-bold text-slate-800">{value}</p>
  </div>
);

const ChartCard = ({ testId, title, children }: { testId: string; title: string; children: React.ReactNode }) => (
  <section data-testid={testId} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
    <h2 className="mb-4 text-lg font-semibold text-slate-800">{title}</h2>
    {children}
  </section>
);

const EmptyChart = ({ testId, message }: { testId: string; message: string }) => (
  <div data-testid={testId} className="flex h-[300px] items-center justify-center text-sm italic text-slate-400">
    {message}
  </div>
);

export default SupplierDashboard;
