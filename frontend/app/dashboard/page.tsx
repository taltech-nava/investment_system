import { apiFetch } from '@/lib/api';
import InstrumentsTable from './instrumentstable';

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

export default async function DashboardPage() {
  //const instruments = await apiFetch<Instrument[]>('/instruments');

  const [instruments, sources, forecasts, publishers] = await Promise.all([
    apiFetch<Instrument[]>('/instruments'),
    apiFetch<Source[]>('/sources'),
    apiFetch<Forecasts[]>('/forecasts'),
    apiFetch<Publishers[]>('/publishers'),
  ]);


  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">Dashboard</h1>
      <InstrumentsTable instruments={instruments} sources={sources} forecasts={forecasts} publishers={publishers} />
    </div>
  )
}
