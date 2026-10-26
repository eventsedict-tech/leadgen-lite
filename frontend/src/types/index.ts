export type CRMStage =
  | 'New'
  | 'Research Pending'
  | 'Qualified'
  | 'Ready for Review'
  | 'Contacted'
  | 'Follow-Up'
  | 'Interested'
  | 'Meeting Scheduled'
  | 'Proposal Sent'
  | 'Converted'
  | 'Not Interested'
  | 'Do Not Contact';

export type LeadPriority = 'High Priority' | 'Medium Priority' | 'Low Priority' | 'Review Required';

export type VerificationStatus = 'Verified' | 'Source-listed' | 'Inferred' | 'Missing' | 'Conflicting';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  organization_id: number;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Lead {
  id: number;
  organization_id: number;
  company_name: string;
  normalized_company_name: string;
  official_website?: string | null;
  normalized_domain?: string | null;
  industry?: string | null;
  business_category?: string | null;
  country?: string | null;
  state?: string | null;
  city?: string | null;
  public_business_address?: string | null;
  public_business_phone?: string | null;
  general_business_email?: string | null;
  contact_page?: string | null;
  publicly_listed_contact_name?: string | null;
  publicly_listed_designation?: string | null;
  company_linkedin_url?: string | null;
  source_url?: string | null;
  data_source: string;
  research_date?: string | null;
  last_verified_date?: string | null;
  website_status?: string | null;
  email_verification_status: VerificationStatus;
  phone_verification_status: VerificationStatus;
  lead_score: number;
  priority: LeadPriority;
  marketing_opportunity?: string | null;
  recommended_service?: string | null;
  crm_status: CRMStage;
  follow_up_date?: string | null;
  notes?: string | null;
  tags?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Lead[];
}

export interface SEOFinding {
  category: string;
  finding: string;
  evidence: string;
  impact: string;
  recommended_improvement: string;
  suggested_service: string;
  passed: boolean;
}

export interface WebsiteAudit {
  id: number;
  lead_id: number;
  audited_url: string;
  http_status?: number | null;
  is_https: boolean;
  page_title?: string | null;
  meta_description?: string | null;
  h1_heading?: string | null;
  images_missing_alt_count: number;
  total_images_count: number;
  has_viewport: boolean;
  has_robots_txt: boolean;
  has_sitemap_xml: boolean;
  has_contact_page: boolean;
  internal_links_count: number;
  local_seo_indicators?: string | null;
  findings: SEOFinding[];
  overall_assessment?: string | null;
  created_at: string;
}

export interface ScoreItem {
  category: string;
  earned_score: number;
  max_score: number;
  explanation: string;
}

export interface LeadScoreResponse {
  id: number;
  lead_id: number;
  total_score: number;
  priority_tier: string;
  industry_fit_score: number;
  website_opportunity_score: number;
  info_quality_score: number;
  marketing_opportunity_score: number;
  business_relevance_score: number;
  breakdown: ScoreItem[];
  manual_override: boolean;
  override_reason?: string | null;
  scored_by: string;
  created_at: string;
}

export interface OutreachDraft {
  id: number;
  lead_id: number;
  channel: string;
  language: string;
  subject_line?: string | null;
  message_body: string;
  recommended_service?: string | null;
  personalization_evidence?: string | null;
  suggested_next_action?: string | null;
  is_approved: boolean;
  is_sent: boolean;
  created_at: string;
}

export interface FollowUpTask {
  id: number;
  lead_id: number;
  company_name?: string | null;
  title: string;
  due_date: string;
  status: string;
  notes?: string | null;
  created_at: string;
}

export interface SuppressionItem {
  id: number;
  email?: string | null;
  phone?: string | null;
  domain?: string | null;
  reason: string;
  added_by?: string | null;
  created_at: string;
}

export interface ProviderInfo {
  id: string;
  name: string;
  is_configured: boolean;
  description: string;
  setup_instructions: string;
  docs_url: string;
}

export interface DiscoveredCompany {
  company_name: string;
  official_website?: string | null;
  industry?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  public_business_phone?: string | null;
  public_business_address?: string | null;
  source_url?: string | null;
  data_source: string;
  rating?: number | null;
  user_ratings_total?: number | null;
  raw_details?: any;
}

export interface DashboardMetrics {
  total_leads: number;
  leads_imported: number;
  leads_discovered: number;
  high_priority_leads: number;
  websites_analyzed: number;
  qualified_leads: number;
  follow_ups_due: number;
  converted_leads: number;
}

export interface DistributionItem {
  label: string;
  count: number;
}

export interface DashboardData {
  metrics: DashboardMetrics;
  distributions: {
    by_industry: DistributionItem[];
    by_city: DistributionItem[];
    by_source: DistributionItem[];
    by_priority: DistributionItem[];
  };
  recent_imports: Array<{
    id: number;
    filename: string;
    imported: number;
    skipped: number;
    merged: number;
    created_at: string;
  }>;
  recent_research_jobs: Array<{
    id: number;
    company_name: string;
    status: string;
    log?: string;
    created_at: string;
  }>;
  upcoming_follow_ups: Array<{
    id: number;
    lead_id: number;
    company_name: string;
    title: string;
    due_date: string;
    is_overdue: boolean;
  }>;
}
