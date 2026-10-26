import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Sparkles, AlertCircle, ArrowRight } from 'lucide-react';

export const AuthModal: React.FC = () => {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [orgName, setOrgName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        if (!fullName || !orgName) {
          setError('Please provide your full name and organization name.');
          setLoading(false);
          return;
        }
        await register(email, password, fullName, orgName);
      } else {
        await login(email, password);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setEmail('demo@leadgenlite.local');
    setPassword('DemoPass123!');
    setFullName('Demo Marketer');
    setOrgName('Growth Digital Agency');
    setError(null);
    setLoading(true);
    try {
      await register('demo@leadgenlite.local', 'DemoPass123!', 'Demo Marketer', 'Growth Digital Agency');
    } catch {
      try {
        await login('demo@leadgenlite.local', 'DemoPass123!');
      } catch (err: any) {
        setError(err.message || 'Demo login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-brand-800 to-brand-600 px-6 py-8 text-white text-center">
          <div className="inline-flex p-3 bg-white/10 rounded-full mb-3 shadow-inner">
            <Sparkles className="w-8 h-8 text-blue-200" />
          </div>
          <h2 className="text-2xl font-bold">LeadGen Lite</h2>
          <p className="text-blue-100 text-sm mt-1">
            B2B Lead Finder, SEO Auditor & Outreach CRM
          </p>
        </div>

        {/* Form Body */}
        <div className="p-6">
          <div className="flex border-b border-slate-200 mb-6">
            <button
              onClick={() => { setIsRegister(false); setError(null); }}
              className={`flex-1 pb-3 text-center text-sm font-semibold border-b-2 transition-colors ${
                !isRegister ? 'border-brand-700 text-brand-700' : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setIsRegister(true); setError(null); }}
              className={`flex-1 pb-3 text-center text-sm font-semibold border-b-2 transition-colors ${
                isRegister ? 'border-brand-700 text-brand-700' : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Create Account
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Alex Morgan"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Organization / Agency Name</label>
                  <input
                    type="text"
                    required
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder="e.g. Apex Marketing Solutions"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-brand-700 hover:bg-brand-800 disabled:opacity-50 text-white font-medium rounded-md shadow-sm text-sm transition-colors flex items-center justify-center gap-2 mt-2"
            >
              <span>{loading ? 'Processing...' : isRegister ? 'Register & Launch' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="relative my-5 text-center">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-200"></div></div>
            <span className="relative bg-white px-3 text-xs text-slate-400">or start immediately</span>
          </div>

          <button
            onClick={handleDemoLogin}
            disabled={loading}
            className="w-full py-2 px-4 border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-md transition-colors"
          >
            🚀 Launch with 1-Click Instant Demo Account
          </button>
        </div>
      </div>
    </div>
  );
};
