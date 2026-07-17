import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

interface Supplier {
  id: string;
  name: string;
  taxId: string;
  email: string;
  address: string;
}

const Suppliers: React.FC = () => {
  const { hasRole } = useAuth();
  const navigate = useNavigate();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [newSupplier, setNewSupplier] = useState({ name: '', taxId: '', email: '', address: '' });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const fetchSuppliers = async () => {
    try {
      const response = await apiClient.get('/suppliers');
      setSuppliers(response.data);
    } catch (error) {
      console.error('Failed to fetch suppliers', error);
    }
  };

  const handleEdit = (supplier: Supplier) => {
    setEditingSupplier(supplier);
    setNewSupplier({
      name: supplier.name,
      taxId: supplier.taxId,
      email: supplier.email || '',
      address: supplier.address || '',
    });
    setShowForm(true);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingSupplier(null);
    setNewSupplier({ name: '', taxId: '', email: '', address: '' });
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingSupplier) {
        await apiClient.put(`/suppliers/${editingSupplier.id}`, newSupplier);
      } else {
        await apiClient.post('/suppliers', newSupplier);
      }
      handleCancelForm();
      fetchSuppliers();
    } catch (error) {
      console.error('Failed to save supplier', error);
      alert('Error saving supplier');
    }
  };

  const handleDelete = async (supplier: Supplier) => {
    if (!window.confirm(`Are you sure you want to delete supplier "${supplier.name}"?`)) return;
    try {
      await apiClient.delete(`/suppliers/${supplier.id}`);
      fetchSuppliers();
    } catch (error: any) {
      const detail = error?.response?.data?.detail || 'Error deleting supplier';
      alert(detail);
    }
  };

  const filteredSuppliers = suppliers.filter((s) =>
    (s.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (s.taxId || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (s.email || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Supplier Management</h1>
        {hasRole('Admin') && (
          <button
            data-testid="add-supplier-btn"
            onClick={() => {
              if (showForm) {
                handleCancelForm();
              } else {
                setShowForm(true);
              }
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {showForm ? 'Cancel' : '+ Add Supplier'}
          </button>
        )}
      </div>

      <div className="mb-4">
        <input
          type="text"
          data-testid="supplier-search"
          placeholder="Search suppliers..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
        />
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 mb-8 grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <h3 className="font-semibold mb-4">{editingSupplier ? 'Edit Supplier' : 'New Supplier Details'}</h3>
            {editingSupplier && (
              <p className="text-xs text-slate-500 mb-2">Editing: <span className="font-medium">{editingSupplier.name}</span></p>
            )}
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Name</label>
            <input 
              required
              type="text" 
              value={newSupplier.name} 
              onChange={e => setNewSupplier({...newSupplier, name: e.target.value})}
              className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Tax ID / VAT</label>
            <input 
              required
              type="text" 
              value={newSupplier.taxId} 
              onChange={e => setNewSupplier({...newSupplier, taxId: e.target.value})}
              className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Email</label>
            <input 
              type="email" 
              value={newSupplier.email} 
              onChange={e => setNewSupplier({...newSupplier, email: e.target.value})}
              className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Address</label>
            <input 
              type="text" 
              value={newSupplier.address} 
              onChange={e => setNewSupplier({...newSupplier, address: e.target.value})}
              className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div className="col-span-2 flex justify-end mt-4">
            <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors">
                {editingSupplier ? 'Update Supplier' : 'Save Supplier'}
              </button>
          </div>
        </form>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600 uppercase text-xs">
            <tr>
              <th className="p-4 font-semibold">Supplier Name</th>
              <th className="p-4 font-semibold">Tax ID</th>
              <th className="p-4 font-semibold">Email</th>
              <th className="p-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredSuppliers.map(s => (
              <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                <td className="p-4 font-medium text-slate-800">{s.name}</td>
                <td className="p-4 text-slate-600">{s.taxId}</td>
                <td className="p-4 text-slate-600">{s.email}</td>
                <td className="p-4 text-right">
                  {(hasRole('Admin') || hasRole('Approver')) && (
                    <div className="flex items-center justify-end gap-3">
                      <button
                        data-testid={`stats-btn-${s.id}`}
                        onClick={() => navigate(`/suppliers/${s.id}/dashboard`)}
                        className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title="View supplier statistics"
                        aria-label={`View statistics for ${s.name}`}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <rect x="4" y="12" width="3" height="8" />
                          <rect x="10.5" y="8" width="3" height="12" />
                          <rect x="17" y="4" width="3" height="16" />
                        </svg>
                      </button>
                      {hasRole('Admin') && (
                        <>
                          <button
                            onClick={() => handleEdit(s)}
                            className="text-blue-600 hover:text-blue-800 font-medium transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            data-testid={`delete-supplier-btn-${s.id}`}
                            onClick={() => handleDelete(s)}
                            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                            title="Delete supplier"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <polyline points="3 6 5 6 21 6" />
                              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                              <path d="M10 11v6" />
                              <path d="M14 11v6" />
                              <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                            </svg>
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </td>
              </tr>
            ))}
            {filteredSuppliers.length === 0 && (
              <tr>
                <td colSpan={4} className="p-8 text-center text-slate-400 italic">No suppliers found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Suppliers;
