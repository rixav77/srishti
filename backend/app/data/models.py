from pydantic import BaseModel, Field
from enum import Enum


# --- Enums ---

class DomainType(str, Enum):
    CONFERENCE = "conference"
    MUSIC_FESTIVAL = "music_festival"
    SPORTING_EVENT = "sporting_event"


class AgentName(str, Enum):
    SPONSOR = "sponsor_agent"
    SPEAKER = "speaker_agent"
    EXHIBITOR = "exhibitor_agent"
    VENUE = "venue_agent"
    PRICING = "pricing_agent"
    GTM = "gtm_agent"
    OPS = "ops_agent"


# --- Event Configuration ---

class EventConfig(BaseModel):
    domain: DomainType = DomainType.CONFERENCE
    category: str = Field(..., description="e.g., AI, Web3, Rock, Cricket")
    subcategory: str | None = None
    geography: str = Field(..., description="e.g., India, USA, Europe")
    city: str | None = None
    target_audience: int = Field(..., ge=50, le=100000)
    budget_min: float | None = None
    budget_max: float | None = None
    currency: str = "INR"
    start_date: str | None = None
    end_date: str | None = None
    event_name: str | None = None
    description: str | None = None


class EventPlanResponse(BaseModel):
    event_id: str
    status: str
    message: str


class EventStatus(BaseModel):
    event_id: str
    status: str
    completed_agents: list[str]
    total_agents: int


# --- Agent Outputs ---

class ScoredEntity(BaseModel):
    rank: int
    name: str
    total_score: float = Field(..., ge=0, le=1)
    scores: dict[str, float] = {}
    evidence: dict = {}
    explanation: str = ""
    data_sources: list[str] = []


class SponsorResult(ScoredEntity):
    company_name: str = ""
    recommended_tier: str = ""
    industry: str = ""
    past_sponsorships: list[str] = []
    outreach_draft: dict = {}


class SpeakerResult(ScoredEntity):
    role: str = ""  # keynote, panel, workshop
    topics: list[str] = []
    linkedin_url: str = ""
    followers: int = 0
    outreach_draft: dict = {}
    estimated_fee_range: str = ""


class VenueResult(ScoredEntity):
    city: str = ""
    country: str = ""
    capacity: int = 0
    daily_rate: float = 0
    venue_type: str = ""
    amenities: list[str] = []
    past_events: list[str] = []
    coordinates: dict = {}


class ExhibitorResult(ScoredEntity):
    category: str = ""  # startup, enterprise, tools, individual
    exhibition_history: list[str] = []
    booth_tier: str = ""


class PricingTier(BaseModel):
    name: str
    price: float
    currency: str = "INR"
    allocation_pct: float
    estimated_sales: int
    revenue: float


class PricingResult(BaseModel):
    tiers: list[PricingTier] = []
    total_projected_revenue: float = 0
    break_even_attendees: int = 0
    estimated_total_attendees: int = 0
    confidence: float = 0
    sensitivity: dict = {}
    break_even: dict = {}


class CommunityResult(ScoredEntity):
    platform: str = ""
    members: int = 0
    activity_level: str = ""
    partnership_suggestion: str = ""


class GTMResult(BaseModel):
    communities: list[CommunityResult] = []
    strategy_phases: list[dict] = []
    messaging: dict = {}
    estimated_reach: int = 0


class ScheduleSlot(BaseModel):
    time: str
    slot_type: str  # keynote, panel, workshop, break, networking
    title: str
    speaker: str = ""
    room: str = ""
    track: str = ""


class OpsResult(BaseModel):
    schedule: list[dict] = []  # days -> slots
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    resource_plan: dict = {}


# --- Consolidated Plan ---

class AgentOutput(BaseModel):
    agent_name: str
    status: str = "pending"
    results: dict = {}
    confidence_score: float = 0
    explanation: str = ""
    data_sources_used: list[str] = []
    execution_time_ms: int = 0


class ConsolidatedPlan(BaseModel):
    event_id: str
    config: EventConfig
    sponsor_results: list[SponsorResult] = []
    speaker_results: list[SpeakerResult] = []
    venue_results: list[VenueResult] = []
    exhibitor_results: list[ExhibitorResult] = []
    pricing: PricingResult | None = None
    gtm: GTMResult | None = None
    ops: OpsResult | None = None
    agent_outputs: list[AgentOutput] = []
