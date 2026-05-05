'use client';

import { useMemo, useState } from 'react';
import MenuItem from '@mui/material/MenuItem';
import { Search, Database } from 'lucide-react';
import Card from '@/app/components/Card';
import DarkAutocomplete from '@/app/components/DarkAutocomplete';
import DarkSelect from '@/app/components/DarkSelect';
import { clientApiFetch } from '@/lib/api';
import type { DistributionResult, ReportsPageResult } from '@/types/analytics';
import type { Instrument, InstrumentClass } from '@/types/instruments';
import type { Publisher } from '@/types/publishers';
import AnalyticsCharts from './AnalyticsCharts';
import AnalyticsRealisationTable from './AnalyticsRealisationTable';

interface AnalyticsFiltersProps {
  instrumentClasses: InstrumentClass[];
  instruments: Instrument[];
  publishers: Publisher[];
}

export default function AnalyticsFilters({
  instrumentClasses,
  instruments,
  publishers,
}: AnalyticsFiltersProps) {
  const PAGE_SIZE = 8;

  const [classId, setClassId] = useState<string>('');
  const [selectedInstrument, setSelectedInstrument] = useState<Instrument | null>(null);
  const [selectedPublisher, setSelectedPublisher] = useState<Publisher | null>(null);
  const [distribution, setDistribution] = useState<DistributionResult | null>(null);
  const [reportsPage, setReportsPage] = useState<ReportsPageResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingReports, setIsLoadingReports] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filteredInstruments = useMemo(() => {
    if (!classId) return instruments;
    return instruments.filter((instrument) => instrument.class_id === Number(classId));
  }, [classId, instruments]);

  const hasActiveFilter = useMemo(
    () => Boolean(selectedInstrument || selectedPublisher),
    [selectedInstrument, selectedPublisher],
  );

  const activeFilterLabel = useMemo(() => {
    if (selectedInstrument) {
      return `ticker ${selectedInstrument.ticker}`;
    }
    if (selectedPublisher) {
      return `publisher ${selectedPublisher.institution ?? `#${selectedPublisher.id}`}`;
    }
    return null;
  }, [selectedInstrument, selectedPublisher]);

  function buildFilterParams(): URLSearchParams {
    const params = new URLSearchParams();
    if (selectedInstrument) {
      params.set('ticker', selectedInstrument.ticker);
    }
    if (selectedPublisher) {
      params.set('publisher_id', String(selectedPublisher.id));
    }
    return params;
  }

  async function fetchReportsPage(page: number) {
    if (!hasActiveFilter) {
      return;
    }

    setIsLoadingReports(true);
    try {
      const params = buildFilterParams();
      params.set('page', String(page));
      params.set('page_size', String(PAGE_SIZE));
      const reportRows = await clientApiFetch<ReportsPageResult>(
        `/analytics/reports?${params.toString()}`,
      );
      setReportsPage(reportRows);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch analytics report rows';
      setError(message);
    } finally {
      setIsLoadingReports(false);
    }
  }

  async function fetchAnalyticsData() {
    if (!selectedInstrument && !selectedPublisher) {
      setError('Select either an instrument or a publisher before fetching analytics.');
      return;
    }

    if (selectedInstrument && selectedPublisher) {
      setError('Choose only one filter: instrument or publisher.');
      return;
    }

    setIsLoading(true);
    setIsLoadingReports(true);
    setError(null);

    const baseParams = buildFilterParams();
    const distributionQuery = baseParams.toString();
    const reportParams = new URLSearchParams(baseParams);
    reportParams.set('page', '1');
    reportParams.set('page_size', String(PAGE_SIZE));

    try {
      const [distributionResult, reportRows] = await Promise.all([
        clientApiFetch<DistributionResult>(`/analytics/distribution?${distributionQuery}`),
        clientApiFetch<ReportsPageResult>(`/analytics/reports?${reportParams.toString()}`),
      ]);
      setDistribution(distributionResult);
      setReportsPage(reportRows);
      console.log('Analytics distribution result:', distributionResult);
      console.log('Analytics report rows:', reportRows);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch analytics data';
      setError(message);
    } finally {
      setIsLoading(false);
      setIsLoadingReports(false);
    }
  }

  return (
    <div className="mb-6">
      <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-x-2">
        <div>
          <h1 className="text-2xl font-semibold text-white">Performance Analytics</h1>
          <p className="mt-1 text-sm text-slate-400">
            Compare distribution outcomes for either a specific instrument or a publisher.
          </p>
        </div>
      </div>

      <div className="mb-16 h-px w-full bg-slate-800" />

      <Card
        header={
          <div>
            <div className="flex items-center gap-2">
              <Search size={15} className="text-blue-400" />
              <span className="text-sm font-semibold text-white">Analytics Filters</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">
              Select either publisher or ticker, then load both distribution and detailed report
              rows.
            </p>
          </div>
        }
      >
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-300">Publisher Name</label>
            <DarkAutocomplete<Publisher>
              options={publishers}
              getOptionLabel={(publisher) => publisher.institution ?? 'Unnamed publisher'}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              value={selectedPublisher}
              onChange={(_, publisher) => {
                setSelectedPublisher(publisher);
                if (publisher) {
                  setSelectedInstrument(null);
                  setDistribution(null);
                  setReportsPage(null);
                }
              }}
              filterOptions={(options, { inputValue }) =>
                options.filter((publisher) =>
                  (publisher.institution ?? '').toLowerCase().includes(inputValue.toLowerCase()),
                )
              }
              renderOption={({ key, ...optionProps }, option) => (
                <li key={key} {...optionProps} style={{ gap: '8px', fontSize: '0.875rem' }}>
                  <span
                    style={{
                      color: 'rgb(96 165 250)',
                      flexShrink: 0,
                    }}
                  >
                    #{option.id}
                  </span>
                  <span
                    style={{
                      color: 'rgb(148 163 184)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {option.institution ?? 'Unnamed publisher'}
                  </span>
                </li>
              )}
              placeholder="Search publisher"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-300">Asset Class</label>
            <DarkSelect
              value={classId}
              onChange={(event) => {
                const value = event.target.value as string;
                setClassId(value);
                if (selectedInstrument && String(selectedInstrument.class_id) !== value) {
                  setSelectedInstrument(null);
                  setDistribution(null);
                  setReportsPage(null);
                }
              }}
              displayEmpty
            >
              <MenuItem value="">
                <span style={{ color: 'rgb(100 116 139)' }}>Select asset class</span>
              </MenuItem>
              {instrumentClasses.map((instrumentClass) => (
                <MenuItem key={instrumentClass.id} value={String(instrumentClass.id)}>
                  {instrumentClass.name}
                </MenuItem>
              ))}
            </DarkSelect>
            {classId && (
              <p className="mt-0.5 text-xs text-slate-400">
                {filteredInstruments.length} instrument
                {filteredInstruments.length !== 1 ? 's' : ''} in this class
              </p>
            )}
          </div>

          <div className="flex flex-col gap-1.5 xl:col-span-1">
            <label className="text-xs font-medium text-slate-300">Ticker Symbol</label>
            <DarkAutocomplete<Instrument>
              options={filteredInstruments}
              getOptionLabel={(instrument) => instrument.ticker}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              value={selectedInstrument}
              onChange={(_, instrument) => {
                setSelectedInstrument(instrument);
                if (instrument) {
                  setClassId(String(instrument.class_id));
                  setSelectedPublisher(null);
                  setDistribution(null);
                  setReportsPage(null);
                }
              }}
              filterOptions={(options, { inputValue }) =>
                options.filter(
                  (instrument) =>
                    instrument.ticker.toLowerCase().includes(inputValue.toLowerCase()) ||
                    instrument.name.toLowerCase().includes(inputValue.toLowerCase()),
                )
              }
              renderOption={({ key, ...optionProps }, option) => (
                <li key={key} {...optionProps} style={{ gap: '8px', fontSize: '0.875rem' }}>
                  <span
                    style={{
                      fontFamily: 'monospace',
                      color: 'rgb(96 165 250)',
                      flexShrink: 0,
                    }}
                  >
                    {option.ticker}
                  </span>
                  <span
                    style={{
                      color: 'rgb(148 163 184)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {option.name}
                  </span>
                </li>
              )}
              placeholder="E.g. NVDA, BTC/USD"
            />
          </div>

          <div className="flex items-end xl:justify-end">
            <button
              type="button"
              disabled={isLoading}
              onClick={fetchAnalyticsData}
              className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50 xl:w-auto"
            >
              <Database size={15} />
              {isLoading ? 'Loading…' : 'Load Analytics'}
            </button>
          </div>
        </div>

        {activeFilterLabel && (
          <p className="mt-3 text-xs text-slate-400">Active filter: {activeFilterLabel}</p>
        )}
      </Card>

      {error && <p className="mt-4 text-xs text-red-400">{error}</p>}

      {distribution && <AnalyticsCharts distribution={distribution} />}

      <div className="mt-8">
        <AnalyticsRealisationTable
          data={reportsPage}
          isLoading={isLoadingReports}
          onPageChange={(page) => {
            if (page < 1) return;
            fetchReportsPage(page);
          }}
        />
      </div>
    </div>
  );
}
