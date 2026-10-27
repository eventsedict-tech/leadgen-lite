import React, { useState, useEffect } from 'react';
import {
  X, Globe, Mail, Phone, MapPin, Building,
  Sparkles, Check, Copy, ShieldCheck,
  RefreshCw, CheckCircle2, Send, ExternalLink, MessageSquare, Share2, ArrowRight
} from 'lucide-react';
import { Lead, WebsiteAudit, LeadScoreResponse, OutreachDraft, CRMStage, VerificationStatus } from '../../types';
import { api } from '../../services/api';

interface LeadDrawerProps {
  lead: Lead | null;
  onClose: () => void;
  onLeadUpdated: () => void;
}

const CRM_STAGES: CRMStage[] = [
  'New', 'Research Pending', 'Qualified', 'Ready for Review',
  'Contacted', 'Follow-Up', 'Interested', 'Meeting Scheduled',
  'Proposal Sent', 'Converted', 'Not Interested', 'Do Not Contact'
];

export const LeadDrawer: React.FC<LeadDrawerProps> = ({ lead, onClose, onLeadUpdated }) => {
  if (!lead) return null;

  const [activeTab, setActiveTab] = useState<'overview' | 'audit' | 'scoring' | 'outreach' | 'tasks'>('overview');
  const [currentLead, setCurrentLead] = useState<Lead>(lead);
  const [audits, setAudits] = useState<WebsiteAudit[]>([]);
  const [scores, setScores] = useState<LeadScoreResponse[]>([]);
  const [drafts, setDrafts] = useState<OutreachDraft[]>([]);
  
  // State for actions
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [loadingScore, setLoadingScore] = useState(false);
  const [loadingDraft, setLoadingDraft] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Outreach form state
  const [outreachChannel, setOutreachChannel] = useState<string>('cold_email');
  const [outreachLang, setOutreachLang] = useState<string>('en');
  const [copiedDraftId, setCopiedDraftId] = useState<number | null>(null);
  const [dispatchingDraftId, setDispatchingDraftId] = useState<number | null>(null);

  // Task form state
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDueDate, setTaskDueDate] = useState('');
  const [taskNotes, setTaskNotes] = useState('');

  // Manual Override state
  const [showOverride, setShowOverride] = useState(false);
  const [overrideScore, setOverrideScore] = useState(lead.lead_score);
  const [overrideReason, setOverrideReason] = useState('');

  useEffect(() => {
    setCurrentLead(lead);
    loadAudits();
    loadScores();
    loadDrafts();
  }, [lead]);

  const loadAudits = async () => {
    try {
      const res = await api.getLeadAudits(lead.id);
      setAudits(res);
    } catch {}
  };

  const loadScores = async () => {
    try {
      const res = await api.getScoreHistory(lead.id);
      setScores(res);
    } catch {}
  };

  const loadDrafts = async () => {
    try {
      const res = await api.getLeadDrafts(lead.id);
      setDrafts(res);
    } catch {}
  };

  const handleStageChange = async (newStage: CRMStage) => {
    try {
      const updated = await api.updateLead(lead.id, { crm_status: newStage });
      setCurrentLead(updated);
      onLeadUpdated();
      setActionMessage(`Status updated to ${newStage}`);
      setTimeout(() => setActionMessage(null), 3000);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleRunAudit = async () => {
    setLoadingAudit(true);
    setActionMessage(null);
    try {
      const audit = await api.runAudit(lead.id);
      setAudits([audit, ...audits]);
      // Reload lead for opportunities
      const updatedLead = await api.getLead(lead.id);
      setCurrentLead(updatedLead);
      onLeadUpdated();
      setActionMessage('Website audit and opportunity scan completed!');
      // Also trigger score recalculation
      await handleCalculateScore();
    } catch (err: any) {
      alert(`Audit error: ${err.message}`);
    } finally {
      setLoadingAudit(false);
      setTimeout(() => setActionMessage(null), 3500);
    }
  };

  const handleCalculateScore = async () => {
    setLoadingScore(true);
    try {
      const score = await api.calculateScore(lead.id);
      setScores([score, ...scores]);
      const updatedLead = await api.getLead(lead.id);
      setCurrentLead(updatedLead);
      onLeadUpdated();
    } catch (err: any) {
      alert(`Scoring error: ${err.message}`);
    } finally {
      setLoadingScore(false);
    }
  };

  const handleManualOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.overrideScore(lead.id, Number(overrideScore), overrideReason);
      setScores([res, ...scores]);
      const updatedLead = await api.getLead(lead.id);
      setCurrentLead(updatedLead);
      onLeadUpdated();
      setShowOverride(false);
      setActionMessage('Lead score manually updated with audit history.');
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleGenerateDraft = async () => {
    setLoadingDraft(true);
    try {
      const draft = await api.generateOutreach(lead.id, outreachChannel, outreachLang);
      setDrafts([draft, ...drafts]);
      setActionMessage('New personalized outreach draft generated!');
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoadingDraft(false);
      setTimeout(() => setActionMessage(null), 3000);
    }
  };

  const handleCopyDraft = (draft: OutreachDraft) => {
    const textToCopy = draft.subject_line
      ? `Subject: ${draft.subject_line}\n\n${draft.message_body}`
      : draft.message_body;
    navigator.clipboard.writeText(textToCopy);
    setCopiedDraftId(draft.id);
    setTimeout(() => setCopiedDraftId(null), 2500);
  };

  const handleApproveDraft = async (draftId: number, currentApproved: boolean) => {
    try {
      const updated = await api.updateDraft(draftId, { is_approved: !currentApproved });
      setDrafts(drafts.map(d => d.id === draftId ? updated : d));
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleSendEmail = async (draft: OutreachDraft) => {
    setDispatchingDraftId(draft.id);
    try {
      const res = await api.sendEmailOutreach(
        lead.id,
        draft.subject_line || `Partnership Opportunity for ${currentLead.company_name}`,
        draft.message_body,
        currentLead.general_business_email || undefined,
        draft.id
      );
      setActionMessage(res.message);
      const updatedLead = await api.getLead(lead.id);
      setCurrentLead(updatedLead);
      loadDrafts();
      onLeadUpdated();
      if (res.mode !== 'smtp_sent' && res.mode !== 'resend_api_sent' && res.link) {
        window.location.href = res.link;
      }
    } catch (err: any) {
      alert(err.message || 'Failed to dispatch email');
    } finally {
      setDispatchingDraftId(null);
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const handleOpenMailApp = async (draft: OutreachDraft) => {
    try {
      await api.sendEmailOutreach(
        lead.id,
        draft.subject_line || `Partnership Opportunity for ${currentLead.company_name}`,
        draft.message_body,
        currentLead.general_business_email || undefined,
        draft.id
      );
      setActionMessage("Opened local mail client & recorded contact in CRM!");
      const updatedLead = await api.getLead(lead.id);
      setCurrentLead(updatedLead);
      loadDrafts();
      onLeadUpdated();
    } catch {
      // Non-blocking fallback
    }
    const mailto = `mailto:${encodeURIComponent(currentLead.general_business_email || '')}?subject=${encodeURIComponent(draft.subject_line || '')}&body=${encodeURIComponent(draft.message_body)}`;
    window.location.href = mailto;
    setTimeout(() => setActionMessage(null), 4000);
  };

  const handleSendWhatsApp = async (draft: OutreachDraft) => {
    setDispatchingDraftId(draft.id);
    try {
      const res = await api.sendWhatsAppOutreach(
        lead.id,
        draft.message_body,
        currentLead.public_business_phone || undefined,
        draft.id
      );
      setActionMessage(res.message);
      const updatedLead = await api.getLead(lead.id);
      setCurrentLead(updatedLead);
      loadDrafts();
      onLeadUpdated();
      if (res.link) {
        window.open(res.link, '_blank');
      }
    } catch (err: any) {
      alert(err.message || 'Failed to dispatch WhatsApp');
    } finally {
      setDispatchingDraftId(null);
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const handleSendLinkedIn = async (draft: OutreachDraft) => {
    setDispatchingDraftId(draft.id);
    try {
      navigator.clipboard.writeText(draft.message_body);
      const res = await api.sendLinkedInOutreach(
        lead.id,
        draft.message_body,
        draft.channel,
        draft.id
      );
      setActionMessage(res.message + " (Pitch copied to clipboard!)");
      const updatedLead = await api.getLead(lead.id);
      setCurrentLead(updatedLead);
      loadDrafts();
      onLeadUpdated();
      if (res.link) {
        window.open(res.link, '_blank');
      }
    } catch (err: any) {
      alert(err.message || 'Failed to log LinkedIn outreach');
    } finally {
      setDispatchingDraftId(null);
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle || !taskDueDate) return;
    try {
      await api.createTask(lead.id, taskTitle, new Date(taskDueDate).toISOString(), taskNotes);
      setActionMessage('Follow-up task successfully scheduled!');
      setTaskTitle('');
      setTaskDueDate('');
      setTaskNotes('');
      onLeadUpdated();
      setTimeout(() => setActionMessage(null), 3000);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const renderBadge = (status: VerificationStatus) => {
    const colors: Record<VerificationStatus, string> = {
      'Verified': 'bg-emerald-50 text-emerald-700 border-emerald-200',
      'Source-listed': 'bg-blue-50 text-blue-700 border-blue-200',
      'Inferred': 'bg-purple-50 text-purple-700 border-purple-200',
      'Missing': 'bg-slate-100 text-slate-500 border-slate-200',
      'Conflicting': 'bg-amber-50 text-amber-700 border-amber-200'
    };
    return (
      <span className={`px-2 py-0.5 text-[10px] font-semibold border rounded-full ${colors[status] || colors.Missing}`}>
        {status}
      </span>
    );
  };

  const latestAudit = audits[0];
  const latestScore = scores[0];

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-900/40 backdrop-blur-sm">
      <div className="bg-white w-full max-w-2xl h-full shadow-2xl flex flex-col border-l border-slate-200 overflow-hidden animate-in slide-in-from-right duration-200">
        
        {/* Top Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-900 truncate max-w-md">{currentLead.company_name}</h2>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                currentLead.priority === 'High Priority' ? 'bg-amber-100 text-amber-800' :
                currentLead.priority === 'Medium Priority' ? 'bg-blue-100 text-blue-800' :
                'bg-slate-100 text-slate-700'
              }`}>
                Score: {currentLead.lead_score}/100
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              ID: {currentLead.id} • Sourced from {currentLead.data_source}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action Message Banner */}
        {actionMessage && (
          <div className="px-6 py-2 bg-emerald-50 border-b border-emerald-200 text-emerald-800 text-xs font-medium flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-600" />
            <span>{actionMessage}</span>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 px-6 bg-white space-x-6 text-sm font-medium">
          {[
            { id: 'overview', label: 'Overview & CRM' },
            { id: 'audit', label: `SEO Audit (${audits.length})` },
            { id: 'scoring', label: 'Scoring Breakdown' },
            { id: 'outreach', label: `🚀 Outreach Studio (${drafts.length})` },
            { id: 'tasks', label: 'Follow-Up' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-3 border-b-2 font-semibold transition-colors ${
                activeTab === tab.id
                  ? 'border-brand-700 text-brand-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* TAB 1: OVERVIEW & CRM */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Quick Outreach Launchpad */}
              <div className="p-4 bg-gradient-to-r from-blue-50/70 via-indigo-50/70 to-emerald-50/70 rounded-xl border border-blue-200 space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Send className="w-4 h-4 text-brand-700" />
                    <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                      Quick Outreach Actions
                    </span>
                  </div>
                  <span className="text-[10px] font-semibold text-brand-700 bg-white px-2 py-0.5 rounded-full border border-blue-200">
                    Email • WhatsApp • LinkedIn
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {/* Email */}
                  <button
                    onClick={() => {
                      setOutreachChannel('cold_email');
                      setActiveTab('outreach');
                    }}
                    className="p-2.5 bg-white hover:bg-blue-50 border border-blue-200 rounded-lg text-left transition-colors flex items-center justify-between group shadow-xs"
                  >
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-blue-100 text-blue-700 rounded group-hover:bg-blue-200">
                        <Mail className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-slate-800">Email Pitch</div>
                        <div className="text-[10px] text-slate-500">{currentLead.general_business_email ? 'Email listed' : 'No email'}</div>
                      </div>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600" />
                  </button>

                  {/* WhatsApp */}
                  <button
                    onClick={() => {
                      setOutreachChannel('whatsapp_draft');
                      setActiveTab('outreach');
                    }}
                    className="p-2.5 bg-white hover:bg-emerald-50 border border-emerald-200 rounded-lg text-left transition-colors flex items-center justify-between group shadow-xs"
                  >
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-emerald-100 text-emerald-700 rounded group-hover:bg-emerald-200">
                        <MessageSquare className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-slate-800">WhatsApp</div>
                        <div className="text-[10px] text-slate-500">{currentLead.public_business_phone ? 'Phone listed' : 'No phone'}</div>
                      </div>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-emerald-600" />
                  </button>

                  {/* LinkedIn */}
                  <button
                    onClick={() => {
                      setOutreachChannel('linkedin_note');
                      setActiveTab('outreach');
                    }}
                    className="p-2.5 bg-white hover:bg-blue-50 border border-blue-300 rounded-lg text-left transition-colors flex items-center justify-between group shadow-xs"
                  >
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-[#0a66c2]/10 text-[#0a66c2] rounded group-hover:bg-[#0a66c2]/20">
                        <Share2 className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-slate-800">LinkedIn Note</div>
                        <div className="text-[10px] text-slate-500">&lt;295 chars note</div>
                      </div>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-[#0a66c2]" />
                  </button>
                </div>
              </div>

              {/* CRM Stage Selector */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  CRM Pipeline Stage
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {CRM_STAGES.map((st) => (
                    <button
                      key={st}
                      onClick={() => handleStageChange(st)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border text-left transition-colors ${
                        currentLead.crm_status === st
                          ? 'bg-brand-700 text-white border-brand-800 shadow-sm'
                          : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              {/* Verified Contact Details Grid */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                  Verifiable Contact Details
                </h3>
                <div className="space-y-3">
                  {/* Website */}
                  <div className="p-3 bg-white border border-slate-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-slate-400" />
                      <div>
                        <div className="text-xs text-slate-500 font-medium">Official Website</div>
                        {currentLead.official_website ? (
                          <a
                            href={currentLead.official_website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-semibold text-brand-700 hover:underline"
                          >
                            {currentLead.official_website}
                          </a>
                        ) : (
                          <span className="text-xs text-slate-400 italic">No website found</span>
                        )}
                      </div>
                    </div>
                    <span className="text-xs text-slate-500 font-medium">
                      Status: {currentLead.website_status || 'Pending'}
                    </span>
                  </div>

                  {/* Email */}
                  <div className="p-3 bg-white border border-slate-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-slate-400" />
                      <div>
                        <div className="text-xs text-slate-500 font-medium">Business Email</div>
                        <span className="text-xs font-semibold text-slate-800">
                          {currentLead.general_business_email || 'Not listed'}
                        </span>
                      </div>
                    </div>
                    {renderBadge(currentLead.email_verification_status)}
                  </div>

                  {/* Phone */}
                  <div className="p-3 bg-white border border-slate-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-slate-400" />
                      <div>
                        <div className="text-xs text-slate-500 font-medium">Public Phone</div>
                        <span className="text-xs font-semibold text-slate-800">
                          {currentLead.public_business_phone || 'Not listed'}
                        </span>
                      </div>
                    </div>
                    {renderBadge(currentLead.phone_verification_status)}
                  </div>

                  {/* Decision Maker */}
                  <div className="p-3 bg-white border border-slate-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Building className="w-4 h-4 text-slate-400" />
                      <div>
                        <div className="text-xs text-slate-500 font-medium">Listed Decision Maker</div>
                        <span className="text-xs font-semibold text-slate-800">
                          {currentLead.publicly_listed_contact_name || 'Team / Unspecified'}
                          {currentLead.publicly_listed_designation && ` (${currentLead.publicly_listed_designation})`}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Location */}
                  <div className="p-3 bg-white border border-slate-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-slate-400" />
                      <div>
                        <div className="text-xs text-slate-500 font-medium">Location</div>
                        <span className="text-xs font-semibold text-slate-800">
                          {[currentLead.city, currentLead.state, currentLead.country].filter(Boolean).join(', ') || 'Not specified'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Marketing Opportunity & Recommended Service */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl space-y-2">
                <div className="text-xs font-bold text-brand-900 uppercase tracking-wide">
                  Identified Marketing Opportunity
                </div>
                <p className="text-xs text-brand-800">
                  {currentLead.marketing_opportunity || 'Run a website audit to discover opportunities.'}
                </p>
                <div className="pt-2 border-t border-blue-200/60 flex items-center justify-between">
                  <span className="text-xs font-medium text-brand-900">Recommended Service:</span>
                  <span className="text-xs font-bold text-brand-700 bg-white px-2.5 py-1 rounded-md border border-blue-300">
                    {currentLead.recommended_service || 'SEO & Growth Retainer'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: WEBSITE SEO AUDIT */}
          {activeTab === 'audit' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-800">Technical SEO & Conversion Audit</h3>
                  <p className="text-xs text-slate-500">SSRF-protected crawl of public website metadata and signals.</p>
                </div>
                <button
                  onClick={handleRunAudit}
                  disabled={loadingAudit || !currentLead.official_website}
                  className="px-3.5 py-1.5 bg-brand-700 hover:bg-brand-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingAudit ? 'animate-spin' : ''}`} />
                  <span>{loadingAudit ? 'Auditing...' : 'Run New Audit'}</span>
                </button>
              </div>

              {!currentLead.official_website && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-xs">
                  This company has no official website listed. This itself is an immediate, high-value opportunity to pitch custom Web Design & Development.
                </div>
              )}

              {latestAudit && (
                <div className="space-y-4">
                  {/* Key Health Checklist */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-center">
                      <div className="text-[11px] text-slate-500">HTTPS SSL</div>
                      <div className={`text-xs font-bold mt-0.5 ${latestAudit.is_https ? 'text-emerald-600' : 'text-red-600'}`}>
                        {latestAudit.is_https ? '✓ Secure' : '✗ Insecure'}
                      </div>
                    </div>
                    <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-center">
                      <div className="text-[11px] text-slate-500">Mobile Viewport</div>
                      <div className={`text-xs font-bold mt-0.5 ${latestAudit.has_viewport ? 'text-emerald-600' : 'text-red-600'}`}>
                        {latestAudit.has_viewport ? '✓ Configured' : '✗ Missing'}
                      </div>
                    </div>
                    <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-center">
                      <div className="text-[11px] text-slate-500">XML Sitemap</div>
                      <div className={`text-xs font-bold mt-0.5 ${latestAudit.has_sitemap_xml ? 'text-emerald-600' : 'text-amber-600'}`}>
                        {latestAudit.has_sitemap_xml ? '✓ Detected' : '✗ Missing'}
                      </div>
                    </div>
                    <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-center">
                      <div className="text-[11px] text-slate-500">Contact Link</div>
                      <div className={`text-xs font-bold mt-0.5 ${latestAudit.has_contact_page ? 'text-emerald-600' : 'text-red-600'}`}>
                        {latestAudit.has_contact_page ? '✓ Present' : '✗ Missing'}
                      </div>
                    </div>
                  </div>

                  {/* Assessment Summary */}
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700">
                    <span className="font-bold">Audit Assessment:</span> {latestAudit.overall_assessment}
                  </div>

                  {/* Findings List */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Findings & Recommendations ({latestAudit.findings?.length || 0})
                    </h4>
                    {latestAudit.findings?.map((f, idx) => (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-lg border text-xs space-y-1.5 ${
                          f.passed ? 'bg-emerald-50/40 border-emerald-200' : 'bg-white border-slate-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-800">{f.finding}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            f.passed ? 'bg-emerald-100 text-emerald-800' :
                            f.impact === 'High' || f.impact === 'Critical' ? 'bg-red-100 text-red-800' :
                            'bg-amber-100 text-amber-800'
                          }`}>
                            {f.passed ? 'Good' : `${f.impact} Impact`}
                          </span>
                        </div>
                        <div className="text-slate-600"><span className="font-semibold text-slate-700">Evidence:</span> {f.evidence}</div>
                        {!f.passed && (
                          <>
                            <div className="text-slate-700"><span className="font-semibold text-slate-800">Improvement:</span> {f.recommended_improvement}</div>
                            <div className="pt-1 text-brand-700 font-medium">Suggested Service: {f.suggested_service}</div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: LEAD SCORING BREAKDOWN */}
          {activeTab === 'scoring' && (
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-800">Explainable Lead Scoring (0–100)</h3>
                  <p className="text-xs text-slate-500">Objective score breakdown based on verifiable signals.</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowOverride(!showOverride)}
                    className="px-3 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium transition-colors"
                  >
                    Manual Override
                  </button>
                  <button
                    onClick={handleCalculateScore}
                    disabled={loadingScore}
                    className="px-3 py-1.5 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-xs font-semibold transition-colors"
                  >
                    {loadingScore ? 'Scoring...' : 'Recalculate'}
                  </button>
                </div>
              </div>

              {/* Manual Override Form */}
              {showOverride && (
                <form onSubmit={handleManualOverride} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                  <div className="text-xs font-bold text-slate-800">Set Manual Lead Score (with audit log)</div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-600 mb-1">New Score (0–100)</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        required
                        value={overrideScore}
                        onChange={(e) => setOverrideScore(Number(e.target.value))}
                        className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-600 mb-1">Reason for Adjustment</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Spoke to CEO directly, requested quote"
                        value={overrideReason}
                        onChange={(e) => setOverrideReason(e.target.value)}
                        className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowOverride(false)}
                      className="px-3 py-1 text-xs text-slate-600 hover:bg-slate-200 rounded"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-3 py-1 bg-brand-700 text-white text-xs font-medium rounded hover:bg-brand-800"
                    >
                      Save Override
                    </button>
                  </div>
                </form>
              )}

              {/* Score Display Card */}
              <div className="p-6 bg-gradient-to-r from-brand-800 to-brand-600 text-white rounded-xl shadow-sm flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-wider text-blue-200 font-semibold">Priority Tier</div>
                  <div className="text-2xl font-bold mt-0.5">{currentLead.priority}</div>
                  <div className="text-xs text-blue-100 mt-1">
                    Based on industry suitability, website gaps, and contact quality.
                  </div>
                </div>
                <div className="h-20 w-20 rounded-full border-4 border-blue-200 flex flex-col items-center justify-center font-bold text-2xl bg-white/10 shadow-inner">
                  {currentLead.lead_score}
                  <span className="text-[10px] font-normal text-blue-100">/ 100</span>
                </div>
              </div>

              {/* Breakdown by Category */}
              {latestScore && latestScore.breakdown && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Score Weight Breakdown</h4>
                  <div className="space-y-2">
                    {latestScore.breakdown.map((item, idx) => (
                      <div key={idx} className="p-3 bg-white border border-slate-200 rounded-lg">
                        <div className="flex justify-between items-center text-xs mb-1">
                          <span className="font-bold text-slate-800">{item.category}</span>
                          <span className="font-semibold text-brand-700">
                            {item.earned_score} / {item.max_score} pts
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden mb-1.5">
                          <div
                            className="bg-brand-600 h-full rounded-full"
                            style={{ width: `${Math.min(100, (item.earned_score / item.max_score) * 100)}%` }}
                          />
                        </div>
                        <p className="text-[11px] text-slate-500">{item.explanation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: OUTREACH GENERATION */}
          {activeTab === 'outreach' && (
            <div className="space-y-5">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Generate Outreach Pitch
                  </h3>
                  <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-lg p-0.5 text-xs font-medium">
                    <button
                      onClick={() => setOutreachLang('en')}
                      className={`px-2.5 py-1 rounded ${outreachLang === 'en' ? 'bg-brand-700 text-white font-bold' : 'text-slate-600'}`}
                    >
                      English
                    </button>
                    <button
                      onClick={() => setOutreachLang('hi')}
                      className={`px-2.5 py-1 rounded ${outreachLang === 'hi' ? 'bg-brand-700 text-white font-bold' : 'text-slate-600'}`}
                    >
                      हिंदी (Hindi)
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5">
                  {[
                    { id: 'cold_email', label: 'Cold Email' },
                    { id: 'follow_up_email', label: 'Follow-Up' },
                    { id: 'linkedin_note', label: 'LinkedIn Note' },
                    { id: 'linkedin_draft', label: 'LinkedIn InMail' },
                    { id: 'whatsapp_draft', label: 'WhatsApp Draft' },
                  ].map((ch) => (
                    <button
                      key={ch.id}
                      onClick={() => setOutreachChannel(ch.id)}
                      className={`py-1.5 px-2 rounded text-xs font-medium text-center border transition-colors ${
                        outreachChannel === ch.id
                          ? 'bg-brand-700 text-white border-brand-800'
                          : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {ch.label}
                    </button>
                  ))}
                </div>

                <button
                  onClick={handleGenerateDraft}
                  disabled={loadingDraft}
                  className="w-full py-2 bg-brand-700 hover:bg-brand-800 disabled:opacity-50 text-white text-xs font-bold rounded-lg shadow-sm transition-colors flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-200" />
                  <span>{loadingDraft ? 'Generating Draft...' : 'Generate Personalized Pitch'}</span>
                </button>
              </div>

              {/* Generated Drafts List */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Generated Drafts ({drafts.length})
                </h4>
                {drafts.length === 0 ? (
                  <div className="p-6 bg-slate-50 border border-slate-200 rounded-xl text-center space-y-3">
                    <Sparkles className="w-6 h-6 text-brand-600 mx-auto" />
                    <p className="text-xs font-semibold text-slate-700">
                      No outreach pitches generated for this lead yet.
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Click any channel below to generate an instant personalized pitch with verifiable evidence:
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 max-w-lg mx-auto">
                      <button
                        onClick={async () => {
                          setOutreachChannel('cold_email');
                          setLoadingDraft(true);
                          try {
                            const draft = await api.generateOutreach(lead.id, 'cold_email', outreachLang);
                            setDrafts([draft, ...drafts]);
                          } catch (err: any) { alert(err.message); }
                          finally { setLoadingDraft(false); }
                        }}
                        className="p-2 bg-white hover:bg-blue-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 flex items-center justify-center gap-1.5 shadow-2xs"
                      >
                        <Mail className="w-3.5 h-3.5 text-blue-600" />
                        <span>Cold Email</span>
                      </button>

                      <button
                        onClick={async () => {
                          setOutreachChannel('whatsapp_draft');
                          setLoadingDraft(true);
                          try {
                            const draft = await api.generateOutreach(lead.id, 'whatsapp_draft', outreachLang);
                            setDrafts([draft, ...drafts]);
                          } catch (err: any) { alert(err.message); }
                          finally { setLoadingDraft(false); }
                        }}
                        className="p-2 bg-white hover:bg-emerald-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 flex items-center justify-center gap-1.5 shadow-2xs"
                      >
                        <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />
                        <span>WhatsApp</span>
                      </button>

                      <button
                        onClick={async () => {
                          setOutreachChannel('linkedin_note');
                          setLoadingDraft(true);
                          try {
                            const draft = await api.generateOutreach(lead.id, 'linkedin_note', outreachLang);
                            setDrafts([draft, ...drafts]);
                          } catch (err: any) { alert(err.message); }
                          finally { setLoadingDraft(false); }
                        }}
                        className="p-2 bg-white hover:bg-blue-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 flex items-center justify-center gap-1.5 shadow-2xs"
                      >
                        <Share2 className="w-3.5 h-3.5 text-[#0a66c2]" />
                        <span>LinkedIn Note</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  drafts.map((d) => (
                    <div key={d.id} className="p-4 bg-white border border-slate-200 rounded-xl space-y-2.5 shadow-sm">
                      <div className="flex items-center justify-between text-xs border-b border-slate-100 pb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 uppercase tracking-wide">
                            {d.channel.replace('_', ' ')}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded uppercase font-semibold">
                            {d.language}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleCopyDraft(d)}
                            className="px-2.5 py-1 text-slate-600 hover:text-brand-700 hover:bg-blue-50 border border-slate-200 rounded text-xs font-medium flex items-center gap-1"
                          >
                            {copiedDraftId === d.id ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                            <span>{copiedDraftId === d.id ? 'Copied!' : 'Copy'}</span>
                          </button>
                          <button
                            onClick={() => handleApproveDraft(d.id, d.is_approved)}
                            className={`px-2.5 py-1 rounded text-xs font-semibold border flex items-center gap-1 ${
                              d.is_approved
                                ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                                : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                            }`}
                          >
                            <ShieldCheck className="w-3.5 h-3.5" />
                            <span>{d.is_approved ? 'Approved' : 'Mark Approved'}</span>
                          </button>
                        </div>
                      </div>

                      {d.subject_line && (
                        <div className="text-xs">
                          <span className="font-bold text-slate-700">Subject: </span>
                          <span className="text-slate-900">{d.subject_line}</span>
                        </div>
                      )}

                      <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-800 font-mono whitespace-pre-wrap leading-relaxed">
                        {d.message_body}
                      </div>

                      <div className="text-[11px] text-slate-500 flex flex-wrap gap-2 pt-1 border-t border-slate-100">
                        <span className="text-brand-700 font-medium">Service: {d.recommended_service}</span>
                        <span>•</span>
                        <span>Next: {d.suggested_next_action}</span>
                      </div>

                      {/* Outreach Dispatch Actions for Email, WhatsApp, and LinkedIn */}
                      <div className="pt-2.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5">
                          {d.is_sent ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                              <span>Contacted / Dispatched</span>
                            </span>
                          ) : (
                            <span className="text-[11px] text-slate-400">Ready to dispatch</span>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          {(d.channel === 'cold_email' || d.channel === 'follow_up_email') && (
                            <>
                              <button
                                onClick={() => handleSendEmail(d)}
                                disabled={dispatchingDraftId === d.id}
                                className="px-3 py-1.5 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors"
                              >
                                <Send className="w-3.5 h-3.5" />
                                <span>{dispatchingDraftId === d.id ? 'Sending...' : 'Send (Resend / SMTP)'}</span>
                              </button>
                              <button
                                onClick={() => handleOpenMailApp(d)}
                                className="px-2.5 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
                                title="Open in Gmail / Outlook on your device (100% Free, zero setup)"
                              >
                                <ExternalLink className="w-3 h-3" />
                                <span>Mail App</span>
                              </button>
                            </>
                          )}

                          {d.channel === 'whatsapp_draft' && (
                            <button
                              onClick={() => handleSendWhatsApp(d)}
                              disabled={dispatchingDraftId === d.id}
                              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors"
                            >
                              <MessageSquare className="w-3.5 h-3.5" />
                              <span>{dispatchingDraftId === d.id ? 'Dispatching...' : 'Send WhatsApp (Direct / API)'}</span>
                            </button>
                          )}

                          {(d.channel === 'linkedin_note' || d.channel === 'linkedin_draft') && (
                            <button
                              onClick={() => handleSendLinkedIn(d)}
                              disabled={dispatchingDraftId === d.id}
                              className="px-3 py-1.5 bg-[#0a66c2] hover:bg-[#004182] text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors"
                            >
                              <Share2 className="w-3.5 h-3.5" />
                              <span>{dispatchingDraftId === d.id ? 'Opening...' : 'Copy Pitch & Open LinkedIn'}</span>
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 5: FOLLOW-UP TASKS */}
          {activeTab === 'tasks' && (
            <div className="space-y-5">
              <form onSubmit={handleCreateTask} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Schedule CRM Follow-Up</h3>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Task Title</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Call for SEO pitch review"
                    value={taskTitle}
                    onChange={(e) => setTaskTitle(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Due Date & Time</label>
                  <input
                    type="datetime-local"
                    required
                    value={taskDueDate}
                    onChange={(e) => setTaskDueDate(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">Notes</label>
                  <textarea
                    rows={2}
                    placeholder="Context for the call or email..."
                    value={taskNotes}
                    onChange={(e) => setTaskNotes(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-700 hover:bg-brand-800 text-white text-xs font-bold rounded-lg shadow-sm transition-colors"
                >
                  Schedule Follow-Up Task
                </button>
              </form>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};
