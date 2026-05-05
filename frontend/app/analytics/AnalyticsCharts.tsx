'use client';

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { BarChart3, Clock3, TrendingDown, TrendingUp } from 'lucide-react';
import Card from '@/app/components/Card';
import type { DistributionResult } from '@/types/analytics';

interface AnalyticsChartsProps {
  distribution: DistributionResult;
}

export default function AnalyticsCharts({ distribution }: AnalyticsChartsProps) {
  const totalAll = distribution.all.reduce((sum, count) => sum + count, 0);
  const totalSelected = distribution.selected.reduce((sum, count) => sum + count, 0);

  const meanAll = distribution.mean_all;
  const meanSelected = distribution.mean_selected;
  const meanDelta =
    meanAll !== null && meanSelected !== null ? Number((meanSelected - meanAll).toFixed(4)) : null;
  const isBullishMae = meanDelta !== null && meanDelta <= 0;

  const chartData = distribution.all.map((allCount, index) => {
    const selectedCount = distribution.selected[index] ?? 0;
    const from = distribution.bins[index];
    const to = distribution.bins[index + 1];

    return {
      range: `${formatSignedPercent(from)} to ${formatSignedPercent(to)}`,
      all: allCount,
      selected: selectedCount,
    };
  });

  return (
    <div className="mt-8 flex flex-col gap-5">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium tracking-wide text-slate-400 uppercase">
                Mean Absolute Error
              </p>
              <p className="mt-2 text-2xl font-semibold text-white">
                {formatNullablePercent(meanSelected)}
              </p>
            </div>

            <div className="rounded-xl bg-slate-100 p-2 text-slate-900">
              {isBullishMae ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-4">
          <p className="text-xs font-medium tracking-wide text-slate-400 uppercase">
            Directional Accuracy
          </p>
          <p className="mt-2 text-2xl font-semibold text-white">-</p>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-4">
          <p className="text-xs font-medium tracking-wide text-slate-400 uppercase">
            Avg. Conviction Gap
          </p>
          <p className={`mt-2 text-2xl font-semibold`}>-</p>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium tracking-wide text-slate-400 uppercase">
                Realised Samples
              </p>
              <p className="mt-2 text-2xl font-semibold text-white">{totalSelected}</p>
            </div>

            <div className="rounded-xl bg-slate-100 p-2 text-blue-600">
              <Clock3 size={16} />
            </div>
          </div>
        </div>
      </div>

      <Card
        header={
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 size={15} className="text-blue-400" />
              <span className="text-sm font-semibold text-white">Error Distribution (20 bins)</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">
              Line comparison of selected filter versus all forecasts across signed error bins.
            </p>
          </div>
        }
      >
        <div className="mb-4 flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <span className="h-2.5 w-2.5 rounded-full bg-blue-500" />
            <span>All forecasts ({totalAll})</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
            <span>Selected ({totalSelected})</span>
          </div>
        </div>

        <div className="h-96 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 18, left: 0, bottom: 56 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(51 65 85)" />
              <XAxis
                dataKey="range"
                stroke="rgb(148 163 184)"
                tick={{ fontSize: 10 }}
                interval={1}
                angle={-35}
                textAnchor="end"
                height={60}
              />
              <YAxis stroke="rgb(148 163 184)" tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgb(15 23 42)',
                  border: '1px solid rgb(51 65 85)',
                  borderRadius: 8,
                  color: 'rgb(226 232 240)',
                }}
                labelStyle={{ color: 'rgb(148 163 184)' }}
              />
              <Line
                type="monotone"
                dataKey="all"
                name="All"
                stroke="rgb(59 130 246)"
                strokeWidth={2.5}
                dot={{ r: 2 }}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="selected"
                name="Selected"
                stroke="rgb(52 211 153)"
                strokeWidth={2.5}
                dot={{ r: 2 }}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}

function formatSignedPercent(value: number): string {
  const scaled = Math.round(value * 100);
  if (scaled > 0) return `+${scaled}%`;
  return `${scaled}%`;
}

function formatNullablePercent(value: number | null, alwaysSigned = false): string {
  if (value === null) return 'N/A';
  const scaled = (value * 100).toFixed(2);
  if (alwaysSigned && value > 0) return `+${scaled}%`;
  return `${scaled}%`;
}
