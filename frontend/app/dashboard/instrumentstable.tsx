'use client';

import { useState } from 'react';
import React from 'react';

interface Instrument {
  id: number;
  ticker: string;
  name: string;
  currency: string;
  class_id: number;
}

interface Source {
  id: number;
  publisher_id: number | null;
  title: string | null;
  file_path: string | null;
  snippet_text: string | null;
  search_subjects: string[] | null;
}

interface Forecasts {
  id: number;
  instrument_id: number | null;
  publisher_id: number | null;
  prediction_date: string | null;
  maturation_date: string | null;
  predicted_price: number;
  method: string | null;
}

interface Publishers {
  id: number;
  title: string | null;
}

interface Props {
  instruments: Instrument[];
  sources: Source[];
  forecasts: Forecasts[];
  publishers: Publishers[];
}

const formatPrice = (value: number, currency: string) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 4,
  }).format(value);


function ExpandedForecastRows({ forecasts, currency, publishers }: { forecasts: Forecasts[], currency: string, publishers: Publisher[] }) {
  return forecasts.map(f => (
    <tr key={f.id} className="bg-slate-800">
      <td />
      <td className="px-5 py-2 text-slate-400">{formatPrice(f.predicted_price, currency)}</td>
      <td className="px-5 py-2 text-slate-400">{f.maturation_date ?? '—'}</td>
      <td className="px-5 py-2 text-slate-400">{f.method ?? '—'}</td>
      <td className="px-5 py-2 text-slate-400">
        {f.publisher_id ? publishers.find(p => p.id === f.publisher_id)?.institution ?? '—' : '—'}
      </td>
      <td /><td /><td />
    </tr>
  ));
}

function ExpandedSourceRows({ sources }: { sources: Source[] }) {
  return sources.map(s => (
    <tr key={s.id} className="bg-slate-800">
      <td /><td /><td /><td /><td /><td />
      <td className="px-5 py-2 text-slate-400">
        {s.file_path ? (
          <a href={s.file_path} target="_blank" className="hover:underline text-blue-400">
            {s.title ?? s.file_path}
          </a>
        ) : (s.title ?? '—')}
      </td>
    </tr>
  ));
}

