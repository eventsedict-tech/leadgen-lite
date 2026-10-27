import React, { useState, useEffect } from 'react';
import {
  Mail, MessageSquare, Share2, ExternalLink, Send, CheckCircle2,
  Sparkles, Search, Filter, Globe, Phone, Copy, Check, Clock,
  AlertCircle, ArrowUpRight
} from 'lucide-react';
import { Lead, CRMStage, OutreachChannelStatus, OutreachDraft } from '../../types';
import { api } from '../../services/api';
import { LeadDrawer } from '../leads/LeadDrawer';

export const OutreachView: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [channelFilter, setChannelFilter] = useState<'all' | 'email' | 'whatsapp' | 'linkedin' | 'uncontacted'>('all');
  const [language, setLanguage] = useState<'en' | 'hi'>('en');
  const [channelStatus, setChannelStatus] = useState<OutreachChannelStatus | null>(null);

  // Selected lead for full drawer
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  // Quick action feedback
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [dispatchingLeadId, setDispatchingLeadId] = useState<number | null>(null);
  const [copiedNoteId, setCopiedNoteId] = useState<number | null>(null);

  useEffect(() => {
    loadLeads();
    loadChannelStatus();
  }, []);

  const loadLeads = async () => {
    try {
      setLoading(true);
      const res = await api.listLeads({ page_size: 100 });
      setLeads(res.items);
    } catch (err: any) {
      alert(err.message || 'Failed to load leads');
    } finally {
      setLoading(false);
    }
  };

  const loadChannelStatus = async () => {
    try {
      const status = await api.getOutreachChannelStatus();
      setChannelStatus(status);
    } catch {
      // Non-blocking
    }
  };

  // Filter leads based on search and channel filter
  const filteredLeads = leads.filter((l) => {
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      l.company_name.toLowerCase().includes(q) ||
      (l.city && l.city.toLowerCase().includes(q)) ||
      (l.general_business_email && l.general_business_email.toLowerCase().includes(q)) ||
      (l.public_business_phone && l.public_business_phone.includes(q));

    if (!matchesSearch) return false;

    if (channelFilter === 'email') return Boolean(l.general_business_email);
    if (channelFilter === 'whatsapp') return Boolean(l.public_business_phone);
    if (channelFilter === 'linkedin') return Boolean(l.company_linkedin_url || l.company_name);
    if (channelFilter === 'uncontacted') return l.crm_status !== 'Contacted' && l.crm_status !== 'Converted';

    return true;
  });

  // 1-Click Mail App dispatch
  const handleQuickMailApp = async (lead: Lead) => {
    if (!lead.general_business_email) {
      alert(`No email address listed for ${lead.company_name}. You can add one by editing the lead.`);
      return;
    }

    setDispatchingLeadId(lead.id);
    try {
      const subject = language === 'hi'
        ? `${lead.company_name} ke digital marketing avsar ke bare me`
        : `Digital Growth & Marketing Opportunity for ${lead.company_name}`;

      const pitch = language === 'hi'
        ? `Namaste ${lead.publicly_listed_contact_name || lead.company_name} Team,\n\nMaine aapki company ${lead.company_name} ki online presence review ki. Humne aapke business ke liye targeted marketing opportunity dekhi hai jisse aapke customers aur sales badh sakte hain.\n\nKya hum is hafte ek brief 10-minute call schedule kar sakte hain?\n\nDhanyawad,\nLeadGen Lite Team`
        : `Hi ${lead.publicly_listed_contact_name || 'Team'},\n\nI recently analyzed ${lead.company_name}'s web presence and identified clear opportunities to expand your digital client acquisition.\n\nWould you be open to a quick 10-minute discussion this week to review the actionable findings?\n\nBest regards,\nLeadGen Lite Team`;

      // Log contact in CRM & advance stage
      await api.sendEmailOutreach(lead.id, subject, pitch, lead.general_business_email);

      // Open local email client
      const mailto = `mailto:${encodeURIComponent(lead.general_business_email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(pitch)}`;
      window.location.href = mailto;

      setActionNotice(`Email opened in your Mail app & ${lead.company_name} marked as Contacted in CRM!`);
      loadLeads();
    } catch (err: any) {
      alert(err.message || 'Failed to dispatch email');
    } finally {
      setDispatchingLeadId(null);
      setTimeout(() => setActionNotice(null), 5000);
    }
  };

  // 1-Click WhatsApp dispatch
  const handleQuickWhatsApp = async (lead: Lead) => {
    if (!lead.public_business_phone) {
      alert(`No phone number listed for ${lead.company_name}.`);
      return;
    }

    setDispatchingLeadId(lead.id);
    try {
      const message = language === 'hi'
        ? `Namaste ${lead.publicly_listed_contact_name || lead.company_name} Team, maine aapki company ${lead.company_name} ki online presence dekhi. Humne aapke digital growth ke liye actionable insights identify kiye hain. Kya hum call par connect kar sakte hain?`
        : `Hi ${lead.publicly_listed_contact_name || lead.company_name} Team, I noticed ${lead.company_name} has high-potential digital marketing growth opportunities. Would you be open to a brief conversation this week?`;

      const res = await api.sendWhatsAppOutreach(lead.id, message, lead.public_business_phone);

      if (res.link) {
        window.open(res.link, '_blank');
      }

      setActionNotice(`WhatsApp chat opened & ${lead.company_name} marked as Contacted in CRM!`);
      loadLeads();
    } catch (err: any) {
      alert(err.message || 'Failed to dispatch WhatsApp');
    } finally {
      setDispatchingLeadId(null);
      setTimeout(() => setActionNotice(null), 5000);
    }
  };

  // 1-Click LinkedIn Note & Search
  const handleQuickLinkedIn = async (lead: Lead) => {
    setDispatchingLeadId(lead.id);
    try {
      const note = language === 'hi'
        ? `Namaste ${lead.publicly_listed_contact_name || lead.company_name}! Humne aapke business ke liye actionable digital growth strategy prepare ki hai. Connect karke discuss karein?`
        : `Hi ${lead.publicly_listed_contact_name || 'there'}! I reviewed ${lead.company_name}'s web presence and identified actionable marketing opportunities. Would love to connect and share findings.`;

      // Copy note to clipboard
      await navigator.clipboard.writeText(note);
      setCopiedNoteId(lead.id);

      const res = await api.sendLinkedInOutreach(lead.id, note, 'connection_note');

      if (res.link) {
        window.open(res.link, '_blank');
      }

      setActionNotice(`LinkedIn note copied to clipboard & ${lead.company_name} marked as Contacted (3-day follow-up scheduled)!`);
      loadLeads();
    } catch (err: any) {
      alert(err.message || 'Failed to open LinkedIn');
    } finally {
      setDispatchingLeadId(null);
      setTimeout(() => {
        setActionNotice(null);
        setCopiedNoteId(null);
      }, 5000);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Send className="w-5 h-5 text-brand-700" />
              <span>Multi-Channel Outreach Hub</span>
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Directly engage verified B2B leads across <strong>Email</strong>, <strong>WhatsApp</strong>, and <strong>LinkedIn</strong> with 1-click personalized pitches.
            </p>
          </div>

          {/* Language Selector */}
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <span className="text-xs font-semibold text-slate-600">Draft Language:</span>
            <div className="bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs flex">
              <button
                onClick={() => setLanguage('en')}
                className={`px-3 py-1 rounded font-medium transition-colors ${
                  language === 'en' ? 'bg-white text-brand-800 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLanguage('hi')}
                className={`px-3 py-1 rounded font-medium transition-colors ${
                  language === 'hi' ? 'bg-white text-brand-800 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                हिंदी (Hindi)
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Floating Action Notice Banner */}
      {actionNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 text-xs font-semibold flex items-center gap-2 shadow-sm animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{actionNotice}</span>
        </div>
      )}

      {/* 3 Active Channel Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Email Outreach */}
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-bold text-slate-900 text-sm">
              <div className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
                <Mail className="w-4 h-4" />
              </div>
              <span>Email Outreach</span>
            </div>
            <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded-full border border-emerald-200">
              {channelStatus?.email_smtp_ready ? 'API / SMTP Active' : 'Mail App Ready'}
            </span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            1-Click <strong>Mail App</strong> opens your local Gmail/Outlook pre-filled, or use <strong>Resend API</strong> for cloud automated sending.
          </p>
          <div className="text-[11px] text-blue-700 font-medium pt-1">
            ✓ Pre-filled Subject & Proposal Pitch
          </div>
        </div>

        {/* WhatsApp Outreach */}
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-bold text-slate-900 text-sm">
              <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
                <MessageSquare className="w-4 h-4" />
              </div>
              <span>WhatsApp Outreach</span>
            </div>
            <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded-full border border-emerald-200">
              wa.me Direct Ready
            </span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            1-Click <strong>Click-to-Chat</strong> opens WhatsApp Web or App with pre-filled personalized message to prospects' verified phone.
          </p>
          <div className="text-[11px] text-emerald-700 font-medium pt-1">
            ✓ Automatic CRM stage update to Contacted
          </div>
        </div>

        {/* LinkedIn Outreach */}
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-bold text-slate-900 text-sm">
              <div className="p-1.5 bg-blue-50 text-[#0a66c2] rounded-lg">
                <Share2 className="w-4 h-4" />
              </div>
              <span>LinkedIn Outreach</span>
            </div>
            <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded-full border border-emerald-200">
              100% Ready (Zero Setup)
            </span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Generates compliant notes strictly under 295 characters, copies pitch to clipboard, opens profile search, and sets a 3-day reminder.
          </p>
          <div className="text-[11px] text-indigo-700 font-medium pt-1">
            ✓ 3-Day Follow-Up Task Auto-Scheduled
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search leads by company, email, phone, city..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:ring-1 focus:ring-brand-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto">
          {[
            { id: 'all', label: `All (${leads.length})` },
            { id: 'uncontacted', label: 'Ready to Contact' },
            { id: 'email', label: '✉️ Has Email' },
            { id: 'whatsapp', label: '💬 Has Phone' },
            { id: 'linkedin', label: '🔗 LinkedIn' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setChannelFilter(tab.id as any)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                channelFilter === tab.id
                  ? 'bg-brand-700 text-white font-bold shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Leads List with Direct Outreach Action Buttons */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-700 mx-auto mb-2"></div>
            <p className="text-xs">Loading leads for outreach...</p>
          </div>
        ) : filteredLeads.length === 0 ? (
          <div className="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200 space-y-2">
            <AlertCircle className="w-8 h-8 mx-auto text-slate-300" />
            <p className="text-xs font-semibold text-slate-600">No leads match the selected outreach filter.</p>
            <p className="text-[11px] text-slate-400">Use Internet Discovery or Import to add businesses with contact details.</p>
          </div>
        ) : (
          filteredLeads.map((lead) => (
            <div
              key={lead.id}
              className="p-5 bg-white rounded-xl border border-slate-200 shadow-sm hover:border-brand-300 transition-all space-y-4"
            >
              {/* Lead Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 text-sm">{lead.company_name}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      lead.crm_status === 'Contacted' ? 'bg-emerald-100 text-emerald-800' :
                      lead.crm_status === 'New' ? 'bg-blue-100 text-blue-800' :
                      'bg-slate-100 text-slate-700'
                    }`}>
                      {lead.crm_status}
                    </span>
                    <span className="px-1.5 py-0.5 bg-amber-50 text-amber-800 border border-amber-200 rounded text-[10px] font-bold">
                      Score: {lead.lead_score}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 flex flex-wrap gap-2 mt-1">
                    {lead.city && <span>📍 {lead.city}</span>}
                    {lead.industry && <span>• {lead.industry}</span>}
                    {lead.official_website && (
                      <a
                        href={lead.official_website}
                        target="_blank"
                        rel="noreferrer"
                        className="text-brand-700 hover:underline flex items-center gap-0.5"
                      >
                        <Globe className="w-3 h-3" />
                        <span>{lead.normalized_domain || 'Website'}</span>
                      </a>
                    )}
                  </div>
                </div>

                {/* Service Opportunity badge */}
                <div className="text-left sm:text-right">
                  <span className="text-[11px] font-semibold text-slate-500">Service Pitch: </span>
                  <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                    {lead.recommended_service || lead.marketing_opportunity || 'Digital Marketing Opportunity'}
                  </span>
                </div>
              </div>

              {/* Verified Contact Details & Direct 1-Click Outreach Buttons */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                {/* 1. Email Outreach Action Box */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex flex-col justify-between space-y-2">
                  <div>
                    <div className="text-[11px] font-bold text-slate-700 flex items-center gap-1">
                      <Mail className="w-3.5 h-3.5 text-blue-600" />
                      <span>Email Outreach</span>
                    </div>
                    <div className="text-xs text-slate-800 font-medium truncate mt-0.5" title={lead.general_business_email || ''}>
                      {lead.general_business_email || <span className="text-slate-400 italic">No email listed</span>}
                    </div>
                  </div>
                  <button
                    onClick={() => handleQuickMailApp(lead)}
                    disabled={!lead.general_business_email || dispatchingLeadId === lead.id}
                    className="w-full py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-sm"
                  >
                    <Send className="w-3 h-3" />
                    <span>Send Email (Mail App)</span>
                  </button>
                </div>

                {/* 2. WhatsApp Outreach Action Box */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex flex-col justify-between space-y-2">
                  <div>
                    <div className="text-[11px] font-bold text-slate-700 flex items-center gap-1">
                      <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />
                      <span>WhatsApp Outreach</span>
                    </div>
                    <div className="text-xs text-slate-800 font-medium truncate mt-0.5">
                      {lead.public_business_phone || <span className="text-slate-400 italic">No phone listed</span>}
                    </div>
                  </div>
                  <button
                    onClick={() => handleQuickWhatsApp(lead)}
                    disabled={!lead.public_business_phone || dispatchingLeadId === lead.id}
                    className="w-full py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white rounded text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-sm"
                  >
                    <MessageSquare className="w-3 h-3" />
                    <span>Send WhatsApp (wa.me)</span>
                  </button>
                </div>

                {/* 3. LinkedIn Outreach Action Box */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex flex-col justify-between space-y-2">
                  <div>
                    <div className="text-[11px] font-bold text-slate-700 flex items-center gap-1">
                      <Share2 className="w-3.5 h-3.5 text-[#0a66c2]" />
                      <span>LinkedIn Outreach</span>
                    </div>
                    <div className="text-xs text-slate-800 font-medium truncate mt-0.5">
                      {lead.company_linkedin_url ? 'Profile Verified' : `${lead.company_name} Search`}
                    </div>
                  </div>
                  <button
                    onClick={() => handleQuickLinkedIn(lead)}
                    disabled={dispatchingLeadId === lead.id}
                    className="w-full py-1.5 bg-[#0a66c2] hover:bg-[#004182] text-white rounded text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-sm"
                  >
                    {copiedNoteId === lead.id ? <Check className="w-3 h-3 text-emerald-300" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedNoteId === lead.id ? 'Copied & Opening!' : 'Copy Note & Open LinkedIn'}</span>
                  </button>
                </div>
              </div>

              {/* Bottom Row: Customize in Lead Drawer */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                <span className="text-slate-400 text-[11px]">
                  Want AI-generated customized pitches or detailed SEO evidence?
                </span>
                <button
                  onClick={() => setSelectedLead(lead)}
                  className="text-brand-700 hover:text-brand-900 font-bold flex items-center gap-1 hover:underline"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-500" />
                  <span>Open Full Outreach Studio</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Lead Drawer Modal */}
      {selectedLead && (
        <LeadDrawer
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onLeadUpdated={() => {
            loadLeads();
          }}
        />
      )}
    </div>
  );
};
