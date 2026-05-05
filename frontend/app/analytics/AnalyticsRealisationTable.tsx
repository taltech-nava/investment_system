'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';
import Card from '@/app/components/Card';
import type { ReportsPageResult } from '@/types/analytics';

interface AnalyticsRealisationTableProps {
  data: ReportsPageResult | null;
  isLoading: boolean;
  onPageChange: (nextPage: number) => void;
}

export default function AnalyticsRealisationTable({
  data,
  isLoading,
  onPageChange,
}: AnalyticsRealisationTableProps) {
  const page = data?.page ?? 1;
  const pageSize = data?.page_size ?? 10;
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <Card
      header={
        <div>
          <h2 className="text-sm font-semibold text-white">Forecast Realisation Log</h2>
          <p className="mt-1 text-xs text-slate-400">
            Detailed audit trail of report rows linked to forecasts, instruments, and publishers.
          </p>
        </div>
      }
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-245 text-sm">
          <thead>
            <tr className="border-b border-slate-700 bg-slate-900/60">
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wide text-slate-400 uppercase">
                Ticker
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wide text-slate-400 uppercase">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wide text-slate-400 uppercase">
                Forecast
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wide text-slate-400 uppercase">
                Realised
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wide text-slate-400 uppercase">
                Error %
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wide text-slate-400 uppercase">
                Publisher
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wide text-slate-400 uppercase">
                Entry Mode
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wide text-slate-400 uppercase">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/70">
            {isLoading && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                  Loading report rows...
                </td>
              </tr>
            )}

            {!isLoading && (!data || data.items.length === 0) && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                  No report rows found for this filter.
                </td>
              </tr>
            )}

            {!isLoading &&
              data?.items.map((row) => (
                <tr key={row.report_id} className="transition-colors hover:bg-slate-900/40">
                  <td className="px-4 py-3 font-mono font-semibold text-blue-300">{row.ticker}</td>
                  <td className="px-4 py-3 text-slate-300">{row.review_date}</td>
                  <td className="px-4 py-3 text-slate-200">{formatCurrency(row.forecast_price)}</td>
                  <td className="px-4 py-3 text-slate-200">{formatCurrency(row.realised_price)}</td>
                  <td className="px-4 py-3">
                    <span className={getErrorBadgeClass(row.error_percent)}>
                      {formatSignedPercent(row.error_percent)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{row.publisher_name ?? 'Unknown'}</td>
                  <td className="px-4 py-3 text-slate-300">{row.method ?? 'N/A'}</td>
                  <td className="px-4 py-3 text-slate-500">-</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex flex-col gap-3 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">
        <span>
          Page {page} of {totalPages} · {total} total rows
        </span>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onPageChange(page - 1)}
            disabled={isLoading || page <= 1}
            className="inline-flex items-center gap-1 rounded border border-slate-700 px-3 py-1.5 text-slate-200 transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ChevronLeft size={14} /> Prev
          </button>
          <button
            type="button"
            onClick={() => onPageChange(page + 1)}
            disabled={isLoading || page >= totalPages}
            className="inline-flex items-center gap-1 rounded border border-slate-700 px-3 py-1.5 text-slate-200 transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </Card>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value);
}

function formatSignedPercent(value: number): string {
  const fixed = value.toFixed(2);
  return value > 0 ? `+${fixed}%` : `${fixed}%`;
}

function getErrorBadgeClass(errorPercent: number): string {
  if (Math.abs(errorPercent) <= 2) {
    return 'rounded-full bg-emerald-300/20 px-2.5 py-1 text-xs font-semibold text-emerald-300';
  }
  if (Math.abs(errorPercent) <= 5) {
    return 'rounded-full bg-amber-300/20 px-2.5 py-1 text-xs font-semibold text-amber-300';
  }
  return 'rounded-full bg-rose-300/20 px-2.5 py-1 text-xs font-semibold text-rose-300';
}