export default function InstrumentsTable({ instruments, sources, forecasts, publishers }: Props) {
  const [expandedSourceId, setExpandedSourceId] = useState<number | null>(null);
  const [expandedForecastId, setExpandedForecastId] = useState<number | null>(null);
  const [methodFilter, setMethodFilter] = useState<'all' | 'sellside' | 'llm' | 'manual'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active'>('all');



  const getMethodType = (method?: string | null) => {
    if (!method) return 'unknown';
    const m = method.toLowerCase();
    if (m.includes('llm')) return 'llm';
    if (m.includes('manual')) return 'manual';
    return 'sellside';
  };

  const today = new Date().toISOString().split('T')[0]; // 'YYYY-MM-DD'

  const filteredInstruments = instruments.filter((instrument) => {
    if (statusFilter === 'all') return true;

    // Active = at least one forecast with maturation_date > today
    return forecasts.some(
      (f) =>
        f.instrument_id === instrument.id &&
        f.maturation_date != null &&
        f.maturation_date > today
    );
  });

  return (
    <div className="overflow-hidden rounded-xl border border-slate-700 bg-slate-900">

      {/* Header + filters */}
      <div className="border-b border-slate-700 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h2 className="text-sm font-semibold text-white">Instruments</h2>
            <p className="mt-0.5 text-xs text-slate-400">{filteredInstruments.length} tracked</p>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as 'all' | 'active')}
            className="text-sm border border-slate-700 rounded-md px-2 py-1 bg-slate-800 text-slate-300"
          >
            <option value="all">All</option>
            <option value="active">Active</option>
          </select>

          <div className="w-3" />

          <p className="text-xs text-slate-400">Method</p>

          <select
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value as any)}
            className="text-sm border border-slate-700 rounded-md px-2 py-1 bg-slate-800 text-slate-300"
          >
            <option value="all">All</option>
            <option value="sellside">Sellside</option>
            <option value="llm">LLM</option>
            <option value="manual">Manual</option>
          </select>
        </div>
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700 bg-slate-800">
            <th className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Ticker</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Predicted Price</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Maturation</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Method</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Publisher</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Bull • Bear case</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Research</th>
          </tr>
        </thead>

        <tbody className="divide-y divide-slate-700">
          {filteredInstruments.map((instrument) => {

            const instrumentSources = sources.filter(s =>
              s.search_subjects?.includes(instrument.ticker)
            );

            const filteredForecasts = forecasts.filter(f => {
              if (f.instrument_id !== instrument.id) return false;
              if (methodFilter === 'all') return true;
              return getMethodType(f.method) === methodFilter;
            });

            const sortedForecasts = [...filteredForecasts].sort((a, b) =>
              (b.prediction_date ?? '').localeCompare(a.prediction_date ?? '')
            );

            const latestForecast = sortedForecasts[0];
            const restForecasts = sortedForecasts.slice(1);

            const prices = sortedForecasts.map(f => f.predicted_price);
            const bullPrice = prices.length ? Math.max(...prices) : null;
            const bearPrice = prices.length ? Math.min(...prices) : null;

            const isForecastExpanded = expandedForecastId === instrument.id;
            const isSourceExpanded = expandedSourceId === instrument.id;

            return (
              <React.Fragment key={instrument.id}>
                <tr className="hover:bg-slate-800/50">

                  {/* Ticker */}
                  <td className="px-5 py-3">
                    <div className="font-mono text-blue-400">{instrument.ticker}</div>
                    <div className="text-[10px] text-slate-500">{instrument.name}</div>
                  </td>

                  {/* Price */}
                  <td className="px-5 py-3 text-slate-200">
                    {latestForecast ? formatPrice(latestForecast.predicted_price, instrument.currency) : '—'}
                    {restForecasts.length > 0 && (
                      <button
                        onClick={() => setExpandedForecastId(isForecastExpanded ? null : instrument.id)}
                        className="ml-2 text-xs text-blue-400 hover:text-blue-300"
                      >
                        {isForecastExpanded ? 'hide' : `+${restForecasts.length}`}
                      </button>
                    )}
                  </td>

                  {/* Maturation */}
                  <td className="px-5 py-3 text-slate-400">
                    {latestForecast?.maturation_date ?? '—'}
                  </td>

                  {/* Method */}
                  <td className="px-5 py-3 text-slate-400">
                    {latestForecast?.method ?? '—'}
                  </td>

                  {/* Publisher */}
                  <td className="px-5 py-3 text-slate-400">
                    {latestForecast?.publisher_id
                      ? publishers.find(p => p.id === latestForecast.publisher_id)?.institution ?? '—'
                      : '—'}
                  </td>

                  {/* Bull / Bear */}
                  <td className="px-5 py-3">
                    {bullPrice !== null && bearPrice !== null ? (
                      <div className="flex items-center gap-1">
                        <span className="text-green-400">
                          {formatPrice(bullPrice, instrument.currency)}
                        </span>
                        <span className="text-slate-600">•</span>
                        <span className="text-red-400">
                          {formatPrice(bearPrice, instrument.currency)}
                        </span>
                      </div>
                    ) : '—'}
                  </td>

                  {/* Research */}
                  <td className="px-5 py-3 text-slate-400">
                    {instrumentSources[0] ? (
                      instrumentSources[0].file_path ? (
                        <a href={instrumentSources[0].file_path} target="_blank" className="hover:underline text-blue-400">
                          {instrumentSources[0].title ?? instrumentSources[0].file_path}
                        </a>
                      ) : (instrumentSources[0].title ?? '—')
                    ) : '—'}
                    {instrumentSources.length > 1 && (
                      <button
                        onClick={() => setExpandedSourceId(isSourceExpanded ? null : instrument.id)}
                        className="ml-2 text-xs text-blue-400 hover:text-blue-300"
                      >
                        {isSourceExpanded ? 'hide' : `+${instrumentSources.length - 1}`}
                      </button>
                    )}
                  </td>
                </tr>

                  {/* Expanded forecasts */}
                  {isForecastExpanded && <ExpandedForecastRows forecasts={restForecasts} currency={instrument.currency} publishers={publishers}/>}

                  {/* Expanded sources */}
                  {isSourceExpanded && <ExpandedSourceRows sources={instrumentSources.slice(1)} />}

              </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}