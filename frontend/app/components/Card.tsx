import type { ReactNode } from 'react';

interface CardProps {
  header: ReactNode;
  children: ReactNode;
}

export default function Card({ header, children }: CardProps) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/40">
      <div className="border-b border-slate-700 px-6 py-4">{header}</div>
      <div className="p-6">{children}</div>
    </div>
  );
}
