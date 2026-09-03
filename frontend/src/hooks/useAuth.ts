import { createContext, createElement, useContext, useEffect, useState, type ReactNode } from 'react';
import { useMsal } from '@azure/msal-react';
import apiClient, { setTokenProvider, setUnauthorizedHandler } from '../api/client';

export type UserRole = 'Admin' | 'Approver' | 'Clerk' | 'Viewer';
export type Permission = 'read' | 'statistics' | 'upload' | 'approve' | 'delete' | 'supplier_admin';

export interface User {
  email: string | null;
  fullName: string | null;
  roles: UserRole[];
  permissions: Permission[];
}

export interface AuthSession {
  account: object | null;
  acquireToken: () => Promise<string>;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

interface AuthValue {
  user: User | null;
  loading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  can: (permission: Permission) => boolean;
  hasRole: (role: UserRole) => boolean;
}

const empty: AuthValue = { user: null, loading: false, login: async () => {}, logout: async () => {}, can: () => false, hasRole: () => false };
const AuthContext = createContext<AuthValue>(empty);

export const AuthProvider = ({ children, session, initialUser }: { children: ReactNode; session?: AuthSession; initialUser?: User }) => {
  const [user, setUser] = useState<User | null>(initialUser ?? null);
  const [loading, setLoading] = useState(!initialUser);
  const clear = () => {
    setTokenProvider(async () => null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_profile');
    setUser(null);
  };

  useEffect(() => {
    if (initialUser) return void setLoading(false);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_profile');
    setUnauthorizedHandler(clear);
    if (!session?.account) return void setLoading(false);
    setTokenProvider(session.acquireToken);
    session.acquireToken().then(() => apiClient.get<User>('/users/me')).then(({ data }) => setUser(data)).catch(clear).finally(() => setLoading(false));
  }, [initialUser, session]);

  const login = async () => {
    await session?.login();
  };

  const logout = async () => {
    clear();
    await session?.logout();
  };

  const value = { user, loading, login, logout, can: (permission: Permission) => !!user?.permissions.includes(permission), hasRole: (role: UserRole) => !!user?.roles.includes(role) };
  return createElement(AuthContext.Provider, { value }, children);
};

export const MsalAuthProvider = ({ children }: { children: ReactNode }) => {
  const { accounts, instance } = useMsal();
  const account = instance.getActiveAccount() ?? accounts[0] ?? null;
  const scope = import.meta.env.VITE_ENTRA_API_SCOPE || '';
  const session: AuthSession = {
    account,
    acquireToken: async () => (await instance.acquireTokenSilent({ account, scopes: [scope] })).accessToken,
    login: () => instance.loginRedirect({ scopes: [scope] }),
    logout: () => instance.logoutRedirect({ account }),
  };
  return createElement(AuthProvider, { session }, children);
};

export const useAuth = () => useContext(AuthContext);
