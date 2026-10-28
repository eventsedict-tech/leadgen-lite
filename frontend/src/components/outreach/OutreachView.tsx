import React, { useState, useEffect } from 'react';
import {
  Mail, MessageSquare, Share2, ExternalLink, Send, CheckCircle2,
  Sparkles, Search, Filter, Globe, Phone, Copy, Check, Clock,
  AlertCircle, ArrowUpRight, CheckSquare, Square, Users, Play,
  Plus, RefreshCw, ChevronLeft, ChevronRight, SkipForward,
  ListOrdered, BarChart3, X
} from 'lucide-react';
import {
  Lead, CRMStage, OutreachChannelStatus, OutreachDraft,
  Campaign, BulkOutreachResponse
} from '../../types';
import { api } from '../../services/api';
import { LeadDrawer } from '../leads/LeadDrawer';

export const OutreachView: React.FC = () => {
  // Main Navigation within Outreach Hub
  const [activeSubTab, setActiveSubTab] = useState<'leads' | 'whatsapp_runner' | 'linkedin_runner' | 'campaigns'>('leads');

  // Leads & Status
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [channelFilter, setChannelFilter] = useState<'all' | 'email' | 'whatsapp' | 'linkedin' | 'uncontacted'>('all');
  const [language, setLanguage] = useState<'en' | 'hi'>('en');
  const [channelStatus, setChannelStatus] = useState<OutreachChannelStatus | null>(null);

  // Multi-Selection State
  const [selectedLeadIds, setSelectedLeadIds] = useState<number[]>([]);

  // Selected lead for full single drawer
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  // Quick action feedback
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [dispatchingLeadId, setDispatchingLeadId] = useState<number | null>(null);
  const [copiedNoteId, setCopiedNoteId] = useState<number | null>(null);

  // Bulk Email Modal State
  const [isBulkEmailOpen, setIsBulkEmailOpen] = useState(false);
  const [bulkEmailLang, setBulkEmailLang] = useState<'en' | 'hi'>('en');
  const [bulkEmailSubject, setBulkEmailSubject] = useState('');
  const [bulkEmailBody, setBulkEmailBody] = useState('');
  const [isSendingBulkEmail, setIsSendingBulkEmail] = useState(false);
  const [bulkEmailResponse, setBulkEmailResponse] = useState<BulkOutreachResponse | null>(null);

  // WhatsApp Queue Runner State
  const [waQueue, setWaQueue] = useState<Lead[]>([]);
  const [waIndex, setWaIndex] = useState(0);
  const [waMessage, setWaMessage] = useState('');
  const [waProcessedIds, setWaProcessedIds] = useState<number[]>([]);

  // LinkedIn Queue Runner State
  const [liQueue, setLiQueue] = useState<Lead[]>([]);
  const [liIndex, setLiIndex] = useState(0);
  const [liNote, setLiNote] = useState('');
  const [liProcessedIds, setLiProcessedIds] = useState<number[]>([]);

  // Campaigns State
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState(false);
  const [isCreateCampaignOpen, setIsCreateCampaignOpen] = useState(false);
  const [newCampaignName, setNewCampaignName] = useState('');
  const [newCampaignChannel, setNewCampaignChannel] = useState('cold_email');
  const [newCampaignLimit, setNewCampaignLimit] = useState(50);
  const [runningCampaignId, setRunningCampaignId] = useState<number | null>(null);

  useEffect(() => {
    loadLeads();
    loadChannelStatus();
    loadCampaigns();
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

  const loadCampaigns = async () => {
    try {
      setLoadingCampaigns(true);
      const res = await api.listCampaigns();
      setCampaigns(res);
    } catch {
      // Non-blocking
    } finally {
      setLoadingCampaigns(false);
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

  // Multi-Selection Toggles
  const toggleSelectLead = (id: number) => {
    setSelectedLeadIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSelectAllFiltered = () => {
    if (selectedLeadIds.length === filteredLeads.length) {
      setSelectedLeadIds([]);
    } else {
      setSelectedLeadIds(filteredLeads.map((l) => l.id));
    }
  };

  const handleSelectWithEmail = () => {
    const emailLeads = filteredLeads.filter((l) => l.general_business_email).map((l) => l.id);
    setSelectedLeadIds(emailLeads);
  };

  const handleSelectWithPhone = () => {
    const phoneLeads = filteredLeads.filter((l) => l.public_business_phone).map((l) => l.id);
    setSelectedLeadIds(phoneLeads);
  };

  // Generate Personalized WhatsApp default text for queue item
  const getWhatsAppDefaultText = (lead: Lead, lang: 'en' | 'hi') => {
    if (lang === 'hi') {
      return `Namaste ${lead.publicly_listed_contact_name || lead.company_name} Team,\nMaine aapki company ${lead.company_name} ki online presence dekhi. Humne aapke digital growth aur lead acquisition ke liye actionable strategy plan ki hai.\nKya hum is hafte ek 10-minute call par connect kar sakte hain?`;
    }
    return `Hi ${lead.publicly_listed_contact_name || lead.company_name} Team,\nI analyzed ${lead.company_name}'s web presence and identified clear opportunities to expand your digital client acquisition.\nWould you be open to a quick 10-minute conversation this week?`;
  };

  // Generate Personalized LinkedIn default note for queue item
  const getLinkedInDefaultNote = (lead: Lead, lang: 'en' | 'hi') => {
    if (lang === 'hi') {
      return `Namaste ${lead.publicly_listed_contact_name || lead.company_name}! Humne aapke business ke liye actionable digital growth strategy prepare ki hai. Connect karke findings share karein?`;
    }
    return `Hi ${lead.publicly_listed_contact_name || 'there'}! I reviewed ${lead.company_name}'s web presence and identified actionable marketing opportunities. Would love to connect and share findings.`;
  };

  // Start WhatsApp Bulk Runner
  const handleStartWhatsAppQueue = () => {
    const queueLeads = leads.filter((l) => selectedLeadIds.includes(l.id) && l.public_business_phone);
    if (queueLeads.length === 0) {
      alert('Please select at least one lead with a verified phone number.');
      return;
    }
    setWaQueue(queueLeads);
    setWaIndex(0);
    setWaProcessedIds([]);
    setWaMessage(getWhatsAppDefaultText(queueLeads[0], language));
    setActiveSubTab('whatsapp_runner');
  };

  // Start LinkedIn Bulk Runner
  const handleStartLinkedInQueue = () => {
    const queueLeads = leads.filter((l) => selectedLeadIds.includes(l.id));
    if (queueLeads.length === 0) {
      alert('Please select at least one lead for LinkedIn outreach.');
      return;
    }
    setLiQueue(queueLeads);
    setLiIndex(0);
    setLiProcessedIds([]);
    setLiNote(getLinkedInDefaultNote(queueLeads[0], language));
    setActiveSubTab('linkedin_runner');
  };

  // Next step in WhatsApp Runner
  const handleSendAndNextWhatsApp = async () => {
    const current = waQueue[waIndex];
    if (!current) return;

    try {
      const res = await api.sendWhatsAppOutreach(current.id, waMessage, current.public_business_phone || undefined);
      if (res.link) {
        window.open(res.link, '_blank');
      }
      setWaProcessedIds((prev) => [...prev, current.id]);

      // Move to next
      if (waIndex + 1 < waQueue.length) {
        const nextLead = waQueue[waIndex + 1];
        setWaIndex(waIndex + 1);
        setWaMessage(getWhatsAppDefaultText(nextLead, language));
      } else {
        setActionNotice(`All ${waQueue.length} leads in WhatsApp Queue completed!`);
        loadLeads();
      }
    } catch (err: any) {
      alert(err.message || 'Failed to dispatch WhatsApp');
    }
  };

  const handleSkipWhatsApp = () => {
    if (waIndex + 1 < waQueue.length) {
      const nextLead = waQueue[waIndex + 1];
      setWaIndex(waIndex + 1);
      setWaMessage(getWhatsAppDefaultText(nextLead, language));
    }
  };

  // Next step in LinkedIn Runner
  const handleCopyAndNextLinkedIn = async () => {
    const current = liQueue[liIndex];
    if (!current) return;

    try {
      await navigator.clipboard.writeText(liNote);
      const res = await api.sendLinkedInOutreach(current.id, liNote, 'connection_note');
      if (res.link) {
        window.open(res.link, '_blank');
      }
      setLiProcessedIds((prev) => [...prev, current.id]);

      // Move to next
      if (liIndex + 1 < liQueue.length) {
        const nextLead = liQueue[liIndex + 1];
        setLiIndex(liIndex + 1);
        setLiNote(getLinkedInDefaultNote(nextLead, language));
      } else {
        setActionNotice(`All ${liQueue.length} LinkedIn outreach notes completed!`);
        loadLeads();
      }
    } catch (err: any) {
      alert(err.message || 'Failed to open LinkedIn');
    }
  };

  const handleSkipLinkedIn = () => {
    if (liIndex + 1 < liQueue.length) {
      const nextLead = liQueue[liIndex + 1];
      setLiIndex(liIndex + 1);
      setLiNote(getLinkedInDefaultNote(nextLead, language));
    }
  };

  // Execute Bulk Email Dispatch
  const handleExecuteBulkEmail = async () => {
    const validEmails = leads.filter((l) => selectedLeadIds.includes(l.id) && l.general_business_email);
    if (validEmails.length === 0) {
      alert('None of the selected leads have an email address listed.');
      return;
    }

    setIsSendingBulkEmail(true);
    setBulkEmailResponse(null);

    try {
      const res = await api.bulkSendEmail({
        lead_ids: validEmails.map((l) => l.id),
        language: bulkEmailLang,
        subject_override: bulkEmailSubject.trim() || undefined,
        message_body_override: bulkEmailBody.trim() || undefined
      });
      setBulkEmailResponse(res);
      loadLeads();
    } catch (err: any) {
      alert(err.message || 'Bulk email dispatch failed');
    } finally {
      setIsSendingBulkEmail(false);
    }
  };

  // Create Campaign
  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCampaignName.trim()) {
      alert('Please enter a campaign name.');
      return;
    }
    if (selectedLeadIds.length === 0) {
      alert('Please select at least one lead for this campaign.');
      return;
    }

    try {
      await api.createCampaign({
        name: newCampaignName.trim(),
        channel: newCampaignChannel,
        lead_ids: selectedLeadIds,
        language,
        sending_limit_per_day: newCampaignLimit
      });
      setIsCreateCampaignOpen(false);
      setNewCampaignName('');
      loadCampaigns();
      setActiveSubTab('campaigns');
      setActionNotice('New campaign created with pre-generated personalized pitches!');
      setTimeout(() => setActionNotice(null), 5000);
    } catch (err: any) {
      alert(err.message || 'Failed to create campaign');
    }
  };

  // Run Campaign
  const handleStartCampaign = async (campaignId: number) => {
    setRunningCampaignId(campaignId);
    try {
      const res = await api.startCampaign(campaignId);
      alert(res.message);
      loadCampaigns();
      loadLeads();
    } catch (err: any) {
      alert(err.message || 'Failed to start campaign');
    } finally {
      setRunningCampaignId(null);
    }
  };

  // 1-Click single Mail App dispatch
  const handleQuickMailApp = async (lead: Lead) => {
    if (!lead.general_business_email) {
      alert(`No email address listed for ${lead.company_name}.`);
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

      await api.sendEmailOutreach(lead.id, subject, pitch, lead.general_business_email);
      const mailto = `mailto:${encodeURIComponent(lead.general_business_email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(pitch)}`;
      window.location.href = mailto;

      setActionNotice(`Email opened in Mail client & ${lead.company_name} marked as Contacted in CRM!`);
      loadLeads();
    } catch (err: any) {
      alert(err.message || 'Failed to dispatch email');
    } finally {
      setDispatchingLeadId(null);
      setTimeout(() => setActionNotice(null), 5000);
    }
  };

  // 1-Click single WhatsApp dispatch
  const handleQuickWhatsApp = async (lead: Lead) => {
    if (!lead.public_business_phone) {
      alert(`No phone number listed for ${lead.company_name}.`);
      return;
    }
    setDispatchingLeadId(lead.id);
    try {
      const message = getWhatsAppDefaultText(lead, language);
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

  // 1-Click single LinkedIn Note
  const handleQuickLinkedIn = async (lead: Lead) => {
    setDispatchingLeadId(lead.id);
    try {
      const note = getLinkedInDefaultNote(lead, language);
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
    <div className="space-y-6 pb-24">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Send className="w-5 h-5 text-brand-700" />
              <span>Multi-Channel Outreach Hub</span>
              <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full">
                Bulk Enabled
              </span>
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Direct and <strong>Bulk Outreach</strong> across <strong>Email</strong>, <strong>WhatsApp</strong>, and <strong>LinkedIn</strong> with automated CRM stage tracking.
            </p>
          </div>

          {/* Sub-Navigation Tabs */}
          <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-medium">
            <button
              onClick={() => setActiveSubTab('leads')}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeSubTab === 'leads' ? 'bg-white text-brand-800 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Leads & Bulk Action</span>
            </button>
            <button
              onClick={() => {
                if (waQueue.length === 0) handleStartWhatsAppQueue();
                else setActiveSubTab('whatsapp_runner');
              }}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeSubTab === 'whatsapp_runner' ? 'bg-white text-emerald-800 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />
              <span>WhatsApp Runner</span>
            </button>
            <button
              onClick={() => {
                if (liQueue.length === 0) handleStartLinkedInQueue();
                else setActiveSubTab('linkedin_runner');
              }}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeSubTab === 'linkedin_runner' ? 'bg-white text-[#0a66c2] shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Share2 className="w-3.5 h-3.5 text-[#0a66c2]" />
              <span>LinkedIn Runner</span>
            </button>
            <button
              onClick={() => setActiveSubTab('campaigns')}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeSubTab === 'campaigns' ? 'bg-white text-brand-800 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Saved Campaigns ({campaigns.length})</span>
            </button>
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

      {/* SUB-TAB 1: LEADS & BULK ACTION */}
      {activeSubTab === 'leads' && (
        <>
          {/* 3 Active Channel Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-slate-900 text-sm">
                  <div className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
                    <Mail className="w-4 h-4" />
                  </div>
                  <span>Bulk Email Outreach</span>
                </div>
                <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded-full border border-emerald-200">
                  {channelStatus?.email_smtp_ready ? 'Resend / SMTP Active' : 'Mail App Ready'}
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Send personalized emails in batch with live progress tracking or launch native Mail client for selected prospects.
              </p>
            </div>

            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-slate-900 text-sm">
                  <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
                    <MessageSquare className="w-4 h-4" />
                  </div>
                  <span>Bulk WhatsApp Runner</span>
                </div>
                <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded-full border border-emerald-200">
                  Interactive Queue
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Step-by-step assistant that lets you send personalized WhatsApp messages to 20+ leads in 2 minutes without blocking.
              </p>
            </div>

            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-slate-900 text-sm">
                  <div className="p-1.5 bg-blue-50 text-[#0a66c2] rounded-lg">
                    <Share2 className="w-4 h-4" />
                  </div>
                  <span>Bulk LinkedIn Runner</span>
                </div>
                <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded-full border border-emerald-200">
                  Compliant &lt;295 chars
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Queue assistant that auto-copies short connection notes, opens LinkedIn profiles, and schedules CRM 3-day follow-ups.
              </p>
            </div>
          </div>

          {/* Filter, Search & Selection Helper Bar */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <div className="flex flex-col md:flex-row items-center justify-between gap-3">
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

              {/* Language Switcher */}
              <div className="flex items-center gap-1.5 self-start sm:self-auto text-xs">
                <span className="text-slate-500 font-medium">Pitch Language:</span>
                <div className="bg-slate-100 p-0.5 rounded-lg border border-slate-200 flex">
                  <button
                    onClick={() => setLanguage('en')}
                    className={`px-2.5 py-1 rounded font-medium ${language === 'en' ? 'bg-white text-brand-800 shadow-xs font-bold' : 'text-slate-600'}`}
                  >
                    English
                  </button>
                  <button
                    onClick={() => setLanguage('hi')}
                    className={`px-2.5 py-1 rounded font-medium ${language === 'hi' ? 'bg-white text-brand-800 shadow-xs font-bold' : 'text-slate-600'}`}
                  >
                    हिंदी
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto">
                {[
                  { id: 'all', label: `All (${leads.length})` },
                  { id: 'uncontacted', label: 'Uncontacted' },
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

            {/* Selection Shortcuts */}
            <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2">
                <button
                  onClick={handleSelectAllFiltered}
                  className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded font-medium flex items-center gap-1"
                >
                  {selectedLeadIds.length === filteredLeads.length && filteredLeads.length > 0 ? (
                    <CheckSquare className="w-3.5 h-3.5 text-brand-700" />
                  ) : (
                    <Square className="w-3.5 h-3.5 text-slate-400" />
                  )}
                  <span>Select All ({filteredLeads.length})</span>
                </button>
                <button
                  onClick={handleSelectWithEmail}
                  className="px-2.5 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded font-medium flex items-center gap-1"
                >
                  <Mail className="w-3.5 h-3.5" />
                  <span>Select With Email</span>
                </button>
                <button
                  onClick={handleSelectWithPhone}
                  className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded font-medium flex items-center gap-1"
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Select With Phone</span>
                </button>
                {selectedLeadIds.length > 0 && (
                  <button
                    onClick={() => setSelectedLeadIds([])}
                    className="text-xs text-rose-600 hover:underline font-medium"
                  >
                    Deselect All
                  </button>
                )}
              </div>
              <div className="text-slate-500 font-semibold">
                {selectedLeadIds.length} of {filteredLeads.length} leads selected
              </div>
            </div>
          </div>

          {/* Leads List with Checkboxes and Direct Action Buttons */}
          <div className="space-y-3">
            {loading ? (
              <div className="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-700 mx-auto mb-2"></div>
                <p className="text-xs">Loading leads...</p>
              </div>
            ) : filteredLeads.length === 0 ? (
              <div className="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200 space-y-2">
                <AlertCircle className="w-8 h-8 mx-auto text-slate-300" />
                <p className="text-xs font-semibold text-slate-600">No leads match the selected outreach filter.</p>
              </div>
            ) : (
              filteredLeads.map((lead) => {
                const isSelected = selectedLeadIds.includes(lead.id);
                return (
                  <div
                    key={lead.id}
                    className={`p-5 bg-white rounded-xl border transition-all space-y-4 ${
                      isSelected ? 'border-brand-500 ring-1 ring-brand-400 bg-blue-50/20' : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    {/* Header Row */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectLead(lead.id)}
                          className="w-4 h-4 rounded text-brand-600 border-slate-300 focus:ring-brand-500 cursor-pointer"
                        />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 text-sm">{lead.company_name}</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              lead.crm_status === 'Contacted' ? 'bg-emerald-100 text-emerald-800' :
                              lead.crm_status === 'New' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-700'
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
                      </div>

                      <div className="text-left sm:text-right">
                        <span className="text-[11px] font-semibold text-slate-500">Service Pitch: </span>
                        <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                          {lead.recommended_service || lead.marketing_opportunity || 'Digital Marketing Opportunity'}
                        </span>
                      </div>
                    </div>

                    {/* Verified Contact Details & Direct 1-Click Outreach Buttons */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                      {/* 1. Email Box */}
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
                          className="w-full py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                        >
                          <Send className="w-3 h-3" />
                          <span>Send Email (Mail App)</span>
                        </button>
                      </div>

                      {/* 2. WhatsApp Box */}
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
                          className="w-full py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white rounded text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                        >
                          <MessageSquare className="w-3 h-3" />
                          <span>Send WhatsApp (wa.me)</span>
                        </button>
                      </div>

                      {/* 3. LinkedIn Box */}
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
                          className="w-full py-1.5 bg-[#0a66c2] hover:bg-[#004182] text-white rounded text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                        >
                          {copiedNoteId === lead.id ? <Check className="w-3 h-3 text-emerald-300" /> : <Copy className="w-3 h-3" />}
                          <span>{copiedNoteId === lead.id ? 'Copied & Opening!' : 'Copy Note & Open LinkedIn'}</span>
                        </button>
                      </div>
                    </div>

                    {/* Customize Link */}
                    <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                      <span className="text-slate-400 text-[11px]">
                        Need custom pitch review or specific SEO audit evidence?
                      </span>
                      <button
                        onClick={() => setSelectedLead(lead)}
                        className="text-brand-700 hover:text-brand-900 font-bold flex items-center gap-1 hover:underline"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-blue-500" />
                        <span>Open Outreach Studio</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* STICKY FLOATING BULK ACTIONS BAR */}
          {selectedLeadIds.length > 0 && (
            <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-slate-900 text-white px-6 py-3.5 rounded-2xl shadow-2xl flex flex-wrap items-center gap-4 border border-slate-700">
              <div className="flex items-center gap-2 border-r border-slate-700 pr-4">
                <span className="h-6 w-6 rounded-full bg-brand-500 text-white font-bold text-xs flex items-center justify-center">
                  {selectedLeadIds.length}
                </span>
                <span className="text-xs font-semibold">Leads Selected</span>
              </div>

              {/* Action 1: Bulk Email */}
              <button
                onClick={() => {
                  setBulkEmailResponse(null);
                  setIsBulkEmailOpen(true);
                }}
                className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors"
              >
                <Mail className="w-4 h-4" />
                <span>Bulk Email Dispatch</span>
              </button>

              {/* Action 2: WhatsApp Runner */}
              <button
                onClick={handleStartWhatsAppQueue}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors"
              >
                <MessageSquare className="w-4 h-4" />
                <span>WhatsApp Queue Runner</span>
              </button>

              {/* Action 3: LinkedIn Runner */}
              <button
                onClick={handleStartLinkedInQueue}
                className="px-3.5 py-1.5 bg-[#0a66c2] hover:bg-[#004182] text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors"
              >
                <Share2 className="w-4 h-4" />
                <span>LinkedIn Queue Runner</span>
              </button>

              {/* Action 4: Save as Campaign */}
              <button
                onClick={() => setIsCreateCampaignOpen(true)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Save as Campaign</span>
              </button>

              <button
                onClick={() => setSelectedLeadIds([])}
                className="text-slate-400 hover:text-white p-1"
                title="Clear Selection"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}

      {/* SUB-TAB 2: WHATSAPP BULK RUNNER */}
      {activeSubTab === 'whatsapp_runner' && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="p-1.5 bg-emerald-100 text-emerald-700 rounded-lg">
                  <MessageSquare className="w-5 h-5" />
                </span>
                <h2 className="text-base font-bold text-slate-900">
                  Sequential WhatsApp Outreach Runner
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Fast-track your WhatsApp outreach. Review the pre-filled pitch, click Send to open WhatsApp chat, and automatically move to the next prospect!
              </p>
            </div>

            <button
              onClick={() => setActiveSubTab('leads')}
              className="px-3 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold self-start sm:self-auto"
            >
              ← Back to All Leads
            </button>
          </div>

          {waQueue.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-3">
              <MessageSquare className="w-10 h-10 mx-auto text-emerald-400" />
              <p className="text-sm font-semibold text-slate-700">No leads currently in the WhatsApp Queue.</p>
              <p className="text-xs text-slate-500">Go to the Leads tab, select leads with verified phone numbers, and click "WhatsApp Queue Runner".</p>
              <button
                onClick={() => {
                  handleSelectWithPhone();
                  setActiveSubTab('leads');
                }}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold"
              >
                Select Leads with Phone
              </button>
            </div>
          ) : (
            <div className="max-w-2xl mx-auto space-y-6">
              {/* Queue Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs font-bold text-slate-700">
                  <span>Prospect {waIndex + 1} of {waQueue.length}</span>
                  <span className="text-emerald-700">{waProcessedIds.length} Sent / Processed</span>
                </div>
                <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-600 h-full transition-all duration-300"
                    style={{ width: `${Math.round(((waIndex + 1) / waQueue.length) * 100)}%` }}
                  />
                </div>
              </div>

              {/* Prospect Card */}
              {waQueue[waIndex] && (
                <div className="p-6 bg-slate-50 rounded-xl border border-slate-200 space-y-4 shadow-sm">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                    <div>
                      <div className="text-lg font-bold text-slate-900">{waQueue[waIndex].company_name}</div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        📍 {waQueue[waIndex].city || 'Location not specified'} • {waQueue[waIndex].industry || 'B2B'}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-full">
                        📞 {waQueue[waIndex].public_business_phone}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">Lead Score: {waQueue[waIndex].lead_score}</div>
                    </div>
                  </div>

                  {/* Message Editor */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-700">
                      Personalized WhatsApp Message (Editable):
                    </label>
                    <textarea
                      rows={5}
                      value={waMessage}
                      onChange={(e) => setWaMessage(e.target.value)}
                      className="w-full p-3 bg-white border border-slate-300 rounded-lg text-xs font-mono leading-relaxed focus:ring-1 focus:ring-emerald-500 focus:outline-none"
                    />
                  </div>

                  {/* Action Controls */}
                  <div className="flex items-center justify-between pt-2">
                    <button
                      onClick={handleSkipWhatsApp}
                      className="px-3.5 py-2 border border-slate-300 hover:bg-slate-100 text-slate-600 rounded-lg text-xs font-semibold flex items-center gap-1"
                    >
                      <SkipForward className="w-3.5 h-3.5" />
                      <span>Skip this Prospect</span>
                    </button>

                    <button
                      onClick={handleSendAndNextWhatsApp}
                      className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-md transition-all"
                    >
                      <MessageSquare className="w-4 h-4" />
                      <span>Open WhatsApp & Advance to Next →</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 3: LINKEDIN BULK RUNNER */}
      {activeSubTab === 'linkedin_runner' && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="p-1.5 bg-blue-100 text-[#0a66c2] rounded-lg">
                  <Share2 className="w-5 h-5" />
                </span>
                <h2 className="text-base font-bold text-slate-900">
                  Sequential LinkedIn Connection Note Runner
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Complies with LinkedIn's 300-character limit. Copies note to your clipboard, opens profile search, and auto-schedules 3-day follow-up.
              </p>
            </div>

            <button
              onClick={() => setActiveSubTab('leads')}
              className="px-3 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold self-start sm:self-auto"
            >
              ← Back to All Leads
            </button>
          </div>

          {liQueue.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-3">
              <Share2 className="w-10 h-10 mx-auto text-[#0a66c2]" />
              <p className="text-sm font-semibold text-slate-700">No leads currently in the LinkedIn Queue.</p>
              <p className="text-xs text-slate-500">Go to the Leads tab, select leads, and click "LinkedIn Queue Runner".</p>
              <button
                onClick={() => {
                  handleSelectAllFiltered();
                  setActiveSubTab('leads');
                }}
                className="px-4 py-2 bg-[#0a66c2] hover:bg-[#004182] text-white rounded-lg text-xs font-bold"
              >
                Select Filtered Leads
              </button>
            </div>
          ) : (
            <div className="max-w-2xl mx-auto space-y-6">
              {/* Queue Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs font-bold text-slate-700">
                  <span>Prospect {liIndex + 1} of {liQueue.length}</span>
                  <span className="text-[#0a66c2]">{liProcessedIds.length} Processed / Contacted</span>
                </div>
                <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                  <div
                    className="bg-[#0a66c2] h-full transition-all duration-300"
                    style={{ width: `${Math.round(((liIndex + 1) / liQueue.length) * 100)}%` }}
                  />
                </div>
              </div>

              {/* Prospect Card */}
              {liQueue[liIndex] && (
                <div className="p-6 bg-slate-50 rounded-xl border border-slate-200 space-y-4 shadow-sm">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                    <div>
                      <div className="text-lg font-bold text-slate-900">{liQueue[liIndex].company_name}</div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        Contact: {liQueue[liIndex].publicly_listed_contact_name || 'Business Owner / Decision Maker'}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-bold text-brand-700 bg-blue-100 px-2.5 py-1 rounded-full">
                        {liQueue[liIndex].company_linkedin_url ? 'Profile Verified' : 'Deep Search'}
                      </span>
                      <div className="text-[11px] text-slate-400 mt-1">Lead Score: {liQueue[liIndex].lead_score}</div>
                    </div>
                  </div>

                  {/* Connection Note Editor with Character Counter */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <label className="font-bold text-slate-700">LinkedIn Note (Strictly under 295 chars):</label>
                      <span className={`font-mono text-[11px] ${liNote.length > 295 ? 'text-rose-600 font-bold' : 'text-slate-500'}`}>
                        {liNote.length} / 295 chars
                      </span>
                    </div>
                    <textarea
                      rows={4}
                      value={liNote}
                      onChange={(e) => setLiNote(e.target.value)}
                      className="w-full p-3 bg-white border border-slate-300 rounded-lg text-xs font-mono leading-relaxed focus:ring-1 focus:ring-[#0a66c2] focus:outline-none"
                    />
                  </div>

                  {/* Action Controls */}
                  <div className="flex items-center justify-between pt-2">
                    <button
                      onClick={handleSkipLinkedIn}
                      className="px-3.5 py-2 border border-slate-300 hover:bg-slate-100 text-slate-600 rounded-lg text-xs font-semibold flex items-center gap-1"
                    >
                      <SkipForward className="w-3.5 h-3.5" />
                      <span>Skip this Prospect</span>
                    </button>

                    <button
                      onClick={handleCopyAndNextLinkedIn}
                      className="px-6 py-2.5 bg-[#0a66c2] hover:bg-[#004182] text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-md transition-all"
                    >
                      <Copy className="w-4 h-4" />
                      <span>Copy Note, Open LinkedIn & Next →</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 4: SAVED CAMPAIGNS */}
      {activeSubTab === 'campaigns' && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-brand-700" />
                <span>Outreach Campaigns & Performance Tracking</span>
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Manage automated multi-lead outreach campaigns with safe daily volume limits and delivery statistics.
              </p>
            </div>

            <button
              onClick={() => {
                if (selectedLeadIds.length === 0) {
                  alert('Please select leads in the Leads tab first before creating a campaign.');
                  setActiveSubTab('leads');
                } else {
                  setIsCreateCampaignOpen(true);
                }
              }}
              className="px-4 py-2 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              <span>Create New Campaign ({selectedLeadIds.length} Selected)</span>
            </button>
          </div>

          {loadingCampaigns ? (
            <div className="p-12 text-center text-slate-400">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-700 mx-auto mb-2"></div>
              <p className="text-xs">Loading campaigns...</p>
            </div>
          ) : campaigns.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-3">
              <BarChart3 className="w-10 h-10 mx-auto text-slate-300" />
              <p className="text-sm font-semibold text-slate-700">No campaigns created yet.</p>
              <p className="text-xs text-slate-500">Select leads in the Leads tab and save them as an automated outreach campaign.</p>
              <button
                onClick={() => setActiveSubTab('leads')}
                className="px-4 py-2 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-xs font-bold"
              >
                Go to Leads Selection
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {campaigns.map((c) => (
                <div key={c.id} className="p-5 bg-slate-50 rounded-xl border border-slate-200 shadow-xs space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-2.5">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 text-sm">{c.name}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          c.status === 'completed' ? 'bg-emerald-100 text-emerald-800' :
                          c.status === 'active' ? 'bg-blue-100 text-blue-800 animate-pulse' :
                          'bg-slate-200 text-slate-700'
                        }`}>
                          {c.status.toUpperCase()}
                        </span>
                        <span className="text-xs font-medium text-slate-500 capitalize">
                          Channel: {c.channel.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        Daily Sending Limit: {c.sending_limit_per_day} recipients • Created on {new Date(c.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    {c.channel === 'cold_email' && c.status !== 'completed' && (
                      <button
                        onClick={() => handleStartCampaign(c.id)}
                        disabled={runningCampaignId === c.id}
                        className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors"
                      >
                        <Play className="w-3.5 h-3.5" />
                        <span>{runningCampaignId === c.id ? 'Dispatching...' : 'Dispatch Daily Batch'}</span>
                      </button>
                    )}
                  </div>

                  {/* Progress Stats */}
                  <div className="grid grid-cols-4 gap-2 text-center text-xs">
                    <div className="p-2.5 bg-white rounded-lg border border-slate-200">
                      <div className="text-slate-400 text-[10px] uppercase font-bold">Total</div>
                      <div className="text-base font-bold text-slate-900 mt-0.5">{c.recipient_count}</div>
                    </div>
                    <div className="p-2.5 bg-white rounded-lg border border-slate-200">
                      <div className="text-emerald-600 text-[10px] uppercase font-bold">Sent</div>
                      <div className="text-base font-bold text-emerald-700 mt-0.5">{c.sent_count}</div>
                    </div>
                    <div className="p-2.5 bg-white rounded-lg border border-slate-200">
                      <div className="text-amber-600 text-[10px] uppercase font-bold">Pending</div>
                      <div className="text-base font-bold text-amber-700 mt-0.5">{c.pending_count}</div>
                    </div>
                    <div className="p-2.5 bg-white rounded-lg border border-slate-200">
                      <div className="text-rose-600 text-[10px] uppercase font-bold">Bounced/Failed</div>
                      <div className="text-base font-bold text-rose-700 mt-0.5">{c.failed_count}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* BULK EMAIL DISPATCH MODAL */}
      {isBulkEmailOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 space-y-5 animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-blue-100 text-blue-700 rounded-lg">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Bulk Email Dispatch</h3>
                  <p className="text-xs text-slate-500">
                    Dispatching to {leads.filter((l) => selectedLeadIds.includes(l.id) && l.general_business_email).length} verified email recipients.
                  </p>
                </div>
              </div>
              <button onClick={() => setIsBulkEmailOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Language Switch */}
            <div className="flex items-center justify-between text-xs bg-slate-50 p-3 rounded-lg border border-slate-200">
              <span className="font-semibold text-slate-700">Message Language:</span>
              <div className="flex bg-white rounded border border-slate-300 p-0.5">
                <button
                  type="button"
                  onClick={() => setBulkEmailLang('en')}
                  className={`px-3 py-1 rounded ${bulkEmailLang === 'en' ? 'bg-brand-700 text-white font-bold' : 'text-slate-600'}`}
                >
                  English
                </button>
                <button
                  type="button"
                  onClick={() => setBulkEmailLang('hi')}
                  className={`px-3 py-1 rounded ${bulkEmailLang === 'hi' ? 'bg-brand-700 text-white font-bold' : 'text-slate-600'}`}
                >
                  हिंदी (Hindi)
                </button>
              </div>
            </div>

            {/* Optional Overrides */}
            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Subject Line Override (Optional - Leave blank to use auto-generated personalized subject):
                </label>
                <input
                  type="text"
                  placeholder="e.g. Partnership Opportunity for Digital Growth"
                  value={bulkEmailSubject}
                  onChange={(e) => setBulkEmailSubject(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Message Body Override (Optional - Leave blank to use personalized SEO audit proposal):
                </label>
                <textarea
                  rows={4}
                  placeholder="Leave empty for automatically personalized drafts tailored to each prospect's industry and website findings."
                  value={bulkEmailBody}
                  onChange={(e) => setBulkEmailBody(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono"
                />
              </div>
            </div>

            {/* Bulk Result Summary if Completed */}
            {bulkEmailResponse && (
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
                <div className="font-bold text-slate-900 flex items-center justify-between">
                  <span>Batch Execution Complete:</span>
                  <span className="text-emerald-700 font-bold">
                    {bulkEmailResponse.success_count} / {bulkEmailResponse.total_requested} Successful
                  </span>
                </div>
                <div className="max-h-36 overflow-y-auto space-y-1 pr-1 font-mono text-[11px]">
                  {bulkEmailResponse.results.map((r, i) => (
                    <div key={i} className="flex justify-between items-center py-1 border-b border-slate-100">
                      <span className="truncate max-w-[200px] text-slate-800">{r.company_name}</span>
                      <span className={r.success ? 'text-emerald-600 font-bold' : 'text-rose-600'}>
                        {r.success ? '✓ Sent' : `✗ ${r.error || 'Failed'}`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Modal Actions */}
            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsBulkEmailOpen(false)}
                className="px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
              <button
                type="button"
                onClick={handleExecuteBulkEmail}
                disabled={isSendingBulkEmail}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm"
              >
                <Send className="w-4 h-4" />
                <span>{isSendingBulkEmail ? 'Sending Batch...' : 'Send Bulk Emails'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CREATE CAMPAIGN MODAL */}
      {isCreateCampaignOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <form onSubmit={handleCreateCampaign} className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Create Outreach Campaign</h3>
              <button type="button" onClick={() => setIsCreateCampaignOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Campaign Name:</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Q4 Real Estate SEO Outreach"
                  value={newCampaignName}
                  onChange={(e) => setNewCampaignName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Outreach Channel:</label>
                <select
                  value={newCampaignChannel}
                  onChange={(e) => setNewCampaignChannel(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white"
                >
                  <option value="cold_email">Cold Email</option>
                  <option value="whatsapp_draft">WhatsApp</option>
                  <option value="linkedin_note">LinkedIn Connection Note</option>
                </select>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Daily Sending Limit:</label>
                <input
                  type="number"
                  min={1}
                  max={500}
                  value={newCampaignLimit}
                  onChange={(e) => setNewCampaignLimit(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
                <p className="text-[10px] text-slate-400 mt-0.5">Keeps daily outreach compliant with spam safety limits.</p>
              </div>

              <div className="p-3 bg-blue-50 rounded-lg text-blue-800 text-[11px]">
                <strong>{selectedLeadIds.length} leads</strong> will be enrolled into this campaign with pre-generated personalized pitches.
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsCreateCampaignOpen(false)}
                className="px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-xs font-bold"
              >
                Create Campaign
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Single Lead Drawer Modal */}
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
