'use client';

import { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import useNotify from '../hooks/useNotify';

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { snackbar, notify } = useNotify();

  return (
    <div className="flex h-screen flex-col">
      <Header onMenuClick={() => setSidebarOpen(true)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="flex-1 overflow-y-auto p-4 pb-6 sm:p-8 md:p-12 md:pb-8">
          <div>{children}</div>
        </main>
      </div>
      <Footer />
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => notify((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => notify((s) => ({ ...s, open: false }))}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </div>
  );
}
