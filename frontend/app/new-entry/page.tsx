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
    <NewEntryForm
      instrumentClasses={instrumentClasses}
      instruments={instruments}
      forecastOptions={forecastOptions}
    />
  );
}
