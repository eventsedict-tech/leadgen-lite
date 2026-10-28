import {
  AuthToken, User, Lead, LeadListResponse, WebsiteAudit,
  LeadScoreResponse, OutreachDraft, FollowUpTask, SuppressionItem,
  ProviderInfo, DiscoveredCompany, DashboardData,
  OutreachActionResponse, OutreachChannelStatus,
  BulkOutreachResponse, Campaign, CampaignDetail
} from '../types';

const API_BASE = '/api';

export class ApiError extends Error {
  status: number;
  data: any;
  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('leadgen_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...(options.headers || {})
  };

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (res.status === 204) {
    return {} as T;
  }

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const errDetail = data?.detail || `HTTP Error ${res.status}`;
    throw new ApiError(res.status, errDetail, data);
  }

  return data as T;
}

export const api = {
  // Auth
  async register(payload: any): Promise<AuthToken> {
    return request<AuthToken>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async login(payload: any): Promise<AuthToken> {
    return request<AuthToken>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async getMe(): Promise<User> {
    return request<User>('/auth/me');
  },

  // Leads
  async listLeads(params: Record<string, any> = {}): Promise<LeadListResponse> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        searchParams.append(k, String(v));
      }
    });
    return request<LeadListResponse>(`/leads?${searchParams.toString()}`);
  },

  async getLead(id: number): Promise<Lead> {
    return request<Lead>(`/leads/${id}`);
  },

  async createLead(payload: any): Promise<Lead> {
    return request<Lead>('/leads', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async updateLead(id: number, payload: any): Promise<Lead> {
    return request<Lead>(`/leads/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  async deleteLead(id: number): Promise<void> {
    return request<void>(`/leads/${id}`, { method: 'DELETE' });
  },

  // Audits & Enrichment
  async runAudit(leadId?: number, url?: string): Promise<WebsiteAudit> {
    return request<WebsiteAudit>('/audits/run', {
      method: 'POST',
      body: JSON.stringify({ lead_id: leadId, url })
    });
  },

  async getLeadAudits(leadId: number): Promise<WebsiteAudit[]> {
    return request<WebsiteAudit[]>(`/audits/lead/${leadId}`);
  },

  async queueEnrichment(leadId: number): Promise<any> {
    return request<any>(`/enrichment/queue/${leadId}`, { method: 'POST' });
  },

  // Scoring
  async calculateScore(leadId: number, weights?: any): Promise<LeadScoreResponse> {
    return request<LeadScoreResponse>(`/scoring/calculate/${leadId}`, {
      method: 'POST',
      body: weights ? JSON.stringify(weights) : undefined
    });
  },

  async overrideScore(leadId: number, newScore: number, reason: string): Promise<LeadScoreResponse> {
    return request<LeadScoreResponse>(`/scoring/override/${leadId}`, {
      method: 'POST',
      body: JSON.stringify({ new_score: newScore, override_reason: reason })
    });
  },

  async getScoreHistory(leadId: number): Promise<LeadScoreResponse[]> {
    return request<LeadScoreResponse[]>(`/scoring/history/${leadId}`);
  },

  // Outreach
  async generateOutreach(leadId: number, channel: string, language: string, useLlm = false): Promise<OutreachDraft> {
    return request<OutreachDraft>('/outreach/generate', {
      method: 'POST',
      body: JSON.stringify({ lead_id: leadId, channel, language, use_llm: useLlm })
    });
  },

  async getLeadDrafts(leadId: number): Promise<OutreachDraft[]> {
    return request<OutreachDraft[]>(`/outreach/lead/${leadId}`);
  },

  async updateDraft(draftId: number, payload: any): Promise<OutreachDraft> {
    return request<OutreachDraft>(`/outreach/drafts/${draftId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  async deleteDraft(draftId: number): Promise<void> {
    return request<void>(`/outreach/drafts/${draftId}`, { method: 'DELETE' });
  },

  async getOutreachChannelStatus(): Promise<OutreachChannelStatus> {
    return request<OutreachChannelStatus>('/outreach/channels/status');
  },

  async sendEmailOutreach(leadId: number, subject: string, messageBody: string, recipientEmail?: string, draftId?: number): Promise<OutreachActionResponse> {
    return request<OutreachActionResponse>('/outreach/send/email', {
      method: 'POST',
      body: JSON.stringify({
        lead_id: leadId,
        draft_id: draftId,
        recipient_email: recipientEmail,
        subject,
        message_body: messageBody
      })
    });
  },

  async sendWhatsAppOutreach(leadId: number, messageBody: string, recipientPhone?: string, draftId?: number): Promise<OutreachActionResponse> {
    return request<OutreachActionResponse>('/outreach/send/whatsapp', {
      method: 'POST',
      body: JSON.stringify({
        lead_id: leadId,
        draft_id: draftId,
        recipient_phone: recipientPhone,
        message_body: messageBody
      })
    });
  },

  async sendLinkedInOutreach(leadId: number, messageBody: string, actionType: string = 'connection_note', draftId?: number): Promise<OutreachActionResponse> {
    return request<OutreachActionResponse>('/outreach/send/linkedin', {
      method: 'POST',
      body: JSON.stringify({
        lead_id: leadId,
        draft_id: draftId,
        action_type: actionType,
        message_body: messageBody
      })
    });
  },

  // Bulk Outreach & Campaigns
  async bulkGenerateDrafts(payload: { lead_ids: number[]; channel?: string; language?: string; use_llm?: boolean; custom_instructions?: string }): Promise<OutreachDraft[]> {
    return request<OutreachDraft[]>('/outreach/bulk/generate', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async bulkSendEmail(payload: { lead_ids: number[]; language?: string; subject_override?: string; message_body_override?: string }): Promise<BulkOutreachResponse> {
    return request<BulkOutreachResponse>('/outreach/bulk/send/email', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async listCampaigns(): Promise<Campaign[]> {
    return request<Campaign[]>('/outreach/campaigns');
  },

  async getCampaign(campaignId: number): Promise<CampaignDetail> {
    return request<CampaignDetail>(`/outreach/campaigns/${campaignId}`);
  },

  async createCampaign(payload: { name: string; channel: string; lead_ids: number[]; language?: string; sending_limit_per_day?: number }): Promise<any> {
    return request<any>('/outreach/campaigns', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async startCampaign(campaignId: number): Promise<any> {
    return request<any>(`/outreach/campaigns/${campaignId}/start`, {
      method: 'POST'
    });
  },

  async testSmtp(payload: any): Promise<any> {
    return request<any>('/settings/test-email', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // Discovery
  async getProviders(): Promise<ProviderInfo[]> {
    return request<ProviderInfo[]>('/discovery/providers');
  },

  async searchDiscovery(providerId: string, query: any): Promise<DiscoveredCompany[]> {
    return request<DiscoveredCompany[]>('/discovery/search', {
      method: 'POST',
      body: JSON.stringify({ provider_id: providerId, query })
    });
  },

  async importDiscovered(companies: DiscoveredCompany[]): Promise<any> {
    return request<any>('/discovery/import-selected', {
      method: 'POST',
      body: JSON.stringify({ companies })
    });
  },

  // Imports
  async uploadImportFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('leadgen_token');
    const res = await fetch(`${API_BASE}/imports/preview`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new ApiError(res.status, err?.detail || 'Upload failed');
    }
    return res.json();
  },

  async validateImport(tempFileId: string, mapping: Record<string, string>, skipDups: boolean, merge: boolean): Promise<any> {
    return request<any>('/imports/validate', {
      method: 'POST',
      body: JSON.stringify({
        temp_file_id: tempFileId,
        column_mapping: mapping,
        skip_duplicates: skipDups,
        merge_existing: merge
      })
    });
  },

  async commitImport(tempFileId: string, mapping: Record<string, string>, skipDups: boolean, merge: boolean): Promise<any> {
    return request<any>('/imports/commit', {
      method: 'POST',
      body: JSON.stringify({
        temp_file_id: tempFileId,
        column_mapping: mapping,
        skip_duplicates: skipDups,
        merge_existing: merge
      })
    });
  },

  // Tasks
  async listTasks(status?: string, leadId?: number): Promise<FollowUpTask[]> {
    const params = new URLSearchParams();
    if (status) params.append('status_filter', status);
    if (leadId) params.append('lead_id', String(leadId));
    return request<FollowUpTask[]>(`/tasks?${params.toString()}`);
  },

  async createTask(leadId: number, title: string, dueDate: string, notes?: string): Promise<FollowUpTask> {
    return request<FollowUpTask>('/tasks', {
      method: 'POST',
      body: JSON.stringify({ lead_id: leadId, title, due_date: dueDate, notes })
    });
  },

  async updateTask(id: number, payload: any): Promise<FollowUpTask> {
    return request<FollowUpTask>(`/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  async deleteTask(id: number): Promise<void> {
    return request<void>(`/tasks/${id}`, { method: 'DELETE' });
  },

  // Suppression
  async listSuppression(): Promise<SuppressionItem[]> {
    return request<SuppressionItem[]>('/suppression');
  },

  async addSuppression(payload: any): Promise<SuppressionItem> {
    return request<SuppressionItem>('/suppression', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async deleteSuppression(id: number): Promise<void> {
    return request<void>(`/suppression/${id}`, { method: 'DELETE' });
  },

  // Dashboard
  async getDashboard(): Promise<DashboardData> {
    return request<DashboardData>('/dashboard/metrics');
  },

  // Settings
  async getIntegrations(): Promise<any[]> {
    return request<any[]>('/settings/integrations');
  },

  async saveIntegration(providerType: string, isActive: boolean, config: any): Promise<any> {
    return request<any>('/settings/integrations', {
      method: 'POST',
      body: JSON.stringify({ provider_type: providerType, is_active: isActive, config })
    });
  },

  // Exports download url builder
  getExportUrl(format: 'xlsx' | 'csv', params: Record<string, string> = {}): string {
    const sp = new URLSearchParams({ format, ...params });
    const token = localStorage.getItem('leadgen_token');
    return `${API_BASE}/exports/leads?${sp.toString()}&token=${token || ''}`;
  }
};
