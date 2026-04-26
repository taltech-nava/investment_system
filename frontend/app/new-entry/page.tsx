import { apiFetch } from '@/lib/api';
import NewEntryForm from './NewEntryForm';
import type { ForecastOptions } from '@/types/forecasts';
import { Instrument, InstrumentClass } from '@/types/instruments';

export default async function NewEntryPage() {
  const [instrumentClasses, instruments, forecastOptions] = await Promise.all([
    apiFetch<InstrumentClass[]>('/instrument-classes'),
    apiFetch<Instrument[]>('/instruments'),
    apiFetch<ForecastOptions>('/forecasts/settings'),
  ]);

  return (
    <div className="mx-auto max-w-200 flex-1 overflow-y-auto p-4 pb-6 sm:p-8 md:p-12 md:pb-8">
      <NewEntryForm
        instrumentClasses={instrumentClasses}
        instruments={instruments}
        forecastOptions={forecastOptions}
      />
    </div>
  );
}
