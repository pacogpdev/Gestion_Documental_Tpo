import { useState } from 'react';

export type UserRole = 'Admin' | 'Approver' | 'Viewer';

interface User {
  email: string;
  fullName: string;
  roles: UserRole[];
}

function getStoredUser(): User | null {
  try {
    const storedUser = localStorage.getItem('user_profile');
    return storedUser ? (JSON.parse(storedUser) as User) : null;
  } catch {
    return null;
  }
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(getStoredUser);
  const [loading] = useState(false);

  const login = (userData: User, token: string) => {
    localStorage.setItem('user_profile', JSON.stringify(userData));
    localStorage.setItem('auth_token', token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('user_profile');
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  const hasRole = (role: UserRole) => {
    return user?.roles.includes(role) || false;
  };

  return { user, loading, login, logout, hasRole };
};
