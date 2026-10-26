import React, { useState, useEffect } from 'react';
import {
  Search, Globe, AlertCircle, CheckCircle,
  PlusCircle, Star, ExternalLink
} from 'lucide-react';
import { ProviderInfo, DiscoveredCompany } from '../../types';
import { api } from '../../services/api';

interface DiscoveryViewProps {
  onNavigateToLeads: () => void;
}

export const DiscoveryView: React.FC<DiscoveryViewProps> = ({ onNavigateToLeads }) => {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('test_mock');
  
  // Search Form State
  const [industry, setIndustry] = useState('Dental Clinic');
  const [city, setCity] = useState('Austin');
  const [state, setState] = useState('TX');
  const [country, setCountry] = useState('USA');
  const [keywords, setKeywords] = useState('');
  const [requireWebsite, setRequireWebsite] = useState(false);
  const [requireContact, setRequireContact] = useState(false);
  const [limit, setLimit] = useState(10);

  // Results State
  const [results, setResults] = useState<DiscoveredCompany[]>([]);
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
  const [searching, setSearching] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [importSuccessMsg, setImportSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      const p = await api.getProviders();
      setProviders(p);
      if (p.length > 0 && !p.some(prov => prov.id === selectedProvider)) {
        setSelectedProvider(p[0].id);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const currentProviderInfo = providers.find(p => p.id === selectedProvider);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setImportSuccessMsg(null);
    setSearching(true);
    try {
      const data = await api.searchDiscovery(selectedProvider, {
        industry,
        city,
        state,
        country,
        keywords: keywords || undefined,
        require_website: requireWebsite,
        require_contact: requireContact,
        limit
      });
      setResults(data);
      // Select all by default for easy import
      setSelectedIndices(data.map((_, i) => i));
    } catch (err: any) {
      setError(err.message || 'Discovery search failed');
    } finally {
      setSearching(false);
    }
  };

  const toggleSelectAll = () => {
    if (selectedIndices.length === results.length) {
      setSelectedIndices([]);
    } else {
      setSelectedIndices(results.map((_, i) => i));
    }
  };

  const toggleIndex = (i: number) => {
    if (selectedIndices.includes(i)) {
      setSelectedIndices(selectedIndices.filter(x => x !== i));
    } else {
      setSelectedIndices([...selectedIndices, i]);
    }
  };

  const handleImportSelected = async () => {
    if (selectedIndices.length === 0) return;
    setImporting(true);
    setImportSuccessMsg(null);
    try {
      const companiesToImport = selectedIndices.map(i => results[i]);
      const res = await api.importDiscovered(companiesToImport);
      setImportSuccessMsg(
        `Successfully imported ${res.imported} businesses into CRM! (${res.skipped_duplicates} duplicate records skipped)`
      );
    } catch (err: any) {
      alert(err.message);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Search className="w-5 h-5 text-brand-700" />
          <span>Pipeline A: Authorized Internet Business Discovery</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Search for targeted commercial accounts using authorized Google Places, commercial search APIs, or evaluation directories.
        </p>

        {/* Provider Selector Tabs */}
        <div className="mt-4 flex flex-wrap gap-2">
          {providers.map((p) => (
            <button
              key={p.id}
              onClick={() => { setSelectedProvider(p.id); setError(null); }}
              className={`px-3 py-2 rounded-lg text-xs font-semibold border flex items-center gap-2 transition-colors ${
                selectedProvider === p.id
                  ? 'bg-brand-50 border-brand-700 text-brand-800 shadow-sm'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${p.is_configured ? 'bg-emerald-500' : 'bg-amber-400'}`} />
              <span>{p.name}</span>
              {!p.is_configured && (
                <span className="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200">
                  Key Needed
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Provider Setup Instructions Banner if Unconfigured */}
        {currentProviderInfo && !currentProviderInfo.is_configured && (
          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs space-y-2">
            <div className="font-bold text-amber-900 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              <span>{currentProviderInfo.name} is not currently configured</span>
            </div>
            <p className="text-amber-800">{currentProviderInfo.description}</p>
            <p className="text-amber-900 font-medium">
              Setup Instructions: {currentProviderInfo.setup_instructions}
            </p>
            <div className="pt-1 flex items-center gap-3">
              <a
                href={currentProviderInfo.docs_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-700 hover:underline font-semibold flex items-center gap-1"
              >
                <span>Read Official Provider Documentation</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <span className="text-amber-700 font-bold">•</span>
              <span className="text-amber-800">
                You can switch to the built-in "Test & Evaluation Business Directory" above to test pipeline discovery immediately without credentials!
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Search Filters Form */}
      <form onSubmit={handleSearch} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Search Filters</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Industry / Niche</label>
            <input
              type="text"
              required
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              placeholder="e.g. Roofing, Dentists, Lawyers"
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Target City</label>
            <input
              type="text"
              required
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="e.g. Austin"
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">State / Region</label>
            <input
              type="text"
              value={state}
              onChange={(e) => setState(e.target.value)}
              placeholder="e.g. TX"
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Country</label>
            <input
              type="text"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              placeholder="e.g. USA or India"
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Secondary filters & checkboxes */}
        <div className="flex flex-wrap items-center gap-6 pt-2 border-t border-slate-100 text-xs">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={requireWebsite}
              onChange={(e) => setRequireWebsite(e.target.checked)}
              className="rounded text-brand-600 focus:ring-brand-500"
            />
            <span className="text-slate-700 font-medium">Must have website listed</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={requireContact}
              onChange={(e) => setRequireContact(e.target.checked)}
              className="rounded text-brand-600 focus:ring-brand-500"
            />
            <span className="text-slate-700 font-medium">Must have public phone</span>
          </label>

          <div className="flex items-center gap-2">
            <span className="text-slate-600 font-medium">Records limit:</span>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="px-2 py-1 bg-slate-50 border border-slate-300 rounded text-xs focus:outline-none"
            >
              <option value={10}>10 records</option>
              <option value={20}>20 records</option>
              <option value={50}>50 records</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={searching}
            className="ml-auto px-5 py-2 bg-brand-700 hover:bg-brand-800 disabled:opacity-50 text-white rounded-lg text-xs font-bold shadow-sm transition-colors flex items-center gap-2"
          >
            <Search className={`w-3.5 h-3.5 ${searching ? 'animate-spin' : ''}`} />
            <span>{searching ? 'Discovering...' : 'Discover Businesses'}</span>
          </button>
        </div>
      </form>

      {/* Errors or Success Alerts */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {importSuccessMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span>{importSuccessMsg}</span>
          </div>
          <button
            onClick={onNavigateToLeads}
            className="text-xs font-bold text-brand-800 underline hover:text-brand-900"
          >
            View in CRM Leads →
          </button>
        </div>
      )}

      {/* Results Table */}
      {results.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="text-xs font-bold text-slate-800">
              Discovered {results.length} Potential Leads ({selectedIndices.length} selected)
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleSelectAll}
                className="px-2.5 py-1 bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 rounded text-xs font-medium"
              >
                {selectedIndices.length === results.length ? 'Deselect All' : 'Select All'}
              </button>
              <button
                onClick={handleImportSelected}
                disabled={importing || selectedIndices.length === 0}
                className="px-3.5 py-1 bg-brand-700 hover:bg-brand-800 disabled:opacity-50 text-white rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1.5"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>{importing ? 'Importing...' : `Import Selected (${selectedIndices.length})`}</span>
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 w-8"></th>
                  <th className="px-4 py-3">Company Name</th>
                  <th className="px-4 py-3">Website</th>
                  <th className="px-4 py-3">Public Phone</th>
                  <th className="px-4 py-3">Address</th>
                  <th className="px-4 py-3">Rating</th>
                  <th className="px-4 py-3">Data Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {results.map((c, i) => (
                  <tr
                    key={i}
                    onClick={() => toggleIndex(i)}
                    className={`hover:bg-blue-50/50 cursor-pointer transition-colors ${
                      selectedIndices.includes(i) ? 'bg-blue-50/30' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedIndices.includes(i)}
                        onChange={() => toggleIndex(i)}
                        className="rounded text-brand-600 focus:ring-brand-500"
                      />
                    </td>
                    <td className="px-4 py-3 font-bold text-slate-900">{c.company_name}</td>
                    <td className="px-4 py-3">
                      {c.official_website ? (
                        <a
                          href={c.official_website}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-brand-700 hover:underline flex items-center gap-1"
                        >
                          <Globe className="w-3 h-3" />
                          <span>{c.official_website.replace(/^https?:\/\//, '')}</span>
                        </a>
                      ) : (
                        <span className="text-amber-600 italic">No website (Pitch Need!)</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-700">
                      {c.public_business_phone || <span className="text-slate-400 italic">Not listed</span>}
                    </td>
                    <td className="px-4 py-3 text-slate-600 max-w-xs truncate">
                      {c.public_business_address || `${c.city || ''}, ${c.state || ''}`}
                    </td>
                    <td className="px-4 py-3">
                      {c.rating ? (
                        <div className="flex items-center gap-1 text-amber-600 font-bold">
                          <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                          <span>{c.rating}</span>
                          <span className="text-slate-400 font-normal">({c.user_ratings_total || 0})</span>
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">Unrated</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{c.data_source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
