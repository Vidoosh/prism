"""Enumerations for pipeline domain values."""

from enum import StrEnum


class OrganizationType(StrEnum):
    HEALTH_PLAN = "health_plan"
    DIGITAL_HEALTH = "digital_health"
    MSO_PHYSICIAN_GROUP = "mso_physician_group"
    HEALTH_SYSTEM = "health_system"
    DENTAL_NETWORK = "dental_network"
    NON_ICP = "non_icp"
    UNKNOWN = "unknown"


class IcpTier(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class GeographicFootprint(StrEnum):
    SINGLE_STATE = "single_state"
    MULTI_STATE = "multi_state"
    NATIONAL = "national"
    UNKNOWN = "unknown"


class ProviderCountRange(StrEnum):
    UNDER_50 = "<50"
    RANGE_50_200 = "50-200"
    RANGE_200_1000 = "200-1000"
    RANGE_1000_5000 = "1000-5000"
    OVER_5000 = "5000+"
    UNKNOWN = "unknown"


class FundingStage(StrEnum):
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D_PLUS = "series_d_plus"
    PUBLIC = "public"
    UNKNOWN = "unknown"


class DataConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FAILED = "failed"


class ScrapeQuality(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BLOCKED = "blocked"
    THIN = "thin"


class PainSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SignalTier(StrEnum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


class HookTechnique(StrEnum):
    REGULATORY_GUILLOTINE = "regulatory_guillotine"
    REVENUE_LEAKAGE_CALCULATOR = "revenue_leakage_calculator"
    INVISIBLE_LIABILITY = "invisible_liability"
    COMPETITIVE_CLOCK = "competitive_clock"
    SCALING_MATH_TRAP = "scaling_math_trap"
    DATA_CHAOS_MIRROR = "data_chaos_mirror"
    HIRING_INTERCEPT = "hiring_intercept"


class PipelineStage(StrEnum):
    NORMALIZE = "normalize"
    SCRAPE = "scrape"
    AI = "ai"
    SANITY = "sanity"
    HUBSPOT = "hubspot"
