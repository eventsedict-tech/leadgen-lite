import React, { useEffect, useState } from 'react';
import {
  Users, UploadCloud, Globe, Award, CheckCircle,
  Clock, TrendingUp, Search, AlertTriangle
} from 'lucide-react';
import { api } from '../../services/api';
import { DashboardData } from '../../types';

interface DashboardViewProps {
  onNavigate: (tab: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        setLoading(true);
        const res = await api.getDashboard();
        setData(res);
      } catch (err: any) {
        setError(err.message || 'Failed to load metrics');
      } finally {
        setLoading(false);
      }
    }
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-brand-700"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
        {error || 'Unable to load dashboard data'}
      </div>
    );
  }

  const { metrics, distributions, recent_imports, recent_research_jobs, upcoming_follow_ups } = data;

  const statCards = [
    { label: 'Total Leads', val: metrics.total_leads, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50', link: 'leads' },
    { label: 'High Priority', val: metrics.high_priority_leads, icon: Award, color: 'text-amber-600', bg: 'bg-amber-50', link: 'leads' },
    { label: 'Websites Analyzed', val: metrics.websites_analyzed, icon: Globe, color: 'text-indigo-600', bg: 'bg-indigo-50', link: 'leads' },
    { label: 'Qualified Leads', val: metrics.qualified_leads, icon: CheckCircle, color: 'text-emerald-600', bg: 'bg-emerald-50', link: 'leads' },
    { label: 'Follow-Ups Due', val: metrics.follow_ups_due, icon: Clock, color: 'text-rose-600', bg: 'bg-rose-50', link: 'leads' },
    { label: 'Leads Imported', val: metrics.leads_imported, icon: UploadCloud, color: 'text-cyan-600', bg: 'bg-cyan-50', link: 'import-export' },
    { label: 'Leads Discovered', val: metrics.leads_discovered, icon: Search, color: 'text-violet-600', bg: 'bg-violet-50', link: 'discovery' },
    { label: 'Converted Leads', val: metrics.converted_leads, icon: TrendingUp, color: 'text-teal-600', bg: 'bg-teal-50', link: 'leads' },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-brand-800 to-brand-700 rounded-xl p-6 text-white shadow-md flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Marketing Intelligence Dashboard</h1>
          <p className="text-blue-100 text-sm mt-1">
            Real-time B2B discovery, SEO audit analytics, lead scoring, and outreach pipeline.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onNavigate('discovery')}
            className="px-4 py-2 bg-white text-brand-800 hover:bg-blue-50 rounded-lg text-sm font-semibold shadow-sm transition-colors"
          >
            Find New Businesses
          </button>
          <button
            onClick={() => onNavigate('import-export')}
            className="px-4 py-2 bg-brand-900/60 hover:bg-brand-900 text-white border border-white/20 rounded-lg text-sm font-semibold transition-colors"
          >
            Import CSV / Excel
          </button>
        </div>
      </div>

      {/* 8 Core Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div
              key={i}
              onClick={() => onNavigate(c.link)}
              className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer flex items-center justify-between"
            >
              <div>
                <p className="text-xs font-medium text-slate-500">{c.label}</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{c.val}</p>
              </div>
              <div className={`p-3 rounded-lg ${c.bg}`}>
                <Icon className={`w-5 h-5 ${c.color}`} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Distributions (Industry, City, Source, Priority) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* By Industry */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Leads by Industry</h3>
          <div className="space-y-2">
            {distributions.by_industry.length === 0 ? (
              <p className="text-xs text-slate-400">No industry data yet</p>
            ) : (
              distributions.by_industry.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs">
                  <span className="text-slate-700 truncate max-w-[140px]">{item.label}</span>
                  <span className="font-semibold text-brand-700 bg-blue-50 px-2 py-0.5 rounded-full">{item.count}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* By City */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Leads by City</h3>
          <div className="space-y-2">
            {distributions.by_city.length === 0 ? (
              <p className="text-xs text-slate-400">No city data yet</p>
            ) : (
              distributions.by_city.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs">
                  <span className="text-slate-700 truncate max-w-[140px]">{item.label}</span>
                  <span className="font-semibold text-brand-700 bg-blue-50 px-2 py-0.5 rounded-full">{item.count}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* By Source */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Leads by Source</h3>
          <div className="space-y-2">
            {distributions.by_source.length === 0 ? (
              <p className="text-xs text-slate-400">No sources recorded</p>
            ) : (
              distributions.by_source.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs">
                  <span className="text-slate-700 truncate max-w-[140px]">{item.label}</span>
                  <span className="font-semibold text-brand-700 bg-blue-50 px-2 py-0.5 rounded-full">{item.count}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* By Priority */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Leads by Priority</h3>
          <div className="space-y-2">
            {distributions.by_priority.length === 0 ? (
              <p className="text-xs text-slate-400">No scored leads</p>
            ) : (
              distributions.by_priority.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs">
                  <span className="text-slate-700 truncate max-w-[140px]">{item.label}</span>
                  <span className="font-semibold text-brand-700 bg-blue-50 px-2 py-0.5 rounded-full">{item.count}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* 3 Detail Panels: Upcoming Follow-ups, Recent Imports, Recent Research Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming Follow-ups */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <Clock className="w-4 h-4 text-brand-600" />
              <span>Upcoming Follow-Ups</span>
            </h2>
            <button onClick={() => onNavigate('leads')} className="text-xs text-brand-700 font-medium hover:underline">
              View CRM
            </button>
          </div>
          {upcoming_follow_ups.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">No pending follow-ups scheduled.</p>
          ) : (
            <div className="space-y-3">
              {upcoming_follow_ups.map((task) => (
                <div key={task.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-start justify-between">
                  <div>
                    <div className="text-xs font-bold text-slate-800">{task.company_name}</div>
                    <div className="text-xs text-slate-600 mt-0.5">{task.title}</div>
                    <div className={`text-[11px] mt-1 font-medium ${task.is_overdue ? 'text-red-600 flex items-center gap-1' : 'text-slate-500'}`}>
                      {task.is_overdue && <AlertTriangle className="w-3 h-3" />}
                      Due: {task.due_date}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Imports */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <UploadCloud className="w-4 h-4 text-cyan-600" />
              <span>Recent File Imports</span>
            </h2>
            <button onClick={() => onNavigate('import-export')} className="text-xs text-brand-700 font-medium hover:underline">
              Import New
            </button>
          </div>
          {recent_imports.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">No CSV/Excel imports yet.</p>
          ) : (
            <div className="space-y-3">
              {recent_imports.map((job) => (
                <div key={job.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-xs font-semibold text-slate-800 truncate">{job.filename}</div>
                  <div className="text-[11px] text-slate-500 mt-1 flex gap-2">
                    <span className="text-emerald-700 font-medium">+{job.imported} imported</span>
                    <span className="text-slate-400">•</span>
                    <span>{job.skipped} skipped</span>
                    <span className="text-slate-400">•</span>
                    <span>{job.merged} merged</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">{job.created_at}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Research & Audits */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <Globe className="w-4 h-4 text-indigo-600" />
              <span>Recent Website Audits</span>
            </h2>
            <button onClick={() => onNavigate('leads')} className="text-xs text-brand-700 font-medium hover:underline">
              Audit a Site
            </button>
          </div>
          {recent_research_jobs.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">No recent website audits.</p>
          ) : (
            <div className="space-y-3">
              {recent_research_jobs.map((job) => (
                <div key={job.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-xs font-semibold text-slate-800 truncate">{job.company_name}</div>
                  <div className="text-[11px] text-slate-600 mt-0.5 truncate">{job.log || 'Audit completed'}</div>
                  <div className="text-[10px] text-slate-400 mt-1">{job.created_at}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
