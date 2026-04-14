import { apiFetch } from '@/lib/api';

interface Instrument {
  id: number;
  ticker: string;
  name: string;
  currency: string;
  class_id: number;
}

export default async function DashboardPage() {
  const instruments = await apiFetch<Instrument[]>('/instruments');

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">Dashboard</h1>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-700">Instruments</h2>
          <p className="mt-0.5 text-xs text-slate-400">{instruments.length} tracked</p>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="px-5 py-3 text-left text-xs font-medium tracking-wide text-slate-500 uppercase">
                Ticker
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium tracking-wide text-slate-500 uppercase">
                Name
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium tracking-wide text-slate-500 uppercase">
                Currency
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {instruments.map((instrument) => (
              <tr key={instrument.id} className="transition-colors hover:bg-slate-50">
                <td className="px-5 py-3 font-mono font-medium text-blue-600">
                  {instrument.ticker}
                </td>
                <td className="px-5 py-3 text-slate-700">{instrument.name}</td>
                <td className="px-5 py-3 text-slate-500">{instrument.currency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
