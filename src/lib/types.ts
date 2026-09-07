export type Role = "client" | "freelancer" | "admin";

export interface User {
  id: string;
  email: string;
  role: Role;
  first_name: string;
  last_name: string;
  company: string;
  bio: string;
  location: string;
  country: string;
  languages: string[];
  skills: string[];
  hourly_rate: number | null;
  availability: string;
  rating: number;
  rating_count: number;
  total_jobs: number;
  completed_jobs: number;
  plan: string;
  referral_code: string | null;
  email_verified: boolean;
  auto_accept_enabled: boolean;
  auto_accept_min_budget: number | null;
  auto_accept_min_score: number | null;
  payout_method: string;
  payout_address: string | null;
  created_at: string;
}

export interface Freelancer {
  id: string;
  first_name: string;
  last_name: string;
  company: string;
  bio: string;
  location: string;
  country: string;
  languages: string[];
  skills: string[];
  hourly_rate: number | null;
  availability: string;
  rating: number;
  rating_count: number;
  completed_jobs: number;
}

export interface JobAnalysis {
  category: string;
  subcategory: string;
  skills: string[];
  urgency: string;
  experience_level: string;
  fair_price: number;
  key_requirements: string;
  model: string;
}

export interface Job {
  id: string;
  title: string;
  description: string;
  category: string;
  subcategory: string;
  budget: number;
  deadline: string;
  location: string;
  required_skills: string[];
  status: string;
  client_id: string;
  ai_analysis: JobAnalysis | null;
  interview_questions: string[] | null;
  deliverables: string | null;
  deliverable_url: string | null;
  deliverable_report: {
    score: number;
    summary: string;
    checklist: { requirement: string; met: boolean; comment: string }[];
    issues: string[];
    recommendation: string;
    model?: string;
  } | null;
  created_at: string;
  client?: User | null;
}

export interface JobListItem extends Job {
  match_count: number;
}

export interface Match {
  id: string;
  job_id: string;
  freelancer_id: string;
  score: number;
  matched_by: string;
  status: string;
  message: string;
  interview_answers: string[] | null;
  interview_score: number | null;
  interview_feedback: string | null;
  interviewed_at: string | null;
  agreed_price: number | null;
  price_proposal: number | null;
  price_status: string;
  created_at: string;
  freelancer?: Freelancer | null;
  job?: Job | null;
}

export interface Milestone {
  id: string;
  contract_id: string;
  title: string;
  amount: number;
  order_index: number;
  status: string;
  submitted_at: string | null;
  released_at: string | null;
  created_at: string;
}

export interface Contract {
  id: string;
  job_id: string;
  match_id: string;
  client_id: string;
  freelancer_id: string;
  amount: number;
  platform_fee: number;
  fee_rate: number;
  status: string;
  completed_at: string | null;
  created_at: string;
  job?: JobListItem | null;
  freelancer?: Freelancer | null;
  milestones?: Milestone[] | null;
  released_amount: number;
  refund_eligible: boolean;
  refund_reason: string;
  dispute_reason: string | null;
  dispute_raised_by: string | null;
  dispute_ai_assessment: string | null;
  disputed_at: string | null;
  dispute_resolution: string | null;
  resolved_at: string | null;
}

export interface AdminDispute {
  id: string;
  job_title: string;
  amount: number;
  client_email: string;
  freelancer_email: string;
  dispute_reason: string;
  dispute_raised_by: string;
  dispute_ai_assessment: string;
  disputed_at: string | null;
}

export interface Rating {
  id: string;
  from_user_id: string;
  to_user_id: string;
  job_id: string | null;
  score: number;
  comment: string;
  created_at: string;
  from_user?: User | null;
}

export interface Analytics {
  role: Role;
  total_jobs: number;
  active_jobs: number;
  completed_jobs: number;
  total_spent: number;
  total_earned: number;
  match_count: number;
  pending_matches: number;
  accepted_matches: number;
  rating: number;
  jobs_this_month: number;
  avg_match_time_seconds: number | null;
  instant_matches: number;
  avg_time_to_hire_hours: number | null;
  recent_jobs: string[];
  recent_matches: string[];
}

export interface AdminStats {
  users: number;
  freelancers: number;
  clients: number;
  jobs: number;
  open_jobs: number;
  completed_jobs: number;
  matches: number;
  contracts: number;
  revenue: number;
  recent_users: { id: string; email: string; role: string; plan: string; created_at: string }[];
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  body: string;
  read: boolean;
  created_at: string;
}

