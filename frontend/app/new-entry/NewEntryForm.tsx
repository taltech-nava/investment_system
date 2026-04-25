'use client';

import { useEffect, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Search, CircleDollarSign, CalendarDays, Database } from 'lucide-react';
import InputAdornment from '@mui/material/InputAdornment';
import MenuItem from '@mui/material/MenuItem';
import { clientApiFetch, ApiError, type PydanticFieldError } from '@/lib/api';
import Card from '@/app/components/Card';
import DarkAutocomplete from '@/app/components/DarkAutocomplete';
import DarkSelect from '@/app/components/DarkSelect';
import DarkTextField from '@/app/components/DarkTextField';
import type { Instrument, InstrumentClass } from '@/types/instruments';
import type { ForecastOptions, ForecastRead } from '@/types/forecasts';
import useNotify from '../hooks/useNotify';
import DarkSlider from '../components/DarkSlider';
import { formatTimestamp } from '@/lib/helpers';
import ScenarioPriceCard from './ScenarioPriceCard';

interface NewEntryFormProps {
  instrumentClasses: InstrumentClass[];
  instruments: Instrument[];
  forecastOptions: ForecastOptions;
}

interface FormValues {
  instrument: Instrument | null;
  publisherName: string;
  classId: string;
  scenarioPrices: Record<string, string>;
  maturationDate: string;
  method: string;
  conviction: number;
}

const DEFAULT_CONVICTION_SOURCE = 'manual';
const DEFAULT_HORIZON_SOURCE = 'source_declared';
const DEFAULT_ENTRY_MODE = 'manual';
const POINT_ESTIMATE_TYPE = 'manual_point_estimate';
const SCENARIO_ESTIMATE_TYPE = 'manual_scenario_estimate';

function getDefaultMaturationDate(): string {
  const date = new Date();
  date.setFullYear(date.getFullYear() + 1);
  return date.toISOString().slice(0, 10);
}

