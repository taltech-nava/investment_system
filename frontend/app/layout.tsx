import type { Metadata } from 'next';
import { Geist } from 'next/font/google';
import './globals.css';
import AppShell from './components/AppShell';
import { NotifyProvider } from './hooks/useNotify';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'InvestSys',
  description: 'Investment management system',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} h-full antialiased`}>
      <body className="flex h-full flex-col bg-slate-50 font-sans">
        <NotifyProvider>
          <AppShell>{children}</AppShell>
        </NotifyProvider>
      </body>
    </html>
  );
}