// #F1 AI Listing Factory
export interface ListingContent {
  title: string;
  description: string;
  bullet_points: string[];
  seo_tags: string[];
  meta_description: string;
  model?: string;
}

export interface ListingHistoryItem {
  id: string;
  product_name: string;
  marketplace: string;
  language: string;
  content: ListingContent;
  created_at: string;
}

// #F6 Video script generator
export interface VideoScript {
  hook: string;
  script: string;
  cta: string;
  duration_seconds: number;
  model?: string;
}

// #F2 Global currency & tax
export interface FxRates {
  base: string;
  rates: Record<string, number>;
  symbols: Record<string, string>;
}

export interface TaxHint {
  vat_rate: number;
  note: string;
}

// #F4 Smart Supplier Risk Score
export interface RiskScore {
  score: number;
  level: "low" | "medium" | "high";
  label: string;
  factors: {
    rating: number;
    track_record: number;
    completion_rate: number;
    review_volume: number;
  };
}

// #F5 AI Co-Pilot
export interface CopilotMessage {
  question: string;
  answer: string;
  created_at: string;
}

// #F7 Global Talent Time-Zone Auto-Scheduler
export interface ScheduleSuggestion {
  client_utc_offset: number;
  freelancer_utc_offset: number;
  hours_apart: number;
  overlap_hours: number;
  suggested_utc_window: [number, number] | null;
  mode: "live-overlap" | "handoff" | "async-24-7";
  tip: string;
}

// #F8 White-label / Reseller API
export interface ApiKeyItem {
  id: string;
  name: string;
  brand_name: string;
  prefix: string;
  active: boolean;
  request_count: number;
  last_used_at: string | null;
  created_at: string;
}

export interface NewApiKey {
  id: string;
  name: string;
  key: string;
  prefix: string;
  warning: string;
}

// Payments
export interface PaymentsConfig {
  stripe_enabled: boolean;
  publishable_key: string | null;
}

export interface CheckoutResult {
  mode: "stripe" | "demo";
  checkout_url?: string;
  payment_id?: string;
  message?: string;
}

// Sprint 4 (#12) Product Source Finder
export interface SourceFinderJob {
  category: string;
  title: string;
  description: string;
  suggested_budget: number;
}

export interface SourceFinderPlan {
  product_summary: string;
  suggested_jobs: SourceFinderJob[];
  total_budget_estimate: number;
  model?: string;
}

// Sprint 4 (#9-#11) e-commerce store integrations
export interface StoreConnection {
  id: string;
  platform: "shopify" | "baselinker";
  label: string;
  active: boolean;
  last_synced_at: string | null;
  created_at: string;
}

// Portal Radar — global scan of external job portals
export interface ExternalListing {
  id: string;
  source: string;
  external_id: string;
  url: string;
  title: string;
  description: string;
  company: string;
  budget_min: number | null;
  budget_max: number | null;
  budget_text: string;
  currency: string;
  category: string;
  tags: string[];
  location: string;
  is_remote: boolean;
  language: string;
  contact: string;
  posted_at: string | null;
  fetched_at: string | null;
  status: "new" | "reviewed" | "imported" | "dismissed";
  imported_job_id: string | null;
}

export interface ExternalTalent {
  id: string;
  source: string;
  external_id: string;
  url: string;
  name: string;
  headline: string;
  skills: string[];
  location: string;
  country: string;
  rate_text: string;
  rating: number | null;
  followers: number | null;
  portfolio_url: string;
  avatar_url: string;
  fetched_at: string | null;
  status: "new" | "contacted" | "invited" | "dismissed";
}

export interface RadarSource {
  slug: string;
  name: string;
  kind: "listings" | "talent" | "both";
  region: string;
  homepage: string;
  access: string;
  requires_key: boolean;
  enabled: boolean;
  last_scan_at: string | null;
  last_scan_ok: boolean | null;
  last_scan_error: string | null;
  listings_count: number;
  talents_count: number;
}

export interface RadarStats {
  listings: { total: number; by_status: Record<string, number> };
  talent: { total: number; by_status: Record<string, number> };
  sources_enabled: number;
  sources_total: number;
  last_scan_at: string | null;
}
