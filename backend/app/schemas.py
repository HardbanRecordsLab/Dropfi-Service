from datetime import date, datetime
from typing import Optional, List, Any

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(pattern="^(client|freelancer)$")
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    referral_code: str = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ---------- User ----------
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    hourly_rate: Optional[float] = None
    availability: Optional[str] = None
    # AI Proposal Autopilot (#13)
    auto_accept_enabled: Optional[bool] = None
    auto_accept_min_budget: Optional[float] = None
    auto_accept_min_score: Optional[float] = None
    # Stablecoin payouts (#6)
    payout_method: Optional[str] = None
    payout_address: Optional[str] = None


class UserOut(ORMModel):
    id: str
    email: EmailStr
    role: str
    first_name: str
    last_name: str
    company: str
    bio: str
    location: str
    country: str
    languages: List[str]
    skills: List[str]
    hourly_rate: Optional[float] = None
    availability: str
    rating: float
    rating_count: int
    total_jobs: int
    completed_jobs: int
    plan: str
    referral_code: Optional[str] = None
    email_verified: bool = False
    auto_accept_enabled: bool = False
    auto_accept_min_budget: Optional[float] = None
    auto_accept_min_score: Optional[float] = None
    payout_method: str = "bank"
    payout_address: Optional[str] = None
    created_at: datetime


class FreelancerOut(ORMModel):
    id: str
    first_name: str
    last_name: str
    company: str
    bio: str
    location: str
    country: str
    languages: List[str]
    skills: List[str]
    hourly_rate: Optional[float] = None
    availability: str
    rating: float
    rating_count: int
    completed_jobs: int


# ---------- Job ----------
class JobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10)
    category: str = ""
    budget: float = Field(gt=0)
    deadline: date
    location: str = ""
    required_skills: List[str] = []
    interview_questions: Optional[List[str]] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    deadline: Optional[date] = None
    location: Optional[str] = None
    status: Optional[str] = None


class JobOut(ORMModel):
    id: str
    title: str
    description: str
    category: str = ""
    subcategory: str = ""
    budget: float
    deadline: date
    location: str = ""
    required_skills: List[str] = []
    status: str
    client_id: str
    ai_analysis: Optional[dict] = None
    interview_questions: Optional[List[str]] = None
    deliverables: Optional[str] = None
    deliverable_url: Optional[str] = None
    deliverable_report: Optional[dict] = None
    created_at: datetime
    client: Optional["UserOut"] = None


class JobListItem(ORMModel):
    id: str
    title: str
    description: str
    category: str = ""
    subcategory: str = ""
    budget: float
    deadline: date
    location: str = ""
    required_skills: List[str] = []
    status: str
    created_at: datetime
    client: Optional[UserOut] = None
    match_count: int = 0


# ---------- Match ----------
class MatchOut(ORMModel):
    id: str
    job_id: str
    freelancer_id: str
    score: float
    matched_by: str
    status: str
    message: str
    interview_answers: Optional[List[str]] = None
    interview_score: Optional[float] = None
    interview_feedback: Optional[str] = None
    interviewed_at: Optional[datetime] = None
    agreed_price: Optional[float] = None
    price_proposal: Optional[float] = None
    price_status: str = "none"
    created_at: datetime
    freelancer: Optional[FreelancerOut] = None
    job: Optional[JobOut] = None


# ---------- Contract ----------
class MilestoneOut(ORMModel):
    id: str
    contract_id: str
    title: str
    amount: float
    order_index: int
    status: str
    submitted_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    created_at: datetime


class ContractOut(ORMModel):
    id: str
    job_id: str
    match_id: str
    client_id: str
    freelancer_id: str
    amount: float
    platform_fee: float
    fee_rate: float = 0.08
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    job: Optional[JobListItem] = None
    freelancer: Optional[FreelancerOut] = None
    milestones: Optional[List[MilestoneOut]] = None
    released_amount: float = 0
    refund_eligible: bool = False
    refund_reason: str = ""
    dispute_reason: Optional[str] = None
    dispute_raised_by: Optional[str] = None
    dispute_ai_assessment: Optional[str] = None
    disputed_at: Optional[datetime] = None
    dispute_resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


# ---------- Rating ----------
class RatingCreate(BaseModel):
    to_user_id: str
    job_id: Optional[str] = None
    score: float = Field(ge=1, le=5)
    comment: str = ""


class RatingOut(ORMModel):
    id: str
    from_user_id: str
    to_user_id: str
    job_id: Optional[str] = None
    score: float
    comment: str
    created_at: datetime
    from_user: Optional[UserOut] = None


# ---------- Analytics ----------
class AnalyticsOut(BaseModel):
    role: str
    total_jobs: int = 0
    active_jobs: int = 0
    completed_jobs: int = 0
    total_spent: float = 0
    total_earned: float = 0
    match_count: int = 0
    pending_matches: int = 0
    accepted_matches: int = 0
    rating: float = 0
    jobs_this_month: int = 0
    avg_match_time_seconds: Optional[float] = None
    instant_matches: int = 0
    avg_time_to_hire_hours: Optional[float] = None
    recent_jobs: List[Any] = []
    recent_matches: List[Any] = []


# ---------- White-label API (#F8) ----------
class PartnerJobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10)
    budget: float = Field(gt=0)
    deadline: date
    location: str = ""
    required_skills: List[str] = []


class AdminStats(BaseModel):
    users: int
    freelancers: int
    clients: int
    jobs: int
    open_jobs: int
    completed_jobs: int
    matches: int
    contracts: int
    revenue: float
    recent_users: List[Any]
