import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import apiClient from '../api/client';

const Navbar: React.FC = () => {
  const { user, login, logout, hasRole } = useAuth();

  // Auto-fetch user profile on mount (dev mode)
  useEffect(() => {
    if (!localStorage.getItem('user_profile')) {
      apiClient.get('/users/me')
        .then(res => {
          const profile = res.data;
          login(profile, 'dev-token');
        })
        .catch(err => console.warn('Could not fetch user profile', err));
    }
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <nav className="bg-slate-800 text-white px-6 py-4 flex justify-between items-center shadow-md">
      <div className="flex items-center gap-8">
        <Link to="/" className="text-xl font-bold tracking-tight">
          Facturas<span className="text-blue-400">Control</span>
        </Link>
        
        <div className="flex gap-6 text-sm font-medium">
          <Link to="/dashboard" className="hover:text-blue-300 transition-colors">Dashboard</Link>
          
           {(hasRole('Approver') || hasRole('Admin')) && (
             <Link to="/upload" className="hover:text-blue-300 transition-colors">Upload Invoice</Link>
           )}
           
           {(hasRole('Approver') || hasRole('Admin')) && (
             <Link to="/suppliers" className="hover:text-blue-300 transition-colors">Suppliers</Link>
           )}
        </div>
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <span className="text-xs text-slate-400">{user.fullName} ({user.roles[0]})</span>
        )}
        <button 
          onClick={logout}
          className="bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded text-xs transition-colors"
        >
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
