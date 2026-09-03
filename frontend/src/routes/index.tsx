import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import UploadInvoice from '../pages/UploadInvoice';
import Suppliers from '../pages/Suppliers';
import ApprovalDashboard from '../pages/ApprovalDashboard';
import SupplierDashboard from '../pages/SupplierDashboard';
import { type Permission, useAuth } from '../hooks/useAuth';

export const RequirePermission = ({ children, permission }: { children: React.ReactNode; permission: Permission }) => {
  const { can, loading, login, user } = useAuth();
  useEffect(() => { if (!loading && !user) void login(); }, [loading, login, user]);
  if (loading) return <div data-testid="auth-loading">Loading session...</div>;
  if (!user) return <div data-testid="sign-in-required">Sign-in required.</div>;
  if (!can(permission)) return <div role="alert">You do not have permission to access this page.</div>;
  return <>{children}</>;
};

export const AccessDeniedNotice = () => {
  const { accessDenied } = useAuth();
  return accessDenied ? <div role="alert" data-testid="access-denied">Access denied. You do not have permission to complete this action.</div> : null;
};

const AppRoutes: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <AccessDeniedNotice />
        <main className="py-8">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<RequirePermission permission="read"><ApprovalDashboard /></RequirePermission>} />
            <Route path="/upload" element={<RequirePermission permission="upload"><UploadInvoice /></RequirePermission>} />
            <Route path="/suppliers" element={<RequirePermission permission="read"><Suppliers /></RequirePermission>} />
            <Route path="/suppliers/:id/dashboard" element={<RequirePermission permission="statistics"><SupplierDashboard /></RequirePermission>} />
            <Route path="*" element={<div className="text-center p-10 text-slate-500">Page not found</div>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default AppRoutes;
