import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Text, Float, Date, DateTime, Boolean, ForeignKey, JSON, Integer
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=gen_id)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="client", index=True)  # client | freelancer | admin
    first_name = Column(String(100), nullable=False, default="")
    last_name = Column(String(100), nullable=False, default="")
    company = Column(String(200), default="")
    bio = Column(Text, default="")
    location = Column(String(255), default="")
    country = Column(String(100), default="")
    languages = Column(JSON, default=list)
    skills = Column(JSON, default=list)
    hourly_rate = Column(Float, nullable=True)
    availability = Column(String(20), default="available", index=True)  # available | busy
    rating = Column(Float, default=5.0)
    rating_count = Column(Integer, default=0)
    total_jobs = Column(Integer, default=0)
    completed_jobs = Column(Integer, default=0)
    plan = Column(String(20), default="free", index=True)  # free | starter | pro | enterprise
    referral_code = Column(String(20), unique=True, index=True)
    referred_by = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    embedding_json = Column(Text, nullable=True)
    # AI Proposal Autopilot (#13)
    auto_accept_enabled = Column(Boolean, default=False)
    auto_accept_min_budget = Column(Float, nullable=True)
    auto_accept_min_score = Column(Float, nullable=True)
    # Stablecoin payouts (#6)
    payout_method = Column(String(20), default="bank")  # bank | stablecoin
    payout_address = Column(String(255), nullable=True)

    jobs_created = relationship("Job", back_populates="client", foreign_keys="Job.client_id")
    matches = relationship("Match", back_populates="freelancer", foreign_keys="Match.freelancer_id")
    ratings_given = relationship("Rating", back_populates="from_user", foreign_keys="Rating.from_user_id")
    ratings_received = relationship("Rating", back_populates="to_user", foreign_keys="Rating.to_user_id")
    notifications = relationship("Notification", back_populates="user")

    @property
    def display_name(self) -> str:
        return (self.first_name + " " + self.last_name).strip() or self.company or self.email


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id = Column(String(32), primary_key=True, default=gen_id)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), default="", index=True)
    subcategory = Column(String(100), default="")
    budget = Column(Float, nullable=False)
    deadline = Column(Date, nullable=False)
    location = Column(String(255), default="")
    required_skills = Column(JSON, default=list)
    status = Column(String(30), default="open", index=True)  # open | matched | in_progress | completed | cancelled
    client_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    ai_analysis = Column(JSON, nullable=True)
    embedding_json = Column(Text, nullable=True)
    # AI Instant Interviews (#1)
    interview_questions = Column(JSON, nullable=True)
    # AI Deliverable Checker (#2)
    deliverables = Column(Text, nullable=True)
    deliverable_url = Column(Text, nullable=True)
    deliverable_report = Column(JSON, nullable=True)

    client = relationship("User", back_populates="jobs_created", foreign_keys=[client_id])
    matches = relationship("Match", back_populates="job", cascade="all, delete-orphan", foreign_keys="Match.job_id")
    contracts = relationship("Contract", back_populates="job", foreign_keys="Contract.job_id")


class Match(TimestampMixin, Base):
    __tablename__ = "matches"

    id = Column(String(32), primary_key=True, default=gen_id)
    job_id = Column(String(32), ForeignKey("jobs.id"), nullable=False, index=True)
    freelancer_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    matched_by = Column(String(20), default="ai")  # ai | manual
    status = Column(String(20), default="pending", index=True)  # pending | accepted | rejected
    message = Column(Text, default="")
    # AI Instant Interviews (#1)
    interview_answers = Column(JSON, nullable=True)
    interview_score = Column(Float, nullable=True)
    interview_feedback = Column(Text, nullable=True)
    interviewed_at = Column(DateTime(timezone=True), nullable=True)
    # AI Price Negotiator (#3)
    agreed_price = Column(Float, nullable=True)
    price_proposal = Column(Float, nullable=True)
    price_status = Column(String(20), default="none", index=True)  # none | proposed | accepted | declined

    job = relationship("Job", back_populates="matches", foreign_keys=[job_id])
    freelancer = relationship("User", back_populates="matches", foreign_keys=[freelancer_id])
    contract = relationship("Contract", back_populates="match", uselist=False, foreign_keys="Contract.match_id")


class Contract(TimestampMixin, Base):
    __tablename__ = "contracts"

    id = Column(String(32), primary_key=True, default=gen_id)
    job_id = Column(String(32), ForeignKey("jobs.id"), nullable=False, index=True)
    match_id = Column(String(32), ForeignKey("matches.id"), nullable=False, index=True)
    client_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    freelancer_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False, default=0)
    fee_rate = Column(Float, nullable=False, default=0.08)
    status = Column(String(20), default="in_progress", index=True)  # in_progress | completed | cancelled | disputed
    completed_at = Column(DateTime(timezone=True), nullable=True)

    job = relationship("Job", back_populates="contracts", foreign_keys=[job_id])
    match = relationship("Match", back_populates="contract", foreign_keys=[match_id])
    payments = relationship("Payment", back_populates="contract", foreign_keys="Payment.contract_id")
    milestones = relationship(
        "Milestone", back_populates="contract", foreign_keys="Milestone.contract_id",
        cascade="all, delete-orphan", order_by="Milestone.order_index",
    )
    commissions = relationship("Commission", back_populates="contract", foreign_keys="Commission.contract_id")
    client = relationship("User", foreign_keys=[client_id])
    freelancer = relationship("User", foreign_keys=[freelancer_id])


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id = Column(String(32), primary_key=True, default=gen_id)
    contract_id = Column(String(32), ForeignKey("contracts.id"), nullable=False, index=True)
    milestone_id = Column(String(32), ForeignKey("milestones.id"), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False, default=0)
    net_amount = Column(Float, nullable=False, default=0)
    status = Column(String(20), default="pending", index=True)  # pending | paid | paid_out | refunded | failed
    provider = Column(String(30), default="stripe")
    provider_ref = Column(String(255), nullable=True)
    payout_method = Column(String(20), default="bank")
    payout_address = Column(String(255), nullable=True)
    payout_date = Column(DateTime(timezone=True), nullable=True)

    contract = relationship("Contract", back_populates="payments", foreign_keys=[contract_id])
    milestone = relationship("Milestone", back_populates="payment", foreign_keys=[milestone_id])


