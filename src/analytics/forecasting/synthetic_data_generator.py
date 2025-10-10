"""Synthetic data generator aligned with the latest transcript and analysis models.

This module is used by CLI/demo scripts to seed SQLite with a realistic dataset
without calling the LLM stack. It relies on the same seeded customer portfolio
that powers the transcript generator, so everything feels consistent.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.data.portfolio_seed import (
    PortfolioSeedProvider,
    AdvisorProfile,
    CustomerProfile,
    LoanProfile,
    PropertyProfile,
)
from src.storage.transcript_store import TranscriptStore
from src.storage.analysis_store import AnalysisStore


class SyntheticDataGenerator:
    """Generate seeded transcripts and analyses for demos/tests."""

    TOPICS = [
        "payment_inquiry",
        "mortgage_payment_issue",
        "escrow_inquiry",
        "pmi_removal_request",
        "refinance_inquiry",
        "hardship_assistance",
        "payoff_request",
        "complaint_resolution",
    ]

    TOPIC_URGENCY = {
        "payment_inquiry": "medium",
        "mortgage_payment_issue": "high",
        "escrow_inquiry": "medium",
        "pmi_removal_request": "low",
        "refinance_inquiry": "medium",
        "hardship_assistance": "high",
        "payoff_request": "medium",
        "complaint_resolution": "high",
    }

    SENTIMENT_SCALE = [
        "Distressed",
        "Frustrated",
        "Anxious",
        "Concerned",
        "Neutral",
        "Calm",
        "Hopeful",
        "Satisfied",
        "Positive",
    ]

    SENTIMENT_BASE_INDEX = {
        "distressed": 0,
        "frustrated": 1,
        "anxious": 2,
        "concerned": 3,
        "neutral": 4,
        "calm": 5,
        "hopeful": 6,
        "satisfied": 7,
        "positive": 8,
    }

    def __init__(self, db_path: str, seed: Optional[int] = 42):
        self.db_path = db_path
        self.random = random.Random(seed or random.randint(1, 10_000))
        self.seed_provider = PortfolioSeedProvider()
        # Initialize storage layers to ensure required SQLite schema exists
        self.transcript_store = TranscriptStore(db_path)
        self.analysis_store = AnalysisStore(db_path)

    # ------------------------------------------------------------------
    # Transcript generation
    # ------------------------------------------------------------------
    def generate_transcripts(self, days: int = 30, base_daily_calls: int = 12) -> List[Dict[str, Any]]:
        """Generate seeded transcripts with contextual metadata."""

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        current_date = start_date

        transcripts: List[Dict[str, Any]] = []
        customers = list(self.seed_provider.customers.values())

        while current_date <= end_date:
            weekday_multiplier = 1.0 if current_date.weekday() < 5 else 0.55
            month_end_multiplier = 1.25 if current_date.day > 25 else 1.0
            daily_calls = int(base_daily_calls * weekday_multiplier * month_end_multiplier * self.random.uniform(0.8, 1.2))

            for _ in range(daily_calls):
                topic = self.random.choice(self.TOPICS)
                customer = self.random.choice(customers)
                loan = self.seed_provider.get_loan(customer, topic=topic)
                property_profile = customer.property_profile
                advisor = self.seed_provider.get_advisor(topic=topic)

                timestamp = current_date.replace(
                    hour=self.random.randint(9, 16),
                    minute=self.random.randint(0, 59),
                    second=self.random.randint(0, 59),
                )

                conversation_context = self._build_conversation_context(topic, customer, loan)
                messages = self._generate_messages(
                    topic,
                    customer,
                    loan,
                    property_profile,
                    advisor,
                    timestamp,
                    conversation_context,
                )

                transcripts.append(
                    {
                        "id": f"CALL_{uuid.uuid4().hex[:8].upper()}",
                        "customer_id": customer.customer_id,
                        "advisor_id": advisor.advisor_id,
                        "loan_id": loan.loan_id,
                        "property_id": property_profile.property_id,
                        "timestamp": timestamp.isoformat() + "Z",
                        "topic": topic,
                        "duration": self.random.randint(210, 360),  # 3–6 minute conversations
                        "urgency": self.TOPIC_URGENCY.get(topic, "medium"),
                        "sentiment": self.random.choice(["positive", "neutral", "frustrated", "concerned"]),
                        "financial_impact": topic in {"mortgage_payment_issue", "hardship_assistance", "payoff_request"},
                        "compliance_flags": [],
                        "outcome": self.random.choice(["open", "follow_up_required", "resolved"]),
                        "messages": messages,
                        "context": conversation_context,
                    }
                )

            current_date += timedelta(days=1)

        return transcripts

    # ------------------------------------------------------------------
    # Analysis generation
    # ------------------------------------------------------------------
    def generate_analyses(self, transcripts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        analyses: List[Dict[str, Any]] = []

        for transcript in transcripts:
            topic = transcript["topic"]
            base_risk = 0.5 if topic in {"mortgage_payment_issue", "hardship_assistance"} else 0.2
            delinquency_risk = round(min(0.95, base_risk + self.random.uniform(0.1, 0.3)), 2)
            churn_risk = round(min(0.9, base_risk + self.random.uniform(0.05, 0.25)), 2)
            empathy_score = round(self.random.uniform(6.5, 9.4), 2)
            compliance_score = round(self.random.uniform(0.78, 0.98), 2)
            borrower_sentiment = self._build_sentiment_profile(transcript["sentiment"])

            analysis_id = f"ANALYSIS_{uuid.uuid4().hex[:8].upper()}"

            analysis_record = {
                    "analysis_id": analysis_id,
                    "transcript_id": transcript["id"],
                    "primary_intent": topic.replace("_", " ").title(),
                    "urgency_level": transcript["urgency"].upper(),
                    "borrower_sentiment": borrower_sentiment,
                    "delinquency_risk": delinquency_risk,
                    "churn_risk": churn_risk,
                    "complaint_risk": round(self.random.uniform(0.1, 0.6), 2),
                    "refinance_likelihood": round(self.random.uniform(0.2, 0.8), 2),
                    "empathy_score": empathy_score,
                    "compliance_adherence": compliance_score,
                    "solution_effectiveness": round(self.random.uniform(0.65, 0.95), 2),
                    "escalation_needed": churn_risk > 0.7 or delinquency_risk > 0.75,
                    "issue_resolved": transcript["outcome"] == "resolved",
                    "first_call_resolution": self.random.choice([True, False]),
                    "confidence_score": round(self.random.uniform(0.72, 0.94), 2),
                    "call_summary": self._build_analysis_summary(topic, transcript.get("context")),
                    "compliance_flags": [],
                    "required_disclosures": [],
                    "borrower_risks": {
                        "delinquency_risk": delinquency_risk,
                        "churn_risk": churn_risk,
                        "complaint_risk": round(self.random.uniform(0.15, 0.55), 2),
                        "refinance_likelihood": round(self.random.uniform(0.2, 0.85), 2),
                    },
                    "advisor_metrics": {
                        "empathy_score": empathy_score,
                        "compliance_adherence": compliance_score,
                        "solution_effectiveness": round(self.random.uniform(0.65, 0.96), 2),
                        "coaching_opportunities": [],
                    },
                    "recommendations": [
                        "Provide proactive follow-up within 2 business days",
                        "Reinforce payment options via customer portal",
                    ],
            }

            topic_insights = self._get_topic_insights(topic, transcript, borrower_sentiment)
            analysis_record.update(
                {
                    "topics_discussed": topic_insights.get("topics_discussed", []),
                    "payment_concerns": topic_insights.get("payment_concerns", []),
                    "property_related_issues": topic_insights.get("property_related_issues", []),
                    "product_opportunities": topic_insights.get("product_opportunities", []),
                    "required_disclosures": topic_insights.get("required_disclosures", []),
                }
            )
            analysis_record["compliance_flags"] = topic_insights.get("compliance_flags", [])
            analysis_record["advisor_metrics"]["coaching_opportunities"] = topic_insights.get(
                "coaching_opportunities", []
            )

            analyses.append(analysis_record)

        return analyses

    # ------------------------------------------------------------------
    # Database population
    # ------------------------------------------------------------------
    def populate_database(self, days: int = 60, base_daily_calls: int = 20) -> Dict[str, int]:
        import json
        import sqlite3

        transcripts = self.generate_transcripts(days, base_daily_calls)
        analyses = self.generate_analyses(transcripts)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for transcript in transcripts:
                cursor.execute(
                    '''
                    INSERT OR REPLACE INTO transcripts
                    (id, customer_id, advisor_id, timestamp, topic, duration, sentiment, urgency, compliance_flags, outcome)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        transcript["id"],
                        transcript["customer_id"],
                        transcript["advisor_id"],
                        transcript["timestamp"],
                        transcript["topic"],
                        transcript["duration"],
                        transcript["sentiment"],
                        transcript["urgency"],
                        json.dumps(transcript["compliance_flags"]),
                        transcript["outcome"],
                    ),
                )

                for message in transcript["messages"]:
                    cursor.execute(
                        '''
                        INSERT INTO messages (transcript_id, speaker, text, timestamp)
                        VALUES (?, ?, ?, ?)
                        ''',
                        (
                            transcript["id"],
                            message["speaker"],
                            message["text"],
                            message["timestamp"],
                        ),
                    )

            for analysis in analyses:
                cursor.execute(
                    '''
                    INSERT OR REPLACE INTO analysis
                    (id, transcript_id, analysis_data, primary_intent, urgency_level,
                     borrower_sentiment, delinquency_risk, churn_risk, complaint_risk,
                     refinance_likelihood, empathy_score, compliance_adherence,
                     solution_effectiveness, compliance_issues, escalation_needed,
                     issue_resolved, first_call_resolution, confidence_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        analysis["analysis_id"],
                        analysis["transcript_id"],
                        json.dumps(analysis),
                        analysis["primary_intent"],
                        analysis["urgency_level"],
                        analysis.get("borrower_sentiment", {}).get("overall", ""),
                        analysis["delinquency_risk"],
                        analysis["churn_risk"],
                        analysis["complaint_risk"],
                        analysis["refinance_likelihood"],
                        analysis["empathy_score"],
                        analysis["compliance_adherence"],
                        analysis["solution_effectiveness"],
                        len(analysis.get("compliance_flags", [])),
                        analysis["escalation_needed"],
                        analysis["issue_resolved"],
                        analysis["first_call_resolution"],
                        analysis["confidence_score"],
                        self._match_transcript_timestamp(transcripts, analysis["transcript_id"]),
                    ),
                )

            conn.commit()

            return {
                "transcripts_generated": len(transcripts),
                "analyses_generated": len(analyses),
                "days_of_data": days,
                "date_range": f"{transcripts[0]['timestamp'][:10]} to {transcripts[-1]['timestamp'][:10]}",
            }

        except Exception as exc:  # pragma: no cover - defensive logging
            conn.rollback()
            raise Exception(f"Database population failed: {exc}")

        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_conversation_context(self, topic: str, customer: CustomerProfile, loan: LoanProfile) -> str:
        if topic == "hardship_assistance":
            return (
                f"Customer {customer.name} is following up on hardship assistance for loan {loan.loan_id}. "
                "Previous arrangement is nearing its end and they are concerned about the next payment."
            )
        if topic == "mortgage_payment_issue":
            return (
                f"Customer {customer.name} reported a payment misapplied to loan {loan.loan_id}. "
                "They have already spoken with an advisor once and are awaiting resolution."
            )
        if topic == "escrow_inquiry":
            return (
                f"Customer {customer.name} is contesting an escrow increase tied to new tax assessments on property {loan.property_id}."
            )
        if topic == "complaint_resolution":
            return (
                f"Customer {customer.name} filed a formal complaint last week about inconsistent statements. "
                "This call is a scheduled follow-up."
            )
        return f"Customer {customer.name} is requesting assistance regarding {topic.replace('_', ' ')}."

    def _generate_messages(
        self,
        topic: str,
        customer: CustomerProfile,
        loan: LoanProfile,
        property_profile: PropertyProfile,
        advisor: AdvisorProfile,
        timestamp: datetime,
        conversation_context: str,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        current_time = timestamp

        def add_message(speaker: str, text: str, advance_seconds: Optional[int] = None) -> None:
            """Append message and move current time forward."""

            nonlocal current_time
            messages.append(
                {
                    "speaker": speaker,
                    "text": text,
                    "timestamp": current_time.isoformat() + "Z",
                }
            )

            increment = advance_seconds if advance_seconds is not None else self.random.randint(30, 65)
            current_time += timedelta(seconds=increment)

        add_message("Customer", f"Hi, this is {customer.name}. I need help regarding {topic.replace('_', ' ')}.")
        add_message("Advisor", f"Hello {customer.name}, this is {advisor.name} from {advisor.team}. I'm here to assist today.")

        for speaker, text in self._get_topic_dialogue(topic, customer, loan, property_profile, advisor):
            add_message(speaker, text)

        add_message(
            "Advisor",
            "I'll log detailed notes and flag the account so any teammate can see the history if you call back.",
        )
        add_message(
            "Customer",
            "Please send a recap to my email as well; it helps me keep everything organized.",
        )
        add_message(
            "Advisor",
            f"Absolutely. I'll send a secure message to {customer.email} once the documentation is updated.",
        )
        add_message(
            "Customer",
            "Great, I appreciate the thorough follow-up. Is there anything else you need from me?",
        )
        add_message(
            "Advisor",
            "That's everything for now. If anything changes, I'll call you immediately.",
        )

        messages.append(
            {
                "speaker": "System",
                "text": f"Context: {conversation_context}",
                "timestamp": current_time.isoformat() + "Z",
            }
        )

        return messages

    def _build_analysis_summary(self, topic: str, conversation_context: Optional[str]) -> str:
        base_summary = f"Summary of customer interaction regarding {topic.replace('_', ' ')}."
        if conversation_context:
            return f"{base_summary} Context note: {conversation_context}"
        return base_summary

    def _get_topic_dialogue(
        self,
        topic: str,
        customer: CustomerProfile,
        loan: LoanProfile,
        property_profile: PropertyProfile,
        advisor: AdvisorProfile,
    ) -> List[tuple[str, str]]:
        """Return an expanded dialogue tailored to the topic."""

        payment_amount = self._format_currency(loan.payment_amount)
        balance = self._format_currency(loan.balance)
        rate = self._format_rate(loan.interest_rate)
        escrow_amount = self._format_currency(loan.escrow_amount)

        property_address = property_profile.full_address
        due_day = loan.payment_due_day

        if topic == "mortgage_payment_issue":
            return [
                ("Customer", f"I submitted the {payment_amount} payment on the {due_day}th, but the portal still shows I'm past due."),
                ("Advisor", "I see that payment. It was held for manual verification because it differed from your typical amount."),
                ("Customer", "That explains the alert. How do we clear the delinquent notice before credit bureaus see it?"),
                ("Advisor", "I'll release the verification hold now and waive the late fee while the system catches up."),
                ("Customer", "Thank you. Can you confirm this doesn't impact my credit score?"),
                ("Advisor", "Yes. I'll add a servicing note that the payment was on time so your credit stays clean."),
                ("Customer", "Do I need to do anything else on my end today?"),
                ("Advisor", "Keep the confirmation email handy. If the alert reappears I'll escalate directly to our payment operations team."),
            ]

        if topic == "payment_inquiry":
            return [
                ("Customer", f"I want to confirm the {due_day} automatic draft pulled the full {payment_amount} yesterday."),
                ("Advisor", "It drafted successfully. The system flagged it for a quick review because escrow adjusted this cycle."),
                ("Customer", "So next month the amount will be different again?"),
                ("Advisor", f"Yes, it will include an escrow catch-up of {escrow_amount}. I'll email the detailed schedule."),
                ("Customer", "Perfect, I rely on those schedules for budgeting."),
                ("Advisor", "I'll also set a reminder to revisit this with you in six months to ensure the shortage is resolved."),
                ("Customer", "Thanks for being proactive. It saves me from future surprises."),
            ]

        if topic == "hardship_assistance":
            return [
                ("Customer", "I'm still on reduced hours at work and the forbearance plan expires after this payment."),
                ("Advisor", "I hear you. We can extend the plan 60 days while underwriting reviews a loan modification."),
                ("Customer", "What documentation should I gather so we don't lose time?"),
                ("Advisor", "Pay stubs for the past 30 days, your hardship letter, and any unemployment statements will help."),
                ("Customer", "I'll send those tonight. Will the payment stay at the reduced amount meanwhile?"),
                ("Advisor", "Yes. I'll lock that in and pause any automated collections calls."),
                ("Customer", "Thank you for treating this with urgency."),
                ("Advisor", "You're welcome. We'll schedule a check-in next Tuesday to confirm underwriting received everything."),
            ]

        if topic == "escrow_inquiry":
            return [
                ("Customer", f"My escrow payment jumped by {escrow_amount} because of new taxes on {property_address}."),
                ("Advisor", "The tax authority increased the assessment after a recent county audit."),
                ("Customer", "Can we spread the shortage over more months?"),
                ("Advisor", "Absolutely. We can re-spread it over twelve months to soften the impact."),
                ("Customer", "I appreciate that. Is there anything I can dispute on the tax bill?"),
                ("Advisor", "I'll attach the county appeal instructions to the email so you can file before the deadline."),
                ("Customer", "Great. Let me know if you need forms from me."),
                ("Advisor", "I'll note the file to follow up on the appeal status in thirty days."),
            ]

        if topic == "pmi_removal_request":
            return [
                ("Customer", "My loan-to-value is below 78%, so I'd like to remove PMI as fast as possible."),
                ("Advisor", "Based on your payments and the latest valuation, you do meet the threshold."),
                ("Customer", "Perfect. What inspection or appraisal fee should I expect?"),
                ("Advisor", "The drive-by appraisal runs about $135 and I'll waive our administrative charge."),
                ("Customer", "Thanks! Once that's complete, when will PMI actually drop?"),
                ("Advisor", "Typically within two billing cycles. I'll also request a manual review in case we can accelerate it."),
                ("Customer", "Could you send me the checklist so I don't miss signatures?"),
                ("Advisor", "I'll include the checklist and flag the workflow so underwriting knows it's high priority."),
            ]

        if topic == "refinance_inquiry":
            new_rate = max(0.5, loan.interest_rate - 0.75)
            return [
                ("Customer", "Rates are trending down and I'm curious whether a refinance makes sense."),
                ("Advisor", f"You're at {rate} on a balance of {balance}. A 15-year option today would land closer to {self._format_rate(new_rate)}."),
                ("Customer", "How would that change my monthly payment?"),
                ("Advisor", "Roughly speaking it would add about $180, but we'd shorten the term by ten years."),
                ("Customer", "That might still work if closing costs stay reasonable."),
                ("Advisor", "I'll prepare a no-obligation Loan Estimate and include a break-even analysis for you."),
                ("Customer", "Please also note that I'm considering cash-out for renovations."),
                ("Advisor", "Got it. I'll model a cash-out option with 80% loan-to-value so we keep mortgage insurance off the table."),
            ]

        if topic == "payoff_request":
            return [
                ("Customer", "I'm selling the property next month and need an accurate payoff quote."),
                ("Advisor", f"Today's good-through date will include per-diem interest and your outstanding balance of {balance}."),
                ("Customer", "Can you email that directly to my title company?"),
                ("Advisor", "Sure, just confirm their secure email and I'll send it within the hour."),
                ("Customer", "It's escrow@pinehillssettlement.com. They'll also want wiring instructions."),
                ("Advisor", "I'll include a payoff authorization form and the full wiring sheet so nothing is delayed."),
                ("Customer", "Thank you—closing is tight and every day counts."),
                ("Advisor", "I'll monitor the account daily and call if we need signatures on anything else."),
            ]

        if topic == "complaint_resolution":
            return [
                ("Customer", "I'm frustrated that no one followed up on my complaint from last week."),
                ("Advisor", "I apologize. I see the case was routed to a team that recently changed leads."),
                ("Customer", "I spent hours explaining the issue and had to repeat myself today."),
                ("Advisor", "I'm documenting every detail now and escalating it to the director of customer advocacy."),
                ("Customer", "Please make sure leadership knows this has already cost me time and money."),
                ("Advisor", "Absolutely. I'll request they respond to you within one business day and copy me on the email."),
                ("Customer", "Thank you. I just want consistent communication."),
                ("Advisor", "I'll personally call you tomorrow to confirm the action plan they provide."),
            ]

        # Generic support dialogue for other topics
        return [
            ("Customer", "I'm trying to make sure I'm following the right steps for this request."),
            ("Advisor", "Happy to walk you through it. I've reviewed your account notes and everything is up to date."),
            ("Customer", "I appreciate you checking. I'm juggling a lot right now."),
            ("Advisor", "No problem at all. I'll send a summary with every requirement spelled out."),
            ("Customer", "That's exactly what I need."),
        ]

    def _format_currency(self, amount: float) -> str:
        return f"${amount:,.2f}"

    def _format_rate(self, rate: float) -> str:
        return f"{rate:.2f}%"

    def _get_topic_insights(
        self,
        topic: str,
        transcript: Dict[str, Any],
        sentiment: Dict[str, str],
    ) -> Dict[str, Any]:
        """Derive topic-specific opportunities, concerns, and coaching tips."""

        topic_metadata: Dict[str, Dict[str, List[str]]] = {
            "mortgage_payment_issue": {
                "topics_discussed": [
                    "Payment processing",
                    "Delinquency alerts",
                    "Manual verification",
                ],
                "payment_concerns": [
                    "Potential credit reporting",
                    "Late fee reversal",
                ],
                "product_opportunities": [
                    "Enroll in autopay",
                    "Payment monitoring alerts",
                ],
                "coaching_opportunities": [
                    "Reinforce proactive credit monitoring scripts",
                ],
                "required_disclosures": [
                    "Payment posting timelines",
                    "Credit bureau reporting policy",
                ],
            },
            "payment_inquiry": {
                "topics_discussed": [
                    "Escrow adjustment",
                    "Automatic draft",
                    "Budget planning",
                ],
                "payment_concerns": [
                    "Escrow shortage",
                    "Draft amount changes",
                ],
                "product_opportunities": [
                    "Escrow analysis review",
                    "Budget planning consultation",
                ],
                "coaching_opportunities": [
                    "Explain escrow math proactively",
                ],
                "required_disclosures": [
                    "Escrow analysis statement",
                ],
            },
            "hardship_assistance": {
                "topics_discussed": [
                    "Income disruption",
                    "Forbearance extension",
                    "Loan modification path",
                ],
                "payment_concerns": [
                    "Reduced income",
                    "Modification eligibility",
                ],
                "product_opportunities": [
                    "Hardship assistance program",
                    "Financial counseling referral",
                ],
                "coaching_opportunities": [
                    "Confirm document checklist up front",
                ],
                "required_disclosures": [
                    "Hardship agreement terms",
                    "Potential credit impact",
                ],
            },
            "escrow_inquiry": {
                "topics_discussed": [
                    "Tax assessment increase",
                    "Escrow shortage",
                    "Appeal process",
                ],
                "payment_concerns": [
                    "Higher monthly payment",
                ],
                "product_opportunities": [
                    "Tax appeal assistance",
                    "Homeowner education webinar",
                ],
                "property_related_issues": [
                    "County tax reassessment",
                ],
                "coaching_opportunities": [
                    "Send appeal instructions proactively",
                ],
                "required_disclosures": [
                    "Escrow analysis statement",
                ],
            },
            "pmi_removal_request": {
                "topics_discussed": [
                    "Loan-to-value review",
                    "Appraisal scheduling",
                    "PMI waiver timeline",
                ],
                "product_opportunities": [
                    "Cross-sell appraisal service",
                    "Equity monitoring alerts",
                ],
                "property_related_issues": [
                    "Appraisal requirement",
                ],
                "coaching_opportunities": [
                    "Clarify PMI removal thresholds",
                ],
                "required_disclosures": [
                    "PMI cancellation policy",
                ],
            },
            "refinance_inquiry": {
                "topics_discussed": [
                    "Rate comparison",
                    "Term options",
                    "Closing costs",
                ],
                "product_opportunities": [
                    "Rate-lock consultation",
                    "Cash-out equity review",
                ],
                "payment_concerns": [
                    "Closing cost budget",
                ],
                "coaching_opportunities": [
                    "Surface break-even analysis early",
                ],
                "required_disclosures": [
                    "Loan Estimate",
                ],
            },
            "payoff_request": {
                "topics_discussed": [
                    "Payoff quote",
                    "Wiring instructions",
                    "Closing timeline",
                ],
                "product_opportunities": [
                    "Retention outreach",
                    "Post-sale servicing transfer",
                ],
                "property_related_issues": [
                    "Title company coordination",
                ],
                "coaching_opportunities": [
                    "Pre-empt title documentation questions",
                ],
                "required_disclosures": [
                    "Payoff statement terms",
                ],
            },
            "complaint_resolution": {
                "topics_discussed": [
                    "Case escalation",
                    "Service breakdown",
                    "Leadership follow-up",
                ],
                "payment_concerns": [],
                "product_opportunities": [
                    "Retention save offer",
                    "Service recovery outreach",
                ],
                "coaching_opportunities": [
                    "Close the loop with detailed recap",
                ],
                "required_disclosures": [
                    "Complaint acknowledgment timeline",
                ],
            },
        }

        metadata = topic_metadata.get(topic, {
            "topics_discussed": ["General account review"],
            "product_opportunities": ["Account follow-up"],
        })

        # Defensive copies so we do not mutate static lists
        def clone(key: str, default: Optional[List[str]] = None) -> List[str]:
            return list(metadata.get(key, default or []))

        compliance_flags = clone("compliance_flags") if "compliance_flags" in metadata else []
        if sentiment.get("overall", "").lower() in {"distressed", "frustrated"} and "Document empathy acknowledgement" not in compliance_flags:
            compliance_flags.append("Document empathy acknowledgement")

        return {
            "topics_discussed": clone("topics_discussed"),
            "payment_concerns": clone("payment_concerns"),
            "property_related_issues": clone("property_related_issues"),
            "product_opportunities": clone("product_opportunities"),
            "required_disclosures": clone("required_disclosures"),
            "coaching_opportunities": clone("coaching_opportunities"),
            "compliance_flags": compliance_flags,
        }

    def _build_sentiment_profile(self, sentiment: str) -> Dict[str, str]:
        """Create a structured borrower sentiment profile from transcript sentiment."""

        base_index = self.SENTIMENT_BASE_INDEX.get(sentiment.lower(), 4)

        if base_index <= 2:
            trend_weights = [0.5, 0.35, 0.15]
        elif base_index >= 6:
            trend_weights = [0.3, 0.45, 0.25]
        else:
            trend_weights = [0.4, 0.4, 0.2]

        trend = self.random.choices(["improving", "stable", "declining"], weights=trend_weights)[0]

        if trend == "improving":
            start_index = max(0, base_index - self.random.choice([1, 2]))
            end_index = min(len(self.SENTIMENT_SCALE) - 1, max(base_index, start_index + self.random.choice([1, 2])))
        elif trend == "declining":
            start_index = min(len(self.SENTIMENT_SCALE) - 1, max(base_index, base_index + self.random.choice([0, 1])))
            end_index = max(0, start_index - self.random.choice([1, 2]))
        else:
            start_index = base_index
            end_index = base_index

        overall_index = max(0, min(len(self.SENTIMENT_SCALE) - 1, round((start_index + end_index) / 2)))

        return {
            "overall": self.SENTIMENT_SCALE[overall_index],
            "start": self.SENTIMENT_SCALE[start_index],
            "end": self.SENTIMENT_SCALE[end_index],
            "trend": trend,
        }

    def _match_transcript_timestamp(self, transcripts: List[Dict[str, Any]], transcript_id: str) -> str:
        for transcript in transcripts:
            if transcript["id"] == transcript_id:
                return transcript["timestamp"]
        return datetime.utcnow().isoformat() + "Z"


def generate_synthetic_data(db_path: str, days: int = 60, base_daily_calls: int = 20) -> Dict[str, int]:
    generator = SyntheticDataGenerator(db_path)
    return generator.populate_database(days, base_daily_calls)
