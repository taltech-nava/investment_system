import type { ReactNode } from 'react';

import { formatLabel } from '@/lib/helpers';

interface ScenarioVisualMeta {
  tone: string;
  helper: string;
  accent: string;
  emphasis?: boolean;
}

interface ScenarioPriceCardProps {
  scenario: string;
  children: ReactNode;
}

function getScenarioVisualMeta(scenario: string): ScenarioVisualMeta {
  if (scenario === 'bear') {
    return {
      tone: 'text-red-400',
      helper: 'Lower bound scenario (P10)',
      accent: '↘',
    };
  }
  if (scenario === 'bull') {
    return {
      tone: 'text-amber-400',
      helper: 'Upper bound scenario (P90)',
      accent: '↗',
    };
  }
  if (scenario === 'single') {
    return {
      tone: 'text-violet-300',
      helper: 'Single estimate without scenario split',
      accent: '•',
    };
  }
  return {
    tone: 'text-blue-300',
    helper: 'Most likely outcome (Base Case)',
    accent: '◎',
    emphasis: true,
  };
}

export default function ScenarioPriceCard({ scenario, children }: ScenarioPriceCardProps) {
  const meta = getScenarioVisualMeta(scenario);

  return (
    <div
      className={`rounded-xl border p-4 ${
        meta.emphasis ? 'border-blue-500/40 bg-blue-950/20' : 'border-slate-700 bg-slate-900/35'
      }`}
    >
      <div className="mb-2 flex items-center gap-2">
        <span className={`text-xs font-semibold tracking-wide uppercase ${meta.tone}`}>
          {meta.accent} {formatLabel(scenario)} Case
        </span>
      </div>
      {children}
      <p className="mt-2 text-[11px] text-slate-400">{meta.helper}</p>
    </div>
  );
}
