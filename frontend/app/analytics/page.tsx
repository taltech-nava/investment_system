import { apiFetch } from '@/lib/api';
import type { Instrument, InstrumentClass } from '@/types/instruments';
import type { Publisher } from '@/types/publishers';
import AnalyticsFilters from './AnalyticsFilters';

export default async function AnalyticsPage() {
  const [instrumentClasses, instruments, publishers] = await Promise.all([
    apiFetch<InstrumentClass[]>('/instrument-classes'),
    apiFetch<Instrument[]>('/instruments'),
    apiFetch<Publisher[]>('/publishers'),
  ]);

  return (
    <AnalyticsFilters
      instrumentClasses={instrumentClasses}
      instruments={instruments}
      publishers={publishers}
    />
  );
}
