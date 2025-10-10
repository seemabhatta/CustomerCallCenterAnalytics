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

from src.data.portfolio_seed import PortfolioSeedProvider, AdvisorProfile, CustomerProfile, LoanProfile, PropertyProfile


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

    def __init__(self, db_path: str, seed: Optional[int] = 42):
        self.db_path = db_path
        self.random = random.Random(seed or random.randint(1, 10_000))
        self.seed_provider = PortfolioSeedProvider()

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
                        "duration": self.random.randint(360, 960),
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

            analysis_id = f"ANALYSIS_{uuid.uuid4().hex[:8].upper()}"

            analyses.append(
                {
                    "analysis_id": analysis_id,
                    "transcript_id": transcript["id"],
                    "primary_intent": topic.replace("_", " ").title(),
                    "urgency_level": transcript["urgency"].upper(),
                    "borrower_sentiment": transcript["sentiment"].capitalize(),
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
                    },
                    "recommendations": [
                        "Provide proactive follow-up within 2 business days",
                        "Reinforce payment options via customer portal",
                    ],
                }
            )

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
                        analysis["borrower_sentiment"],
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

        def add_message(speaker: str, text: str) -> None:
            nonlocal current_time
            messages.append(
                {
                    "speaker": speaker,
                    "text": text,
                    "timestamp": current_time.isoformat() + "Z",
                }
            )
            current_time += timedelta(seconds=self.random.randint(15, 75))

        add_message("Customer", f"Hi, this is {customer.name}. I need help regarding {topic.replace('_', ' ')}.")
        add_message("Advisor", f"Hello {customer.name}, this is {advisor.name} from {advisor.team}. I'm here to assist.")

        if topic in {"mortgage_payment_issue", "payment_inquiry"}:
            add_message("Customer", f"Loan {loan.loan_id} shows a payment due on the {loan.payment_due_day}th, but I already paid yesterday.")
            add_message("Advisor", "Let me review the payment history... I see the payment posted but was flagged for verification.")
        elif topic == "hardship_assistance":
            add_message("Customer", "I'm still recovering financially and worried about the next payment.")
            add_message("Advisor", "We can extend the hardship plan by 60 days while we reassess your income documentation.")
        elif topic == "escrow_inquiry":
            add_message("Customer", f"My escrow went up $150 because of new taxes on {property_profile.full_address}.")
            add_message("Advisor", "I can see that. We received the updated tax bill yesterday; let's explore spreading the shortage over 12 months.")
        elif topic == "pmi_removal_request":
            add_message("Customer", "I'm hoping to remove PMI now that my loan-to-value is below 78%.")
            add_message("Advisor", "I'll order an updated valuation and send the paperwork for your signature.")
        elif topic == "refinance_inquiry":
            add_message("Customer", "Rates dropped and I want to see if refinancing makes sense.")
            add_message("Advisor", "We can run a scenario—your current balance is ${loan.balance:,.0f} at {loan.interest_rate}% and we have a 15-year option available.")
        elif topic == "payoff_request":
            add_message("Customer", "Please prepare a payoff quote for my loan; I'm planning to close next month.")
            add_message("Advisor", "I'll generate a payoff valid for 30 days and email it to you today.")
        elif topic == "complaint_resolution":
            add_message("Customer", "I'm disappointed with how my previous inquiry was handled.")
            add_message("Advisor", "I understand and I'm escalating this to our resolution desk with priority status.")

        add_message("Customer", "Is there anything else I should do right now?")
        add_message("Advisor", "I'll document the case and send a summary with next steps within 24 hours.")
        add_message("Customer", "Thank you for the help today.")
        add_message("Advisor", "You're welcome. Please reach out if anything changes.")

        # Add context summary as final message metadata (not spoken)
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

    def _match_transcript_timestamp(self, transcripts: List[Dict[str, Any]], transcript_id: str) -> str:
        for transcript in transcripts:
            if transcript["id"] == transcript_id:
                return transcript["timestamp"]
        return datetime.utcnow().isoformat() + "Z"


def generate_synthetic_data(db_path: str, days: int = 60, base_daily_calls: int = 20) -> Dict[str, int]:
    generator = SyntheticDataGenerator(db_path)
    return generator.populate_database(days, base_daily_calls)