export default function NewEntryForm({
  instrumentClasses,
  instruments,
  forecastOptions,
}: NewEntryFormProps) {
  const [timestamp, setTimestamp] = useState<Date | null>(null);

  const { notify } = useNotify();

  const {
    control,
    handleSubmit,
    reset,
    setValue,
    watch,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    defaultValues: {
      instrument: null,
      publisherName: '',
      classId: '',
      scenarioPrices: Object.fromEntries(
        forecastOptions.scenarios.map((scenario) => [scenario, '']),
      ),
      maturationDate: getDefaultMaturationDate(),
      method: '',
      conviction: 3,
    },
  });

  useEffect(() => {
    setTimestamp(new Date());
  }, []);

  const classId = watch('classId');
  const conviction = watch('conviction');
  const instrumentValue = watch('instrument');

  const filteredInstruments = classId
    ? instruments.filter((i) => i.class_id === Number(classId))
    : instruments;

  async function onSubmit(data: FormValues) {
    if (!data.instrument) return;
    const instrument = data.instrument;

    const filledScenarios = Object.entries(data.scenarioPrices)
      .map(([scenario, value]) => ({ scenario, price: Number.parseFloat(value) }))
      .filter(({ price }) => Number.isFinite(price) && price > 0);

    if (filledScenarios.length === 0) {
      setError('root', {
        message: 'Add at least one scenario price before saving.',
      });
      return;
    }

    try {
      const created = await Promise.all(
        filledScenarios.map(({ scenario, price }) =>
          clientApiFetch<ForecastRead>('/forecasts', {
            method: 'POST',
            body: JSON.stringify({
              instrument_id: instrument.id,
              publisher_name: data.publisherName || null,
              scenario,
              predicted_price: price,
              maturation_date: data.maturationDate,
              conviction: data.conviction,
              conviction_source: DEFAULT_CONVICTION_SOURCE,
              horizon_source: DEFAULT_HORIZON_SOURCE,
              method: data.method || null,
              entry_mode: DEFAULT_ENTRY_MODE,
              estimate_type: scenario === 'single' ? POINT_ESTIMATE_TYPE : SCENARIO_ESTIMATE_TYPE,
            }),
          }),
        ),
      );
      const count = created.length;
      notify({
        open: true,
        message: `Saved ${count} forecast${count !== 1 ? 's' : ''} successfully.`,
        severity: 'success',
      });
      reset();
    } catch (err) {
      if (err instanceof ApiError && Array.isArray(err.detail)) {
        // Map Pydantic field errors back to form fields where possible
        const fieldMap: Record<string, keyof FormValues> = {
          maturation_date: 'maturationDate',
          instrument_id: 'instrument',
          conviction: 'conviction',
          method: 'method',
          publisher_name: 'publisherName',
        };
        let hasFieldErrors = false;
        for (const e of err.detail as PydanticFieldError[]) {
          const apiField = e.loc[1] as string;
          if (apiField === 'scenario' || apiField === 'predicted_price') {
            setError('root', { message: e.msg });
            hasFieldErrors = true;
            continue;
          }
          const formField = fieldMap[apiField];
          if (formField) {
            setError(formField, { message: e.msg });
            hasFieldErrors = true;
          }
        }
        if (!hasFieldErrors) {
          notify({ open: true, message: err.message, severity: 'error' });
        }
      } else {
        const message = err instanceof Error ? err.message : 'An unexpected error occurred';
        notify({ open: true, message, severity: 'error' });
      }
    }
  }

  return (
    <>
      <form onSubmit={handleSubmit(onSubmit)} className="mb-6">
        {/* Page header */}
        <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-x-2">
          <div>
            <h1 className="text-2xl font-semibold text-white">Manual Price Entry</h1>
            <p className="mt-1 text-sm text-slate-400">
              Input precise market expectations or correct automated extraction failures.
            </p>
          </div>
          <div className="flex w-fit shrink-0 items-center gap-2 rounded-md border border-slate-700 px-3 py-2 text-xs">
            <span className="font-medium tracking-wide text-slate-500 uppercase">
              Entry Timestamp
            </span>
            <span className="font-mono text-slate-200">
              {timestamp ? formatTimestamp(timestamp) : '—'}
            </span>
          </div>
        </div>

        <div className="mb-16 h-px w-full bg-slate-800" />

        <div className="flex max-w-3xl flex-col gap-5">
          <Card
            header={
              <div>
                <div className="flex items-center gap-2">
                  <Database size={15} className="text-blue-400" />
                  <span className="text-sm font-semibold text-white">Publisher</span>
                </div>
                <p className="mt-1 text-xs text-slate-400">
                  Source institution for this forecast. Empty value defaults to Self.
                </p>
              </div>
            }
          >
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-slate-300">Publisher Name</label>
              <Controller
                name="publisherName"
                control={control}
                render={({ field }) => (
                  <DarkTextField {...field} placeholder="Optional. Defaults to Self" fullWidth />
                )}
              />
              <p className="text-xs text-slate-500">
                Leave empty to use publisher &quot;Self&quot;.
              </p>
              {errors.publisherName && (
                <p className="mt-0.5 text-xs text-red-400">{errors.publisherName.message}</p>
              )}
            </div>
          </Card>

          {/* Asset Details */}
          <Card
            header={
              <div>
                <div className="flex items-center gap-2">
                  <Search size={15} className="text-blue-400" />
                  <span className="text-sm font-semibold text-white">Asset Details</span>
                </div>
                <p className="mt-1 text-xs text-slate-400">
                  Specify the financial instrument for this forecast.
                </p>
              </div>
            }
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-slate-300">Ticker Symbol</label>
                <Controller
                  name="instrument"
                  control={control}
                  rules={{ required: 'Select an instrument' }}
                  render={({ field }) => (
                    <DarkAutocomplete<Instrument>
                      options={filteredInstruments}
                      getOptionLabel={(o) => o.ticker}
                      isOptionEqualToValue={(o, v) => o.ticker === v.ticker}
                      value={field.value}
                      onChange={(_, instrument) => {
                        field.onChange(instrument);
                        if (instrument) setValue('classId', String(instrument.class_id));
                      }}
                      filterOptions={(opts, { inputValue }) =>
                        opts.filter(
                          (o) =>
                            o.ticker.toLowerCase().includes(inputValue.toLowerCase()) ||
                            o.name.toLowerCase().includes(inputValue.toLowerCase()),
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
                  )}
                />
                {errors.instrument && (
                  <p className="mt-0.5 text-xs text-red-400">{errors.instrument.message}</p>
                )}
                {!errors.instrument && instrumentValue && (
                  <p className="mt-0.5 text-xs text-slate-400">
                    {instrumentValue.name} · {instrumentValue.currency}
                  </p>
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-slate-300">Asset Class</label>
                <Controller
                  name="classId"
                  control={control}
                  render={({ field }) => (
                    <DarkSelect
                      value={field.value}
                      onChange={(e) => {
                        const val = e.target.value as string;
                        field.onChange(val);
                        if (instrumentValue && String(instrumentValue.class_id) !== val) {
                          setValue('instrument', null);
                        }
                      }}
                      displayEmpty
                    >
                      <MenuItem value="">
                        <span style={{ color: 'rgb(100 116 139)' }}>Select asset class</span>
                      </MenuItem>
                      {instrumentClasses.map((ic) => (
                        <MenuItem key={ic.id} value={String(ic.id)}>
                          {ic.name}
                        </MenuItem>
                      ))}
                    </DarkSelect>
                  )}
                />
                {classId && (
                  <p className="mt-0.5 text-xs text-slate-400">
                    {filteredInstruments.length} instrument
                    {filteredInstruments.length !== 1 ? 's' : ''} in this class
                  </p>
                )}
              </div>
            </div>
          </Card>

          {/* Price Targets */}
          <Card
            header={
              <div>
                <div className="flex items-center gap-2">
                  <CircleDollarSign size={15} className="text-blue-400" />
                  <span className="text-sm font-semibold text-white">Price Targets</span>
                </div>
                <p className="mt-1 text-xs text-slate-400">
                  Fill any scenarios you need. The form sends one forecast request per filled card.
                </p>
              </div>
            }
          >
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              {forecastOptions.scenarios.map((scenario) => (
                <ScenarioPriceCard key={scenario} scenario={scenario}>
                  <Controller
                    name={`scenarioPrices.${scenario}`}
                    control={control}
                    render={({ field }) => (
                      <DarkTextField
                        {...field}
                        fullWidth
                        type="number"
                        slotProps={{
                          input: {
                            startAdornment: (
                              <InputAdornment position="start">
                                <span className="text-sm text-slate-400">$</span>
                              </InputAdornment>
                            ),
                          },
                          htmlInput: { min: 0, step: 0.01 },
                        }}
                      />
                    )}
                  />
                </ScenarioPriceCard>
              ))}
            </div>
          </Card>

          {/* Forecast Metadata */}
          <Card
            header={
              <div>
                <div className="flex items-center gap-2">
                  <CalendarDays size={15} className="text-blue-400" />
                  <span className="text-sm font-semibold text-white">Forecast Metadata</span>
                </div>
                <p className="mt-1 text-xs text-slate-400">
                  Technical details and conviction metrics.
                </p>
              </div>
            }
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-slate-300">Maturation Date</label>
                <Controller
                  name="maturationDate"
                  control={control}
                  rules={{
                    required: 'Maturation date is required',
                    validate: (v) => new Date(v) > new Date() || 'Date must be in the future',
                  }}
                  render={({ field }) => <DarkTextField {...field} type="date" />}
                />
                {errors.maturationDate && (
                  <p className="mt-0.5 text-xs text-red-400">{errors.maturationDate.message}</p>
                )}
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-slate-300">Method</label>
                <Controller
                  name="method"
                  control={control}
                  render={({ field }) => (
                    <DarkTextField
                      {...field}
                      placeholder="Optional free-text method details"
                      fullWidth
                    />
                  )}
                />
                {errors.method && (
                  <p className="mt-0.5 text-xs text-red-400">{errors.method.message}</p>
                )}
              </div>
            </div>

            <div className="my-6 h-px bg-slate-700" />

            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-300">Conviction Level</span>
                <span className="rounded-full bg-blue-500/20 px-3 py-0.5 text-xs font-medium text-blue-400">
                  {conviction} Confidence
                </span>
              </div>
              <Controller
                name="conviction"
                control={control}
                render={({ field }) => (
                  <DarkSlider
                    value={field.value}
                    onChange={(_, val) => field.onChange(val)}
                    min={1}
                    max={5}
                  />
                )}
              />
              <div className="flex justify-between text-xs font-medium tracking-wide text-slate-500 uppercase">
                <span>Speculative</span>
                <span>Moderate</span>
                <span>High Conviction</span>
              </div>
            </div>
          </Card>
        </div>

        {errors.root && (
          <p className="mt-4 max-w-3xl text-xs text-red-400">{errors.root.message}</p>
        )}

        <div className="mt-6 flex max-w-3xl flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-center text-xs text-slate-500 italic">
            * All entries are subject to internal audit trails.
          </p>
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Database size={15} />
            {isSubmitting ? 'Saving…' : 'Save Forecast'}
          </button>
        </div>
      </form>
    </>
  );
}
