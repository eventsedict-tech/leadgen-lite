import React from 'react';
import {
  LayoutDashboard, Users, Search, UploadCloud,
  ShieldBan, Settings, LogOut, Sparkles, Send
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  onOpenNewLead: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, onOpenNewLead }) => {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'leads', label: 'CRM Leads', icon: Users },
    { id: 'outreach', label: 'Outreach Hub', icon: Send, highlight: true },
    { id: 'discovery', label: 'Internet Discovery', icon: Search },
    { id: 'import-export', label: 'Import & Export', icon: UploadCloud },
    { id: 'suppression', label: 'Suppression List', icon: ShieldBan },
    { id: 'settings', label: 'Integrations & Settings', icon: Settings },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-brand-700 flex items-center justify-center text-white shadow-md font-bold text-xl">
              <Sparkles className="w-5 h-5 text-blue-200" />
            </div>
            <div>
              <span className="text-xl font-bold bg-gradient-to-r from-brand-800 to-brand-600 bg-clip-text text-transparent">
                LeadGen Lite
              </span>
              <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-xs font-medium bg-blue-50 text-brand-700 border border-blue-200 rounded-full">
                B2B Lead Finder & CRM
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentTab(item.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-50 text-brand-700 border-b-2 border-brand-700 font-bold'
                      : item.highlight
                      ? 'text-emerald-700 bg-emerald-50/60 hover:bg-emerald-100 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-brand-600' : item.highlight ? 'text-emerald-600' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                  {item.highlight && !isActive && (
                    <span className="px-1.5 py-0.2 text-[10px] bg-emerald-200 text-emerald-900 font-bold rounded-full">
                      New
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={onOpenNewLead}
              className="px-3.5 py-1.5 bg-brand-700 hover:bg-brand-800 text-white rounded-md text-sm font-medium shadow-sm transition-colors flex items-center gap-1.5"
            >
              <span>+ New Lead</span>
            </button>

            {user && (
              <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                <div className="hidden lg:block text-right">
                  <div className="text-xs font-semibold text-slate-800">{user.full_name}</div>
                  <div className="text-[11px] text-slate-500">{user.email}</div>
                </div>
                <button
                  onClick={logout}
                  title="Logout"
                  className="p-1.5 text-slate-400 hover:text-red-600 rounded-md hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Mobile Navigation bar */}
        <div className="md:hidden flex overflow-x-auto py-2 space-x-1 border-t border-slate-100">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`flex items-center gap-1.5 whitespace-nowrap px-3 py-1.5 rounded-md text-xs font-medium ${
                  isActive ? 'bg-brand-100 text-brand-800' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.label}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
