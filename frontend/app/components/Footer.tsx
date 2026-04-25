export default function Footer() {
  return (
    <footer className="flex h-10 shrink-0 items-center justify-center border-t border-slate-800 bg-slate-900 px-6">
      <span className="text-xs text-slate-500">
        © {new Date().getFullYear()} InvestSys Intelligence Systems
      </span>
    </footer>
  );
}
