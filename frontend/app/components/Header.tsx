import { TrendingUp, Bell, Menu } from 'lucide-react';
import { redirect } from 'next/navigation';

interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-800 bg-slate-900 px-6">
      {/* Hamburger on mobile, spacer on desktop */}
      <button
        onClick={onMenuClick}
        className="text-slate-400 transition-colors hover:text-white md:hidden"
        aria-label="Open navigation"
      >
        <Menu size={20} strokeWidth={2} />
      </button>
      <div className="hidden w-8 md:block" />

      <div
        className="flex cursor-pointer items-center gap-2.5"
        onClick={() => redirect('/dashboard')}
      >
        <TrendingUp size={20} className="text-blue-400" strokeWidth={2.5} />
        <span className="text-base font-semibold tracking-tight text-blue-500">ForecastReview</span>
      </div>

      <Bell
        size={18}
        className="cursor-pointer text-slate-400 transition-colors hover:text-white"
        strokeWidth={2}
      />
    </header>
  );
}
