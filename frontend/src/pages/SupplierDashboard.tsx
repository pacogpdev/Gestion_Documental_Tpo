import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Text,
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
  currency: string;
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
  currency?: string;
  monthlyAmounts?: MonthlyAmount[];
  topLineItems?: TopLineItem[];
  statusDistribution?: StatusDistribution;
  averageInvoiceAmount?: number;
  topInvoice?: { number?: string; invoiceNumber?: string; amount: number } | null;
}

const CHART_COLORS = ['#22c55e', '#ef4444', '#f59e0b'];
const KPI_COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b', '#22c55e', '#ec4899'];

const CURRENCY_SYMBOLS: Record<string, string> = { EUR: '\u20AC', USD: '$', GBP: '\u00A3' };

const currencySymbol = (currency: string) => CURRENCY_SYMBOLS[currency] || currency + ' ';

const formatMoney = (amount: number, currency: string) =>
  `${currencySymbol(currency)}${amount.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;

const formatCompactMoney = (value: number, currency: string) => {
  if (value >= 1000) return `${currencySymbol(currency)}${(value / 1000).toFixed(0)}k`;
  return `${currencySymbol(currency)}${value.toFixed(0)}`;
};

const truncate = (text: string, max: number = 25) =>
  text.length > max ? `${text.slice(0, max)}\u2026` : text;

const normalizeStats = (response: SupplierStatsApiResponse): SupplierStats => ({
  supplierName: response.supplierName || 'Supplier',
  taxId: response.taxId || '',
  totalInvoices: response.totalInvoices || 0,
  annualTotal: response.annualTotal ?? response.annualAccumulated ?? response.totalAmount ?? 0,
  annualPercentage: response.annualPercentage || 0,
  grandTotal: response.grandTotal ?? response.grandTotalAllSuppliers ?? 0,
  currency: response.currency || 'EUR',
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
      { name: `Approved: ${stats.statusDistribution.Approved}`, value: stats.statusDistribution.Approved, color: CHART_COLORS[0] },
      { name: `Rejected: ${stats.statusDistribution.Rejected}`, value: stats.statusDistribution.Rejected, color: CHART_COLORS[1] },
      { name: `Pending: ${stats.statusDistribution.Pending}`, value: stats.statusDistribution.Pending, color: CHART_COLORS[2] },
    ];
  }, [stats]);

  const shareData = useMemo(() => {
    if (!stats) return [];
    return [
      { name: stats.supplierName, value: Math.max(0, stats.annualPercentage), color: '#3b82f6' },
      { name: 'Other suppliers', value: Math.max(0, 100 - stats.annualPercentage), color: '#cbd5e1' },
    ];
  }, [stats]);

  const topItemsTruncated = useMemo(() => {
    if (!stats) return [];
    return stats.topLineItems.map((item) => ({
      ...item,
      shortDescription: truncate(item.description),
    }));
  }, [stats]);

  const isActive = stats && stats.totalInvoices > 0;

  if (!canViewStats) {
    return <div role="alert" className="max-w-5xl mx-auto p-6 text-red-600">You do not have permission to view supplier statistics.</div>;
  }

  if (loading) {
    return (
      <div data-testid="dashboard-loading" className="max-w-6xl mx-auto p-6">
        <div className="flex items-center gap-3 text-slate-500">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600"></div>
          Loading supplier statistics...
        </div>
      </div>
    );
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
          <span className="font-extrabold">{'\u2190'}</span> Back to Suppliers
        </button>
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          {error || 'Unable to load supplier statistics.'}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header with badges */}
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={() => navigate('/suppliers')}
          aria-label="Back to Suppliers"
          className="self-start text-blue-600 hover:text-blue-800 font-medium"
        >
          <span className="font-extrabold">{'\u2190'}</span> Back to Suppliers
        </button>
        <div className="sm:text-right">
          <div className="flex items-center gap-2 justify-end">
            <h1 className="text-2xl font-bold text-slate-800">{stats.supplierName}</h1>
            <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
              {stats.totalInvoices} invoices
            </span>
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${isActive ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'}`}>
              {isActive ? 'Active' : 'No activity'}
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">Tax ID: {stats.taxId}</p>
        </div>
      </header>

      {/* KPI Cards with colored top border */}
      <section aria-label="Supplier KPIs" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <KpiCard testId="kpi-annual-total" label="Annual total" value={formatMoney(stats.annualTotal, stats.currency)} accentColor={KPI_COLORS[0]} icon="\u20AC" />
        <KpiCard testId="kpi-annual-percentage" label="Share of total" value={`${stats.annualPercentage.toFixed(1)}%`} accentColor={KPI_COLORS[1]} icon="%" />
        <KpiCard testId="kpi-average-invoice" label="Average invoice" value={formatMoney(stats.averageInvoiceAmount, stats.currency)} accentColor={KPI_COLORS[2]} icon="\u00F7" />
        <KpiCard testId="kpi-invoice-count" label="Invoice count" value={`${stats.totalInvoices}`} accentColor={KPI_COLORS[3]} icon="#" />
        <KpiCard
          testId="kpi-top-invoice"
          label="Top invoice"
          value={stats.topInvoice ? formatMoney(stats.topInvoice.amount, stats.currency) : '\u2014'}
          subValue={stats.topInvoice?.invoiceNumber}
          accentColor={KPI_COLORS[4]}
          icon="\u2605"
        />
      </section>

      {/* Monthly billing — full width with gradient */}
      <ChartCard testId="monthly-chart" title="Monthly billing (trailing 12 months)">
        {stats.monthlyAmounts.length === 0 ? (
          <EmptyChart testId="monthly-empty" message="No monthly billing data" />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={stats.monthlyAmounts} aria-label="Monthly billing chart">
              <defs>
                <linearGradient id="monthlyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#64748b' }} />
              <YAxis tickFormatter={(v: number) => formatCompactMoney(v, stats.currency)} tick={{ fontSize: 12, fill: '#64748b' }} />
              <Tooltip formatter={(value: number) => [formatMoney(value, stats.currency), 'Amount']} />
              <Area type="monotone" dataKey="amount" stroke="#3b82f6" strokeWidth={2} fill="url(#monthlyGradient)" name="Amount" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      {/* Supplier share + Status — side by side */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard testId="supplier-share-chart" title="Supplier share of total">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart aria-label="Supplier share chart">
              <Pie
                data={shareData}
                dataKey="value"
                nameKey="name"
                innerRadius={75}
                outerRadius={100}
                label={(entry: any) => `${entry.value.toFixed(1)}%`}
                labelLine={false}
              >
                {shareData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard testId="status-chart" title="Status distribution">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart aria-label="Status distribution chart">
              <Pie
                data={statusData}
                dataKey="value"
                nameKey="name"
                innerRadius={75}
                outerRadius={100}
                label
              >
                {statusData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>

      {/* Top 10 items — full width with amounts on bars */}
      <ChartCard testId="items-chart" title="Top 10 line items by total amount">
        {stats.topLineItems.length === 0 ? (
          <EmptyChart testId="items-empty" message="No line item data" />
        ) : (
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={topItemsTruncated} layout="vertical" margin={{ left: 10, right: 60, top: 5, bottom: 5 }}>
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#60a5fa" stopOpacity={0.7} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
              <XAxis type="number" tickFormatter={(v: number) => formatCompactMoney(v, stats.currency)} tick={{ fontSize: 12, fill: '#64748b' }} />
              <YAxis
                type="category"
                dataKey="shortDescription"
                width={140}
                tick={{ fontSize: 11, fill: '#475569' }}
              />
              <Tooltip
                formatter={(value: number) => [formatMoney(value, stats.currency), 'Amount']}
                labelFormatter={(_label: string, payload: any) => payload?.[0]?.payload?.description || _label}
              />
              <Bar dataKey="totalAmount" fill="url(#barGradient)" name="Amount" radius={[0, 4, 4, 0]}>
                <LabelList
                  dataKey="totalAmount"
                  position="right"
                  formatter={(value: number) => formatMoney(value, stats.currency)}
                  style={{ fontSize: 11, fill: '#475569' }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </div>
  );
};

const KpiCard = ({
  testId,
  label,
  value,
  subValue,
  accentColor,
  icon,
}: {
  testId: string;
  label: string;
  value: string;
  subValue?: string;
  accentColor: string;
  icon: string;
}) => (
  <div
    data-testid={testId}
    className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm"
  >
    <div className="h-1" style={{ backgroundColor: accentColor }} />
    <div className="p-4">
      <div className="flex items-center gap-2">
        <span
          className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white"
          style={{ backgroundColor: accentColor }}
        >
          {icon}
        </span>
        <p className="text-xs font-bold uppercase text-slate-500">{label}</p>
      </div>
      <p className="mt-2 text-xl font-bold text-slate-800">{value}</p>
      {subValue && <p className="mt-0.5 text-xs text-slate-400">{subValue}</p>}
    </div>
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
