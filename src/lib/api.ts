const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getErrorMessage(err: unknown, fallback = "Request failed"): string {
  if (err instanceof Error) return err.message;
  if (typeof err === "string") return err;
  return fallback;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("dropify_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("dropify_token", token);
  else localStorage.removeItem("dropify_token");
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit & { auth?: boolean } = {}
): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const h: Record<string, string> = {
    "Content-Type": "application/json",
    ...(headers as Record<string, string>),
  };
  if (auth) {
    const token = getToken();
    if (token) h.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...rest, headers: h });
  const body = await res.json().catch(() => null);

  if (!res.ok) {
    const message =
      (body && (body.detail || body.message)) ||
      `Request failed (${res.status})`;
    throw new ApiError(res.status, typeof message === "string" ? message : JSON.stringify(message));
  }
  return body as T;
}

export const API = {
  // Auth
  register: (data: Record<string, unknown>) =>
    api("/auth/register", { method: "POST", body: JSON.stringify(data), auth: false }),
  login: (data: Record<string, unknown>) =>
    api("/auth/login", { method: "POST", body: JSON.stringify(data), auth: false }),
  me: () => api("/auth/me"),

  // Users
  updateProfile: (data: Record<string, unknown>) =>
    api("/users/me", { method: "PUT", body: JSON.stringify(data) }),
  getFreelancers: (params = "") => api(`/users${params}`),
  getUser: (id: string) => api(`/users/${id}`),

  // Jobs
  createJob: (data: Record<string, unknown>) =>
    api("/jobs", { method: "POST", body: JSON.stringify(data) }),
  listJobs: (params = "") => api(`/jobs${params}`),
  myJobs: () => api("/jobs/mine"),
  recommendedJobs: () => api("/jobs/recommended"),
  getJob: (id: string) => api(`/jobs/${id}`),
  updateJob: (id: string, data: Record<string, unknown>) =>
    api(`/jobs/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteJob: (id: string) => api(`/jobs/${id}`, { method: "DELETE" }),
  completeJob: (id: string) => api(`/jobs/${id}/complete`, { method: "POST" }),

  // Matches
  jobMatches: (jobId: string) => api(`/matches/job/${jobId}`),
  myMatches: () => api("/matches/mine"),
  acceptMatch: (id: string) => api(`/matches/${id}/accept`, { method: "POST" }),
  rejectMatch: (id: string) => api(`/matches/${id}/reject`, { method: "POST" }),
  submitInterview: (id: string, answers: string[]) =>
    api(`/matches/${id}/interview`, { method: "POST", body: JSON.stringify(answers) }),
  proposePrice: (id: string, amount: number) =>
    api(`/matches/${id}/propose-price`, { method: "POST", body: JSON.stringify({ amount }) }),
  confirmPrice: (id: string) => api(`/matches/${id}/confirm-price`, { method: "POST" }),
  declinePrice: (id: string) => api(`/matches/${id}/decline-price`, { method: "POST" }),

  // Jobs Sprint 2
  generateJobDraft: (idea: string) => api("/jobs/generate", { method: "POST", body: JSON.stringify({ idea }) }),
  submitDeliverables: (jobId: string, description: string, url: string) =>
    api(`/jobs/${jobId}/deliverables`, { method: "POST", body: JSON.stringify({ description, url }) }),
  fairPrice: (jobId: string) => api(`/jobs/${jobId}/fair-price`),

  // Contracts
  myContracts: () => api("/contracts/mine"),
  getContract: (id: string) => api(`/contracts/${id}`),
  submitMilestone: (contractId: string, milestoneId: string) =>
    api(`/contracts/${contractId}/milestones/${milestoneId}/submit`, { method: "POST" }),
  releaseMilestone: (contractId: string, milestoneId: string) =>
    api(`/contracts/${contractId}/milestones/${milestoneId}/release`, { method: "POST" }),
  requestRefund: (id: string) => api(`/contracts/${id}/request-refund`, { method: "POST" }),

  // Ratings
  createRating: (data: Record<string, unknown>) =>
    api("/ratings", { method: "POST", body: JSON.stringify(data) }),
  userRatings: (id: string) => api(`/ratings/user/${id}`),

  // Analytics / Admin
  analytics: () => api("/analytics/dashboard"),
  adminStats: () => api("/admin/stats"),
  adminUsers: () => api("/admin/users"),

  // Plans / Notifications
  subscribe: (plan: string) => api(`/plans/subscribe?plan=${plan}`, { method: "POST" }),
  notifications: () => api("/notifications"),
  readNotifications: () => api("/notifications/read-all", { method: "POST" }),

  // Referrals (#15)
  referrals: () => api("/referrals/me"),

  // #F1/#F6 AI Factory (listings + video scripts)
  generateListing: (data: { product_name: string; description?: string; source_url?: string; language?: string; marketplace?: string }) =>
    api("/factory/listing", { method: "POST", body: JSON.stringify(data) }),
  generateVideoScript: (data: { product_name: string; description?: string; language?: string }) =>
    api("/factory/video-script", { method: "POST", body: JSON.stringify(data) }),
  listingHistory: () => api("/factory/history"),

  // #F2 Global currency & tax
  fxRates: () => api("/fx/rates", { auth: false }),
  taxHint: (countryCode: string) => api(`/fx/tax-hint/${encodeURIComponent(countryCode || "DEFAULT")}`, { auth: false }),

  // #F3 AI Contract & Compliance Generator
  contractAgreement: (contractId: string, language: string) => api(`/contracts/${contractId}/agreement?language=${language}`),

  // #F4 Smart Supplier Risk Score
  riskScore: (userId: string) => api(`/users/${userId}/risk-score`, { auth: false }),

  // #F5 AI Co-Pilot
  askCopilot: (jobId: string, question: string, language: string) =>
    api("/copilot/ask", { method: "POST", body: JSON.stringify({ job_id: jobId, question, language }) }),
  copilotHistory: (jobId: string) => api(`/copilot/history/${jobId}`),

  // #F7 Global Talent Time-Zone Auto-Scheduler
  matchSchedule: (matchId: string) => api(`/matches/${matchId}/schedule`),

  // #F8 White-label / Reseller API keys
  createApiKey: (name: string, brandName: string) =>
    api("/developer/keys", { method: "POST", body: JSON.stringify({ name, brand_name: brandName }) }),
  listApiKeys: () => api("/developer/keys"),
  revokeApiKey: (id: string) => api(`/developer/keys/${id}`, { method: "DELETE" }),

  // Payments (Stripe checkout, real money movement)
  paymentsConfig: () => api("/payments/config", { auth: false }),
  checkoutMilestone: (contractId: string, milestoneId: string) =>
    api(`/payments/checkout/${contractId}/${milestoneId}`, { method: "POST" }),
};
