import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import UploadInvoice from '../pages/UploadInvoice';
import Suppliers from '../pages/Suppliers';
import ApprovalDashboard from '../pages/ApprovalDashboard';

const AppRoutes: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <main className="py-8">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<ApprovalDashboard />} />
            <Route path="/upload" element={<UploadInvoice />} />
            <Route path="/suppliers" element={<Suppliers />} />
            <Route path="*" element={<div className="text-center p-10 text-slate-500">Page not found</div>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default AppRoutes;
