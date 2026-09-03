import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import './index.css';
import AppRoutes from './routes';
import { MsalAuthProvider } from './hooks/useAuth';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: true,
    },
  },
});
const msal = new PublicClientApplication({ auth: { clientId: import.meta.env.VITE_ENTRA_CLIENT_ID || '', authority: `https://login.microsoftonline.com/${import.meta.env.VITE_ENTRA_TENANT_ID || ''}`, redirectUri: import.meta.env.VITE_ENTRA_REDIRECT_URI || window.location.origin } });

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MsalProvider instance={msal}><MsalAuthProvider><AppRoutes /></MsalAuthProvider></MsalProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