class Milestone(TimestampMixin, Base):
    """#5 Milestones + Auto-Release Escrow: AI-proposed payment splits."""
    __tablename__ = "milestones"

    id = Column(String(32), primary_key=True, default=gen_id)
    contract_id = Column(String(32), ForeignKey("contracts.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    status = Column(String(20), default="pending", index=True)  # pending | in_review | released | rejected
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)

    contract = relationship("Contract", back_populates="milestones", foreign_keys=[contract_id])
    payment = relationship("Payment", back_populates="milestone", uselist=False, foreign_keys="Payment.milestone_id")


class Rating(TimestampMixin, Base):
    __tablename__ = "ratings"

    id = Column(String(32), primary_key=True, default=gen_id)
    from_user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String(32), ForeignKey("jobs.id"), nullable=True)
    score = Column(Float, nullable=False)
    comment = Column(Text, default="")

    from_user = relationship("User", back_populates="ratings_given", foreign_keys=[from_user_id])
    to_user = relationship("User", back_populates="ratings_received", foreign_keys=[to_user_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(30), default="info")
    title = Column(String(255), nullable=False)
    body = Column(Text, default="")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(String(32), primary_key=True, default=gen_id)
    referrer_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    bonus = Column(Float, default=0)
    status = Column(String(20), default="pending")  # pending | paid
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Commission(Base):
    """Referral 2.0 'Earn Forever': 2% level-1, 1% level-2 of contract amount."""
    __tablename__ = "commissions"

    id = Column(String(32), primary_key=True, default=gen_id)
    referrer_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    contract_id = Column(String(32), ForeignKey("contracts.id"), nullable=False, index=True)
    level = Column(Integer, nullable=False, default=1)  # 1 = direct, 2 = second level
    rate = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="paid")  # pending | paid
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="commissions", foreign_keys=[contract_id])
    referrer = relationship("User", foreign_keys=[referrer_id])
    referred = relationship("User", foreign_keys=[referred_id])


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(String(32), primary_key=True, default=gen_id)
    report_date = Column(Date, unique=True, nullable=False, index=True)
    metrics = Column(JSON, default=dict)
    anomalies = Column(JSON, default=list)
    insights = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    plan = Column(String(20), nullable=False)
    price = Column(Float, nullable=False, default=0)
    status = Column(String(20), default="active")  # active | cancelled | expired
    renews_at = Column(Date, nullable=True)


class ApiKey(TimestampMixin, Base):
    """#F8 White-Label / Reseller API: partner keys for embedding DROPIFY's AI
    matching as a branded service inside an agency's own portal."""
    __tablename__ = "api_keys"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, default="API key")
    brand_name = Column(String(100), default="")
    key_prefix = Column(String(16), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False, unique=True)
    active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    request_count = Column(Integer, default=0)

    user = relationship("User", foreign_keys=[user_id])


class Listing(TimestampMixin, Base):
    """#F1 AI Listing Factory: generated multi-marketplace product listings."""
    __tablename__ = "listings"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    source_url = Column(String(500), default="")
    language = Column(String(10), default="pl")
    marketplace = Column(String(30), default="generic")  # shopify | woocommerce | allegro | generic
    content = Column(JSON, default=dict)  # {title, description, bullet_points, seo_tags, meta_description}

    user = relationship("User", foreign_keys=[user_id])


class StoreConnection(TimestampMixin, Base):
    """Sprint-4 e-commerce integrations (#9-#11): a merchant's Shopify or
    BaseLinker (which itself aggregates Allegro + WooCommerce + Shopify order
    sync) account, linked so DROPIFY can call out to the store's own API.
    WooCommerce needs no row here — the WP plugin (integrations/woocommerce/)
    calls the White-Label API (routes/developer.py) directly with its own key."""
    __tablename__ = "store_connections"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # shopify | baselinker
    label = Column(String(255), default="")  # shop domain / account name
    access_token = Column(String(500), nullable=False)
    webhook_secret = Column(String(255), nullable=True)
    active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id])


class CopilotMessage(Base):
    """#F5 AI Co-Pilot: in-job assistant Q&A log."""
    __tablename__ = "copilot_messages"

    id = Column(String(32), primary_key=True, default=gen_id)
    job_id = Column(String(32), ForeignKey("jobs.id"), nullable=False, index=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
