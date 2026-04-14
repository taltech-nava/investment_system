export default function Footer() {
  return (
    <footer className="h-10 shrink-0 bg-slate-900 border-t border-slate-800 flex items-center justify-center px-6">
      <span className="text-xs text-slate-500">
        © {new Date().getFullYear()} InvestSys Intelligence Systems
      </span>
    </footer>
  );
}
