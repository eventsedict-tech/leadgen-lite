import React, { useState, useEffect } from 'react';
import { ShieldBan, Plus, Trash2, AlertCircle } from 'lucide-react';
import { SuppressionItem } from '../../types';
import { api } from '../../services/api';

export const SuppressionView: React.FC = () => {
  const [items, setItems] = useState<SuppressionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [domain, setDomain] = useState('');
  const [reason, setReason] = useState('Requested Unsubscribe');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSuppression();
  }, []);

  const loadSuppression = async () => {
    try {
      setLoading(true);
      const res = await api.listSuppression();
      setItems(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email && !phone && !domain) {
      setError('Please provide at least an email, phone, or domain.');
      return;
    }
    setError(null);
    try {
      await api.addSuppression({ email, phone, domain, reason });
      setEmail('');
      setPhone('');
      setDomain('');
      loadSuppression();
    } catch (err: any) {
      setError(err.message || 'Failed to add to suppression list');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Remove this item from the suppression list?')) return;
    try {
      await api.deleteSuppression(id);
      loadSuppression();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <ShieldBan className="w-5 h-5 text-rose-600" />
          <span>Outreach Suppression List</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Contacts on this list are permanently prevented from entering outreach campaigns, and their CRM status is automatically locked to "Do Not Contact".
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Add to Suppression Form */}
      <form onSubmit={handleAdd} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Add to Suppression</h3>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Email Address</label>
            <input
              type="email"
              placeholder="e.g. optout@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Phone Number</label>
            <input
              type="text"
              placeholder="e.g. +1 512 555 0199"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full px-3 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Company Domain</label>
            <input
              type="text"
              placeholder="e.g. competitor.com"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full px-3 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Reason</label>
            <input
              type="text"
              required
              placeholder="e.g. Unsubscribe request"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
            />
          </div>
        </div>
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold shadow-sm transition-colors flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Suppression Entry</span>
          </button>
        </div>
      </form>

      {/* Suppression Records Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-3 bg-slate-50 border-b border-slate-200 font-bold text-xs text-slate-800">
          Active Suppressions ({items.length})
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Phone</th>
                <th className="px-4 py-3">Domain</th>
                <th className="px-4 py-3">Reason</th>
                <th className="px-4 py-3">Added Date</th>
                <th className="px-4 py-3 text-right">Remove</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-400">Loading suppression list...</td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-400">No contacts currently suppressed.</td>
                </tr>
              ) : (
                items.map((it) => (
                  <tr key={it.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-semibold text-slate-900">{it.email || '-'}</td>
                    <td className="px-4 py-3 text-slate-700">{it.phone || '-'}</td>
                    <td className="px-4 py-3 text-slate-700">{it.domain || '-'}</td>
                    <td className="px-4 py-3 text-rose-700 font-medium">{it.reason}</td>
                    <td className="px-4 py-3 text-slate-400">{new Date(it.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDelete(it.id)}
                        className="p-1 text-slate-400 hover:text-red-600 rounded"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
