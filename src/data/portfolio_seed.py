"""Seeded portfolio profiles for deterministic transcript generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import cycle
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class PropertyProfile:
    """Represents a serviced property."""

    property_id: str
    street: str
    city: str
    state: str
    postal_code: str
    property_type: str
    valuation: float
    year_built: int

    @property
    def full_address(self) -> str:
        return f"{self.street}, {self.city}, {self.state} {self.postal_code}"

    def to_context(self) -> Dict[str, Any]:
        return {
            "property_id": self.property_id,
            "address": self.full_address,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "property_type": self.property_type,
            "valuation": self.valuation,
            "year_built": self.year_built,
        }


@dataclass(frozen=True)
class LoanProfile:
    """Represents a mortgage or servicing relationship."""

    loan_id: str
    property_id: str
    product_type: str
    balance: float
    interest_rate: float
    payment_amount: float
    escrow_amount: float
    payment_due_day: int
    delinquency_status: str
    start_date: str
    maturity_date: str
    tags: List[str] = field(default_factory=list)
    expected_call_duration: int = 540  # seconds

    def to_context(self) -> Dict[str, Any]:
        return {
            "loan_id": self.loan_id,
            "product": self.product_type,
            "principal_balance": self.balance,
            "interest_rate": self.interest_rate,
            "monthly_payment": self.payment_amount,
            "escrow_amount": self.escrow_amount,
            "payment_due_day": self.payment_due_day,
            "delinquency_status": self.delinquency_status,
            "start_date": self.start_date,
            "maturity_date": self.maturity_date,
            "context_tags": self.tags,
            "tags": self.tags,
            "expected_call_duration": self.expected_call_duration,
        }


@dataclass(frozen=True)
class CustomerProfile:
    """Represents a serviced customer."""

    customer_id: str
    name: str
    segment: str
    email: str
    phone: str
    preferred_channel: str
    lifecycle_status: str
    risk_flags: List[str]
    property_profile: PropertyProfile
    loans: List[LoanProfile]

    def to_context(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "segment": self.segment,
            "email": self.email,
            "phone": self.phone,
            "preferred_channel": self.preferred_channel,
            "lifecycle_status": self.lifecycle_status,
            "risk_flags": self.risk_flags,
        }


@dataclass(frozen=True)
class AdvisorProfile:
    """Represents an advisor supporting the contact center."""

    advisor_id: str
    name: str
    team: str
    role: str
    specialization: str
    experience_years: int
    shift: str

    def to_context(self) -> Dict[str, Any]:
        return {
            "advisor_id": self.advisor_id,
            "name": self.name,
            "team": self.team,
            "role": self.role,
            "specialization": self.specialization,
            "experience_years": self.experience_years,
            "shift": self.shift,
        }


class PortfolioSeedProvider:
    """Provides seeded customer, loan, property, and advisor profiles."""

    _TOPIC_TO_TAG = {
        "hardship_assistance": "loss_mitigation",
        "mortgage_payment_issue": "payments",
        "payment_inquiry": "payments",
        "escrow_inquiry": "escrow",
        "pmi_removal_request": "pmi",
        "refinance_inquiry": "refi",
        "payoff_request": "payoff",
        "complaint_resolution": "retention",
    }

    def __init__(self) -> None:
        self.customers: Dict[str, CustomerProfile] = {
            profile.customer_id: profile for profile in _build_customer_profiles()
        }
        self.advisors: Dict[str, AdvisorProfile] = {
            profile.advisor_id: profile for profile in _build_advisor_profiles()
        }

        if not self.customers:
            raise ValueError("PortfolioSeedProvider requires at least one customer profile")
        if not self.advisors:
            raise ValueError("PortfolioSeedProvider requires at least one advisor profile")

        self._customer_cycle = cycle(self.customers.values())
        self._advisor_cycle = cycle(self.advisors.values())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_customer(self, customer_id: Optional[str] = None) -> CustomerProfile:
        if customer_id:
            profile = self.customers.get(customer_id)
            if not profile:
                raise ValueError(f"Unknown customer_id '{customer_id}'")
            return profile
        return next(self._customer_cycle)

    def get_loan(self, customer: CustomerProfile, loan_id: Optional[str] = None,
                 topic: Optional[str] = None) -> LoanProfile:
        if loan_id:
            for loan in customer.loans:
                if loan.loan_id == loan_id:
                    return loan
            raise ValueError(f"Customer '{customer.customer_id}' has no loan '{loan_id}'")

        if topic:
            tag = self._TOPIC_TO_TAG.get(topic)
            if tag:
                for loan in customer.loans:
                    if tag in loan.tags:
                        return loan
        return customer.loans[0]

    def get_property(self, customer: CustomerProfile, loan: LoanProfile) -> PropertyProfile:
        if loan.property_id != customer.property_profile.property_id:
            return customer.property_profile
        return customer.property_profile

    def get_advisor(self, advisor_id: Optional[str] = None,
                    topic: Optional[str] = None) -> AdvisorProfile:
        if advisor_id:
            profile = self.advisors.get(advisor_id)
            if not profile:
                raise ValueError(f"Unknown advisor_id '{advisor_id}'")
            return profile

        if topic:
            specialization = self._TOPIC_TO_TAG.get(topic)
            if specialization:
                matching = [adv for adv in self.advisors.values() if adv.specialization == specialization]
                if matching:
                    return matching[0]
        return next(self._advisor_cycle)

    def build_generation_context(
        self,
        customer: CustomerProfile,
        loan: LoanProfile,
        property_profile: PropertyProfile,
        advisor: AdvisorProfile,
    ) -> Dict[str, Dict[str, Any]]:
        """Compose the structured context passed to the transcript agent."""

        return {
            "customer_profile": customer.to_context(),
            "loan_profile": loan.to_context(),
            "property_profile": property_profile.to_context(),
            "advisor_profile": advisor.to_context(),
        }

    def apply_metadata_to_transcript(
        self,
        transcript: Any,
        customer: CustomerProfile,
        loan: LoanProfile,
        property_profile: PropertyProfile,
        advisor: AdvisorProfile,
    ) -> None:
        """Populate canonical metadata on the generated transcript object."""

        transcript.customer_id = customer.customer_id
        transcript.customer_name = customer.name
        transcript.customer_segment = customer.segment
        transcript.customer_email = customer.email
        transcript.customer_phone = customer.phone
        transcript.preferred_channel = customer.preferred_channel
        transcript.customer_risk_flags = customer.risk_flags

        transcript.loan_id = loan.loan_id
        transcript.loan_product = loan.product_type
        transcript.loan_balance = loan.balance
        transcript.loan_interest_rate = loan.interest_rate
        transcript.loan_payment_amount = loan.payment_amount
        transcript.loan_payment_due_day = loan.payment_due_day
        transcript.loan_delinquency_status = loan.delinquency_status
        transcript.loan_escrow_amount = loan.escrow_amount
        transcript.loan_expected_call_duration = loan.expected_call_duration

        transcript.property_id = property_profile.property_id
        transcript.property_address = property_profile.full_address
        transcript.property_city = property_profile.city
        transcript.property_state = property_profile.state
        transcript.property_postal_code = property_profile.postal_code
        transcript.property_type = property_profile.property_type
        transcript.property_valuation = property_profile.valuation

        transcript.advisor_id = advisor.advisor_id
        transcript.advisor_name = advisor.name
        transcript.advisor_team = advisor.team
        transcript.advisor_role = advisor.role
        transcript.advisor_specialization = advisor.specialization
        transcript.advisor_experience_years = advisor.experience_years

        # Attach structured profiles for downstream consumers
        transcript.customer_profile = customer.to_context()
        transcript.loan_profile = loan.to_context()
        transcript.property_profile = property_profile.to_context()
        transcript.advisor_profile = advisor.to_context()

    def estimate_call_duration(self, topic: str, loan: LoanProfile) -> int:
        """Provide a consistent call duration estimate when the LLM omits it."""

        adjustments = {
            "hardship_assistance": 180,
            "mortgage_payment_issue": 120,
            "escrow_inquiry": 60,
            "pmi_removal_request": 90,
            "refinance_inquiry": 150,
        }
        return loan.expected_call_duration + adjustments.get(topic, 0)

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def list_customers(self) -> List[Dict[str, Any]]:
        return [
            {
                **profile.to_context(),
                "display_name": f"{profile.name} ({profile.segment})",
                "property": profile.property_profile.to_context(),
                "loans": [loan.to_context() for loan in profile.loans],
            }
            for profile in self.customers.values()
        ]

    def list_advisors(self) -> List[Dict[str, Any]]:
        return [
            {
                **advisor.to_context(),
                "display_name": f"{advisor.name} · {advisor.team}",
            }
            for advisor in self.advisors.values()
        ]

    def serialize_profiles(self) -> Dict[str, Any]:
        return {
            "customers": self.list_customers(),
            "advisors": self.list_advisors(),
            "topics": sorted(self._TOPIC_TO_TAG.keys()),
        }


# ----------------------------------------------------------------------
# Seed Data Construction
# ----------------------------------------------------------------------


def _build_customer_profiles() -> List[CustomerProfile]:
    property_primary = PropertyProfile(
        property_id="PROP-4477",
        street="1284 Willow Creek Lane",
        city="Denver",
        state="CO",
        postal_code="80211",
        property_type="Single Family",
        valuation=612_500.0,
        year_built=2012,
    )

    property_secondary = PropertyProfile(
        property_id="PROP-7331",
        street="88 Seaside Drive",
        city="Tampa",
        state="FL",
        postal_code="33602",
        property_type="Townhome",
        valuation=387_900.0,
        year_built=2015,
    )

    property_vip = PropertyProfile(
        property_id="PROP-VIP-9001",
        street="4501 Bayview Heights",
        city="San Diego",
        state="CA",
        postal_code="92106",
        property_type="Luxury Condo",
        valuation=1_450_000.0,
        year_built=2018,
    )

    property_midwest = PropertyProfile(
        property_id="PROP-5210",
        street="975 Harbor Point",
        city="Milwaukee",
        state="WI",
        postal_code="53202",
        property_type="Duplex",
        valuation=289_400.0,
        year_built=2008,
    )

    property_southwest = PropertyProfile(
        property_id="PROP-8820",
        street="742 Desert Bloom Trail",
        city="Phoenix",
        state="AZ",
        postal_code="85016",
        property_type="Single Family",
        valuation=465_700.0,
        year_built=2016,
    )

    property_northeast = PropertyProfile(
        property_id="PROP-3010",
        street="211 Harborview Terrace",
        city="Boston",
        state="MA",
        postal_code="02108",
        property_type="Brownstone",
        valuation=815_250.0,
        year_built=1898,
    )

    property_mountain = PropertyProfile(
        property_id="PROP-6642",
        street="18 Summit Crest Way",
        city="Boise",
        state="ID",
        postal_code="83702",
        property_type="Single Family",
        valuation=395_100.0,
        year_built=2010,
    )

    property_southeast = PropertyProfile(
        property_id="PROP-5575",
        street="403 Magnolia Ridge",
        city="Charleston",
        state="SC",
        postal_code="29401",
        property_type="Historic",
        valuation=598_900.0,
        year_built=1907,
    )

    base_profiles = [
        CustomerProfile(
            customer_id="CUST-1001",
            name="Amelia Hughes",
            segment="Prime",
            email="amelia.hughes@example.com",
            phone="303-555-0195",
            preferred_channel="phone",
            lifecycle_status="in_repayment",
            risk_flags=["on_time_payer"],
            property_profile=property_primary,
            loans=[
                LoanProfile(
                    loan_id="LN-8821",
                    property_id=property_primary.property_id,
                    product_type="30 Year Fixed",
                    balance=412_300.0,
                    interest_rate=3.75,
                    payment_amount=2_145.32,
                    escrow_amount=612.48,
                    payment_due_day=1,
                    delinquency_status="current",
                    start_date="2019-04-01",
                    maturity_date="2049-04-01",
                    tags=["escrow", "payments", "refi"],
                    expected_call_duration=520,
                ),
            ],
        ),
        CustomerProfile(
            customer_id="CUST-1044",
            name="Devon Price",
            segment="Emerging Affluent",
            email="devon.price@example.com",
            phone="813-555-4420",
            preferred_channel="sms",
            lifecycle_status="early_stage",
            risk_flags=["escrow_review"],
            property_profile=property_secondary,
            loans=[
                LoanProfile(
                    loan_id="LN-6710",
                    property_id=property_secondary.property_id,
                    product_type="5/1 ARM",
                    balance=298_775.0,
                    interest_rate=4.25,
                    payment_amount=1_746.58,
                    escrow_amount=388.11,
                    payment_due_day=12,
                    delinquency_status="current",
                    start_date="2021-07-15",
                    maturity_date="2051-07-15",
                    tags=["escrow", "pmi"],
                    expected_call_duration=480,
                ),
            ],
        ),
        CustomerProfile(
            customer_id="CUST-2001",
            name="Lina Moreno",
            segment="At Risk",
            email="lina.moreno@example.com",
            phone="414-555-8821",
            preferred_channel="email",
            lifecycle_status="loss_mitigation",
            risk_flags=["hardship_plan", "delinquent_30"],
            property_profile=property_midwest,
            loans=[
                LoanProfile(
                    loan_id="LN-5594",
                    property_id=property_midwest.property_id,
                    product_type="FHA 30 Year",
                    balance=221_900.0,
                    interest_rate=3.5,
                    payment_amount=1_145.09,
                    escrow_amount=275.33,
                    payment_due_day=5,
                    delinquency_status="30_days_past_due",
                    start_date="2016-02-01",
                    maturity_date="2046-02-01",
                    tags=["loss_mitigation", "payments"],
                    expected_call_duration=620,
                ),
            ],
        ),
        CustomerProfile(
            customer_id="CUST_VIP001",
            name="Jordan Bailey",
            segment="Private Banking",
            email="jordan.bailey@example.com",
            phone="619-555-7710",
            preferred_channel="phone",
            lifecycle_status="seasoned",
            risk_flags=["pmi_eligible"],
            property_profile=property_vip,
            loans=[
                LoanProfile(
                    loan_id="LN-VIP-9900",
                    property_id=property_vip.property_id,
                    product_type="15 Year Fixed",
                    balance=895_000.0,
                    interest_rate=2.85,
                    payment_amount=6_118.44,
                    escrow_amount=1_245.31,
                    payment_due_day=25,
                    delinquency_status="current",
                    start_date="2020-11-01",
                    maturity_date="2035-11-01",
                    tags=["refi", "pmi", "payoff"],
                    expected_call_duration=560,
                ),
            ],
        ),
        CustomerProfile(
            customer_id="CUST-3055",
            name="Ethan Parker",
            segment="Mass Affluent",
            email="ethan.parker@example.com",
            phone="480-555-4477",
            preferred_channel="mobile_app",
            lifecycle_status="in_repayment",
            risk_flags=["auto_pay_enrolled"],
            property_profile=property_southwest,
            loans=[
                LoanProfile(
                    loan_id="LN-7722",
                    property_id=property_southwest.property_id,
                    product_type="20 Year Fixed",
                    balance=327_450.0,
                    interest_rate=4.05,
                    payment_amount=1_992.17,
                    escrow_amount=421.63,
                    payment_due_day=3,
                    delinquency_status="current",
                    start_date="2022-03-01",
                    maturity_date="2042-03-01",
                    tags=["payments", "escrow"],
                    expected_call_duration=495,
                ),
            ],
        ),
        CustomerProfile(
            customer_id="CUST-4411",
            name="Priya Shah",
            segment="Emerging Affluent",
            email="priya.shah@example.com",
            phone="617-555-3382",
            preferred_channel="email",
            lifecycle_status="refi_consideration",
            risk_flags=["rate_shopper"],
            property_profile=property_northeast,
            loans=[
                LoanProfile(
                    loan_id="LN-8830",
                    property_id=property_northeast.property_id,
                    product_type="30 Year Fixed",
                    balance=612_900.0,
                    interest_rate=3.95,
                    payment_amount=3_014.05,
                    escrow_amount=789.44,
                    payment_due_day=17,
                    delinquency_status="current",
                    start_date="2018-09-01",
                    maturity_date="2048-09-01",
                    tags=["refi", "escrow", "pmi"],
                    expected_call_duration=545,
                ),
            ],
        ),
        CustomerProfile(
            customer_id="CUST-5090",
            name="Marcus Lee",
            segment="At Risk",
            email="marcus.lee@example.com",
            phone="208-555-6751",
            preferred_channel="phone",
            lifecycle_status="loss_mitigation",
            risk_flags=["payment_plan_review"],
            property_profile=property_mountain,
            loans=[
                LoanProfile(
                    loan_id="LN-3349",
                    property_id=property_mountain.property_id,
                    product_type="FHA 30 Year",
                    balance=245_780.0,
                    interest_rate=4.6,
                    payment_amount=1_382.24,
                    escrow_amount=259.60,
                    payment_due_day=22,
                    delinquency_status="60_days_past_due",
                    start_date="2017-05-01",
                    maturity_date="2047-05-01",
                    tags=["loss_mitigation", "payments"],
                    expected_call_duration=640,
                ),
            ],
        ),
        CustomerProfile(
            customer_id="CUST-6125",
            name="Renee Caldwell",
            segment="Prime",
            email="renee.caldwell@example.com",
            phone="843-555-2244",
            preferred_channel="sms",
            lifecycle_status="seasoned",
            risk_flags=["payoff_pending"],
            property_profile=property_southeast,
            loans=[
                LoanProfile(
                    loan_id="LN-9902",
                    property_id=property_southeast.property_id,
                    product_type="Jumbo ARM",
                    balance=432_150.0,
                    interest_rate=3.15,
                    payment_amount=2_486.78,
                    escrow_amount=668.05,
                    payment_due_day=28,
                    delinquency_status="current",
                    start_date="2015-08-01",
                    maturity_date="2045-08-01",
                    tags=["payoff", "refi"],
                    expected_call_duration=515,
                ),
            ],
        ),
    ]

    additional_profiles: List[CustomerProfile] = []

    template_configs = [
        {
            "city": "Portland",
            "state": "OR",
            "property_type": "Townhome",
            "street_suffix": "Cedar Crest Way",
            "base_value": 425_000.0,
            "base_balance": 285_000.0,
            "product_type": "30 Year Fixed",
            "base_rate": 3.65,
            "payment_factor": 0.0056,
            "risk_flag": "escrow_review",
            "lifecycle_status": "in_repayment",
            "preferred_channel": "email",
            "delinquency_statuses": ["current", "current", "30_days_past_due"],
            "tags": ["escrow", "payments"],
            "segment": "Prime",
            "base_duration": 520,
        },
        {
            "city": "Austin",
            "state": "TX",
            "property_type": "Single Family",
            "street_suffix": "Live Oak Drive",
            "base_value": 512_000.0,
            "base_balance": 348_500.0,
            "product_type": "15 Year Fixed",
            "base_rate": 3.25,
            "payment_factor": 0.0068,
            "risk_flag": "refi_interested",
            "lifecycle_status": "refi_consideration",
            "preferred_channel": "phone",
            "delinquency_statuses": ["current", "current", "current"],
            "tags": ["refi", "payments"],
            "segment": "Emerging Affluent",
            "base_duration": 505,
        },
        {
            "city": "Cleveland",
            "state": "OH",
            "property_type": "Duplex",
            "street_suffix": "Lakeview Terrace",
            "base_value": 268_400.0,
            "base_balance": 189_750.0,
            "product_type": "FHA 30 Year",
            "base_rate": 4.45,
            "payment_factor": 0.0052,
            "risk_flag": "hardship_plan",
            "lifecycle_status": "loss_mitigation",
            "preferred_channel": "sms",
            "delinquency_statuses": ["30_days_past_due", "60_days_past_due", "current"],
            "tags": ["loss_mitigation", "payments"],
            "segment": "At Risk",
            "base_duration": 630,
        },
        {
            "city": "Seattle",
            "state": "WA",
            "property_type": "Condo",
            "street_suffix": "Harbor Lights Way",
            "base_value": 688_900.0,
            "base_balance": 441_300.0,
            "product_type": "5/1 ARM",
            "base_rate": 3.85,
            "payment_factor": 0.0061,
            "risk_flag": "rate_shopper",
            "lifecycle_status": "refi_consideration",
            "preferred_channel": "mobile_app",
            "delinquency_statuses": ["current", "current", "current"],
            "tags": ["refi", "escrow"],
            "segment": "Mass Affluent",
            "base_duration": 540,
        },
        {
            "city": "Atlanta",
            "state": "GA",
            "property_type": "Single Family",
            "street_suffix": "Peachtree Hollow",
            "base_value": 379_200.0,
            "base_balance": 256_800.0,
            "product_type": "30 Year Fixed",
            "base_rate": 3.95,
            "payment_factor": 0.0058,
            "risk_flag": "auto_pay_enrolled",
            "lifecycle_status": "in_repayment",
            "preferred_channel": "email",
            "delinquency_statuses": ["current", "current", "current"],
            "tags": ["payments", "escrow"],
            "segment": "Prime",
            "base_duration": 490,
        },
        {
            "city": "Chicago",
            "state": "IL",
            "property_type": "Brownstone",
            "street_suffix": "Lakeshore Promenade",
            "base_value": 732_400.0,
            "base_balance": 515_900.0,
            "product_type": "20 Year Fixed",
            "base_rate": 3.55,
            "payment_factor": 0.0064,
            "risk_flag": "pmi_eligible",
            "lifecycle_status": "seasoned",
            "preferred_channel": "phone",
            "delinquency_statuses": ["current", "current", "30_days_past_due"],
            "tags": ["pmi", "refi"],
            "segment": "Private Banking",
            "base_duration": 560,
        },
        {
            "city": "Denver",
            "state": "CO",
            "property_type": "Townhome",
            "street_suffix": "Highland Summit Road",
            "base_value": 418_300.0,
            "base_balance": 287_450.0,
            "product_type": "7/1 ARM",
            "base_rate": 3.75,
            "payment_factor": 0.0060,
            "risk_flag": "escrow_review",
            "lifecycle_status": "in_repayment",
            "preferred_channel": "mobile_app",
            "delinquency_statuses": ["current", "current", "current"],
            "tags": ["escrow", "payments"],
            "segment": "Prime",
            "base_duration": 515,
        },
        {
            "city": "Miami",
            "state": "FL",
            "property_type": "Condo",
            "street_suffix": "Ocean Breeze Circle",
            "base_value": 529_600.0,
            "base_balance": 354_750.0,
            "product_type": "30 Year Fixed",
            "base_rate": 4.05,
            "payment_factor": 0.0059,
            "risk_flag": "payoff_pending",
            "lifecycle_status": "seasoned",
            "preferred_channel": "sms",
            "delinquency_statuses": ["current", "current", "current"],
            "tags": ["payoff", "refi"],
            "segment": "Prime",
            "base_duration": 505,
        },
        {
            "city": "Nashville",
            "state": "TN",
            "property_type": "Single Family",
            "street_suffix": "Cumberland Ridge",
            "base_value": 398_800.0,
            "base_balance": 276_400.0,
            "product_type": "FHA 30 Year",
            "base_rate": 4.35,
            "payment_factor": 0.0054,
            "risk_flag": "payment_plan_review",
            "lifecycle_status": "loss_mitigation",
            "preferred_channel": "phone",
            "delinquency_statuses": ["30_days_past_due", "60_days_past_due", "current"],
            "tags": ["loss_mitigation", "payments"],
            "segment": "At Risk",
            "base_duration": 620,
        },
        {
            "city": "Minneapolis",
            "state": "MN",
            "property_type": "Duplex",
            "street_suffix": "North Loop Avenue",
            "base_value": 312_500.0,
            "base_balance": 214_200.0,
            "product_type": "30 Year Fixed",
            "base_rate": 3.9,
            "payment_factor": 0.0057,
            "risk_flag": "escrow_adjustment",
            "lifecycle_status": "in_repayment",
            "preferred_channel": "email",
            "delinquency_statuses": ["current", "current", "30_days_past_due"],
            "tags": ["escrow", "payments"],
            "segment": "Prime",
            "base_duration": 500,
        },
        {
            "city": "Sacramento",
            "state": "CA",
            "property_type": "Single Family",
            "street_suffix": "River Bend Lane",
            "base_value": 486_900.0,
            "base_balance": 332_600.0,
            "product_type": "20 Year Fixed",
            "base_rate": 3.45,
            "payment_factor": 0.0062,
            "risk_flag": "refi_interested",
            "lifecycle_status": "refi_consideration",
            "preferred_channel": "mobile_app",
            "delinquency_statuses": ["current", "current", "current"],
            "tags": ["refi", "pmi"],
            "segment": "Emerging Affluent",
            "base_duration": 530,
        },
        {
            "city": "Charlotte",
            "state": "NC",
            "property_type": "Townhome",
            "street_suffix": "Blue Ridge Crossing",
            "base_value": 351_400.0,
            "base_balance": 245_900.0,
            "product_type": "30 Year Fixed",
            "base_rate": 3.8,
            "payment_factor": 0.0058,
            "risk_flag": "auto_pay_enrolled",
            "lifecycle_status": "in_repayment",
            "preferred_channel": "email",
            "delinquency_statuses": ["current", "current", "current"],
            "tags": ["payments", "escrow"],
            "segment": "Prime",
            "base_duration": 495,
        },
        {
            "city": "Phoenix",
            "state": "AZ",
            "property_type": "Single Family",
            "street_suffix": "Saguaro Vista",
            "base_value": 407_200.0,
            "base_balance": 279_100.0,
            "product_type": "5/1 ARM",
            "base_rate": 3.7,
            "payment_factor": 0.0060,
            "risk_flag": "rate_shopper",
            "lifecycle_status": "seasoned",
            "preferred_channel": "sms",
            "delinquency_statuses": ["current", "current", "current"],
            "tags": ["refi", "payments"],
            "segment": "Mass Affluent",
            "base_duration": 510,
        },
    ]

    first_names = [
        "Avery",
        "Jordan",
        "Skylar",
        "Parker",
        "Dakota",
        "Rowan",
        "Emerson",
        "Reese",
        "Hayden",
        "Blair",
        "Finley",
        "Sloane",
    ]

    last_names = [
        "Mitchell",
        "Sanchez",
        "Kim",
        "Reynolds",
        "Patel",
        "Nguyen",
        "Henderson",
        "Lopez",
        "Carson",
        "Bennett",
        "Fletcher",
        "Grayson",
    ]

    total_generated = 36

    for idx in range(total_generated):
        template = template_configs[idx % len(template_configs)]
        first = first_names[idx % len(first_names)]
        last = last_names[(idx // len(first_names)) % len(last_names)]
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}@example.com"
        phone = f"{200 + idx}-555-{7000 + idx:04d}"

        property_profile = PropertyProfile(
            property_id=f"PROP-AUTO-{idx:04d}",
            street=f"{104 + idx} {template['street_suffix']}",
            city=template["city"],
            state=template["state"],
            postal_code=f"{90000 + idx:05d}",
            property_type=template["property_type"],
            valuation=template["base_value"] + (idx % 5) * 12_500.0,
            year_built=1995 + (idx % 25),
        )

        delinquency_status = template["delinquency_statuses"][idx % len(template["delinquency_statuses"])]
        balance = template["base_balance"] + (idx % 6) * 11_750.0
        interest_rate = round(template["base_rate"] + (idx % 4) * 0.12, 2)
        payment_amount = round(balance * template["payment_factor"], 2)
        escrow_amount = round((property_profile.valuation * 0.0025) / 12, 2)
        start_year = 2014 + (idx % 6)
        start_month = (idx % 12) + 1
        maturity_year = start_year + 30

        loan_profile = LoanProfile(
            loan_id=f"LN-AUTO-{idx:04d}",
            property_id=property_profile.property_id,
            product_type=template["product_type"],
            balance=balance,
            interest_rate=interest_rate,
            payment_amount=payment_amount,
            escrow_amount=escrow_amount,
            payment_due_day=(idx % 28) + 1,
            delinquency_status=delinquency_status,
            start_date=f"{start_year}-{start_month:02d}-01",
            maturity_date=f"{maturity_year}-{start_month:02d}-01",
            tags=template["tags"],
            expected_call_duration=template["base_duration"] + (idx % 5) * 18,
        )

        additional_profiles.append(
            CustomerProfile(
                customer_id=f"CUST-AUTO-{idx:04d}",
                name=name,
                segment=template["segment"],
                email=email,
                phone=phone,
                preferred_channel=template["preferred_channel"],
                lifecycle_status=template["lifecycle_status"],
                risk_flags=[template["risk_flag"]],
                property_profile=property_profile,
                loans=[loan_profile],
            )
        )

    base_profiles.extend(additional_profiles)
    return base_profiles


def _build_advisor_profiles() -> List[AdvisorProfile]:
    return [
        AdvisorProfile(
            advisor_id="ADV-301",
            name="Riley Chen",
            team="Escrow Operations",
            role="Senior Advisor",
            specialization="escrow",
            experience_years=8,
            shift="day",
        ),
        AdvisorProfile(
            advisor_id="ADV-412",
            name="Morgan Patel",
            team="Loss Mitigation",
            role="Hardship Specialist",
            specialization="loss_mitigation",
            experience_years=11,
            shift="swing",
        ),
        AdvisorProfile(
            advisor_id="ADV-509",
            name="Casey Alvarez",
            team="Retention & Refis",
            role="Relationship Manager",
            specialization="refi",
            experience_years=9,
            shift="day",
        ),
        AdvisorProfile(
            advisor_id="ADV-615",
            name="Taylor Brooks",
            team="Customer Care",
            role="Generalist",
            specialization="payments",
            experience_years=6,
            shift="evening",
        ),
        AdvisorProfile(
            advisor_id="ADV-744",
            name="Jamie Singh",
            team="Mortgage Payoff",
            role="Payoff Specialist",
            specialization="payoff",
            experience_years=7,
            shift="day",
        ),
        AdvisorProfile(
            advisor_id="ADV-803",
            name="Noah Thompson",
            team="Payoff Desk",
            role="Payoff Specialist",
            specialization="payoff",
            experience_years=10,
            shift="day",
        ),
        AdvisorProfile(
            advisor_id="ADV-926",
            name="Sasha Nguyen",
            team="Customer Advocacy",
            role="Escalation Lead",
            specialization="retention",
            experience_years=9,
            shift="evening",
        ),
        AdvisorProfile(
            advisor_id="ADV-978",
            name="Harper James",
            team="Mortgage Renewal",
            role="Refinance Strategist",
            specialization="refi",
            experience_years=8,
            shift="day",
        ),
        AdvisorProfile(
            advisor_id="ADV-105",
            name="Imani Douglas",
            team="Hardship Support",
            role="Senior Specialist",
            specialization="loss_mitigation",
            experience_years=13,
            shift="swing",
        ),
    ]


__all__ = ["PortfolioSeedProvider"]
