import React, { useState, useEffect } from 'react';
import {
  Search, Filter, Download, Columns, Table as TableIcon,
  Globe, Phone, Mail, ChevronLeft, ChevronRight, Eye, Trash2
} from 'lucide-react';
import { Lead, CRMStage } from '../../types';
import { api } from '../../services/api';
import { LeadDrawer } from './LeadDrawer';

const CRM_STAGES: CRMStage[] = [
  'New', 'Research Pending', 'Qualified', 'Ready for Review',
  'Contacted', 'Follow-Up', 'Interested', 'Meeting Scheduled',
  'Proposal Sent', 'Converted', 'Not Interested', 'Do Not Contact'
];

export const LeadsView: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedStage, setSelectedStage] = useState<string>('');
  const [selectedPriority, setSelectedPriority] = useState<string>('');
  const [minScore, setMinScore] = useState<number | ''>('');
  const [viewMode, setViewMode] = useState<'table' | 'kanban'>('table');

  // Selected lead for drawer
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  useEffect(() => {
    fetchLeads();
  }, [page, selectedStage, selectedPriority, minScore]);

  const fetchLeads = async () => {
    try {
      setLoading(true);
      const res = await api.listLeads({
        search: search || undefined,
        stage: selectedStage || undefined,
        priority: selectedPriority || undefined,
        min_score: minScore !== '' ? Number(minScore) : undefined,
        page,
        page_size: pageSize
      });
      setLeads(res.items);
      setTotal(res.total);
    } catch (err: any) {
      alert(err.message || 'Failed to fetch leads');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchLeads();
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this lead?')) return;
    try {
      await api.deleteLead(id);
      fetchLeads();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleExport = (format: 'xlsx' | 'csv') => {
    const params: Record<string, string> = {};
    if (selectedStage) params.stage = selectedStage;
    if (selectedPriority) params.priority = selectedPriority;
    if (search) params.search = search;
    const url = api.getExportUrl(format, params);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-4">
      {/* Search and Action Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex-1 w-full flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search companies, email, phone, city, or decision maker..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-1 focus:ring-brand-500 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            Search
          </button>
        </form>

        {/* View Toggle & Export Dropdowns */}
        <div className="flex items-center gap-2 self-end md:self-auto">
          <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs">
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-colors ${
                viewMode === 'table' ? 'bg-white text-brand-800 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
              <span>Table</span>
            </button>
            <button
              onClick={() => setViewMode('kanban')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-colors ${
                viewMode === 'kanban' ? 'bg-white text-brand-800 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>Kanban</span>
            </button>
          </div>

          <button
            onClick={() => handleExport('xlsx')}
            className="flex items-center gap-1 px-3 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-emerald-600" />
            <span>Excel</span>
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center gap-1 px-3 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-blue-600" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Filter Row */}
      <div className="flex flex-wrap items-center gap-3 text-xs bg-white p-3 rounded-xl border border-slate-200">
        <div className="flex items-center gap-1 text-slate-500 font-semibold">
          <Filter className="w-3.5 h-3.5" />
          <span>Filters:</span>
        </div>

        {/* Stage Filter */}
        <select
          value={selectedStage}
          onChange={(e) => { setSelectedStage(e.target.value); setPage(1); }}
          className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-md focus:outline-none"
        >
          <option value="">All CRM Stages</option>
          {CRM_STAGES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        {/* Priority Filter */}
        <select
          value={selectedPriority}
          onChange={(e) => { setSelectedPriority(e.target.value); setPage(1); }}
          className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-md focus:outline-none"
        >
          <option value="">All Priorities</option>
          <option value="High Priority">High Priority (80–100)</option>
          <option value="Medium Priority">Medium Priority (60–79)</option>
          <option value="Low Priority">Low Priority (40–59)</option>
          <option value="Review Required">Review Required (0–39)</option>
        </select>

        {/* Min Score Input */}
        <div className="flex items-center gap-1">
          <span className="text-slate-500">Min Score:</span>
          <input
            type="number"
            min="0"
            max="100"
            placeholder="0"
            value={minScore}
            onChange={(e) => { setMinScore(e.target.value === '' ? '' : Number(e.target.value)); setPage(1); }}
            className="w-14 px-2 py-1 bg-slate-50 border border-slate-300 rounded-md text-center focus:outline-none"
          />
        </div>

        {(selectedStage || selectedPriority || minScore !== '' || search) && (
          <button
            onClick={() => { setSelectedStage(''); setSelectedPriority(''); setMinScore(''); setSearch(''); }}
            className="text-xs text-brand-700 hover:underline font-semibold ml-auto"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Main View: Table or Kanban */}
      {viewMode === 'table' ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Company</th>
                  <th className="px-4 py-3">Contact</th>
                  <th className="px-4 py-3">Location</th>
                  <th className="px-4 py-3">Score & Priority</th>
                  <th className="px-4 py-3">Opportunity</th>
                  <th className="px-4 py-3">CRM Stage</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-slate-400">Loading leads...</td>
                  </tr>
                ) : leads.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-slate-400">
                      No leads match the specified criteria. Use Discovery or Import to add businesses.
                    </td>
                  </tr>
                ) : (
                  leads.map((l) => (
                    <tr
                      key={l.id}
                      onClick={() => setSelectedLead(l)}
                      className="hover:bg-blue-50/40 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="font-bold text-slate-900">{l.company_name}</div>
                        {l.official_website ? (
                          <div className="text-[11px] text-brand-700 hover:underline flex items-center gap-1 mt-0.5">
                            <Globe className="w-3 h-3" />
                            <span>{l.normalized_domain || l.official_website}</span>
                          </div>
                        ) : (
                          <div className="text-[11px] text-amber-600 italic">No website</div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {l.general_business_email && (
                          <div className="text-[11px] text-slate-700 flex items-center gap-1">
                            <Mail className="w-3 h-3 text-slate-400" />
                            <span>{l.general_business_email}</span>
                          </div>
                        )}
                        {l.public_business_phone && (
                          <div className="text-[11px] text-slate-700 flex items-center gap-1 mt-0.5">
                            <Phone className="w-3 h-3 text-slate-400" />
                            <span>{l.public_business_phone}</span>
                          </div>
                        )}
                        {!l.general_business_email && !l.public_business_phone && (
                          <span className="text-slate-400 italic">No contact info</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {l.city || l.state || l.country ? (
                          <span>{[l.city, l.state].filter(Boolean).join(', ')}</span>
                        ) : (
                          <span className="text-slate-400 italic">Unknown</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            l.lead_score >= 80 ? 'bg-amber-100 text-amber-800' :
                            l.lead_score >= 60 ? 'bg-blue-100 text-blue-800' :
                            'bg-slate-100 text-slate-700'
                          }`}>
                            {l.lead_score}
                          </span>
                          <span className="text-slate-500 text-[11px]">{l.priority}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 max-w-xs truncate text-slate-700">
                        {l.recommended_service || l.marketing_opportunity || 'Pending audit'}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-800 rounded font-medium border border-slate-200">
                          {l.crm_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={(e) => { e.stopPropagation(); setSelectedLead(l); }}
                            className="p-1 text-slate-400 hover:text-brand-700 rounded hover:bg-slate-100"
                            title="Inspect Lead"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => handleDelete(l.id, e)}
                            className="p-1 text-slate-400 hover:text-red-600 rounded hover:bg-red-50"
                            title="Delete Lead"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <div>
              Showing {leads.length} of {total} leads
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-1 bg-white border border-slate-200 rounded disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span>Page {page} of {Math.max(1, Math.ceil(total / pageSize))}</span>
              <button
                disabled={page * pageSize >= total}
                onClick={() => setPage(page + 1)}
                className="p-1 bg-white border border-slate-200 rounded disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Kanban Board View */
        <div className="flex gap-4 overflow-x-auto pb-6">
          {['New', 'Qualified', 'Ready for Review', 'Contacted', 'Interested', 'Converted', 'Do Not Contact'].map((colStage) => {
            const colLeads = leads.filter(l => l.crm_status === colStage);
            return (
              <div key={colStage} className="w-72 flex-shrink-0 bg-slate-100 rounded-xl p-3 border border-slate-200 flex flex-col max-h-[75vh]">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200">
                  <span className="font-bold text-xs text-slate-800">{colStage}</span>
                  <span className="bg-white text-slate-600 px-2 py-0.5 rounded-full text-[11px] font-semibold border border-slate-200">
                    {colLeads.length}
                  </span>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                  {colLeads.map((l) => (
                    <div
                      key={l.id}
                      onClick={() => setSelectedLead(l)}
                      className="p-3 bg-white rounded-lg border border-slate-200 shadow-sm hover:border-brand-500 cursor-pointer space-y-1.5 transition-colors"
                    >
                      <div className="font-bold text-xs text-slate-900 truncate">{l.company_name}</div>
                      <div className="text-[11px] text-slate-500 truncate">{l.city || 'No city'}</div>
                      <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-[10px]">
                        <span className="font-bold text-brand-700">Score: {l.lead_score}</span>
                        <span className="text-slate-400">{l.data_source}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Lead Drawer / Detail Modal */}
      {selectedLead && (
        <LeadDrawer
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onLeadUpdated={fetchLeads}
        />
      )}
    </div>
  );
};
