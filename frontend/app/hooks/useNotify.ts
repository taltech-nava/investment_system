'use client';

import {
  createElement,
  createContext,
  useContext,
  useMemo,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from 'react';

export interface SnackbarState {
  open: boolean;
  message: string;
  severity: 'success' | 'error';
}

interface NotifyContextValue {
  snackbar: SnackbarState;
  notify: Dispatch<SetStateAction<SnackbarState>>;
}

const NotifyContext = createContext<NotifyContextValue | null>(null);

export function NotifyProvider({ children }: { children: ReactNode }) {
  const [snackbar, notify] = useState<SnackbarState>({
    open: false,
    message: '',
    severity: 'success',
  });

  const value = useMemo<NotifyContextValue>(
    () => ({
      snackbar,
      notify,
    }),
    [snackbar],
  );

  return createElement(NotifyContext.Provider, { value }, children);
}

export default function useNotify() {
  const context = useContext(NotifyContext);
  if (!context) {
    throw new Error('useNotify must be used within NotifyProvider');
  }

  return context;
}
