"""Synthetic data generator for forecasting demos.

Generates realistic call center data with seasonal patterns
when real historical data is insufficient.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid


class SyntheticDataGenerator:
    """Generate synthetic call center data with realistic patterns."""

    def __init__(self, db_path: str):
        """Initialize generator.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    def generate_transcripts(self, days: int = 60, base_daily_calls: int = 20) -> List[Dict[str, Any]]:
        """Generate synthetic transcripts with seasonal patterns.

        Args:
            days: Number of days of data to generate
            base_daily_calls: Base number of calls per day

        Returns:
            List of synthetic transcript data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        transcripts = []
        current_date = start_date

        topics = [
            'refinance_inquiry',
            'hardship_assistance',
            'mortgage_payment_issue',
            'payment_inquiry',
            'payoff_request',
            'escrow_inquiry',
            'pmi_removal_request'
        ]

        while current_date <= end_date:
            # Weekday effect: more calls on weekdays
            weekday_multiplier = 1.0 if current_date.weekday() < 5 else 0.6

            # Monthly pattern: more calls at month end
            day_of_month = current_date.day
            month_end_multiplier = 1.3 if day_of_month > 25 else 1.0

            # Calculate calls for this day
            daily_calls = int(base_daily_calls * weekday_multiplier * month_end_multiplier * random.uniform(0.8, 1.2))

            for i in range(daily_calls):
                # Distribute throughout business hours (9 AM - 5 PM)
                hour = random.randint(9, 16)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)

                timestamp = current_date.replace(hour=hour, minute=minute, second=second)

                # Generate transcript
                transcript_id = str(uuid.uuid4())
                topic = random.choice(topics)

                transcript = {
                    'id': transcript_id,
                    'customer_id': f'CUST{random.randint(1000, 9999)}',
                    'advisor_id': f'ADV{random.randint(100, 999)}',
                    'timestamp': timestamp.isoformat() + 'Z',
                    'topic': topic,
                    'duration': random.randint(180, 1200),  # 3-20 minutes
                    'messages': self._generate_messages(topic)
                }

                transcripts.append(transcript)

            current_date += timedelta(days=1)

        return transcripts

    def generate_analyses(self, transcripts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate synthetic analyses for transcripts.

        Args:
            transcripts: List of transcript data

        Returns:
            List of synthetic analysis data
        """
        analyses = []

        intent_map = {
            'refinance_inquiry': 'Refinancing inquiry',
            'hardship_assistance': 'Hardship assistance due to financial difficulties',
            'mortgage_payment_issue': 'Mortgage payment issue resolution',
            'payment_inquiry': 'Payment status inquiry',
            'payoff_request': 'Requesting payoff statement',
            'escrow_inquiry': 'Escrow account inquiry',
            'pmi_removal_request': 'PMI removal request'
        }

        sentiments = ['Positive', 'Neutral', 'Frustrated', 'Satisfied']

        for transcript in transcripts:
            analysis_id = str(uuid.uuid4())
            topic = transcript['topic']

            # Generate realistic risk scores based on topic
            if topic == 'hardship_assistance':
                delinquency_risk = random.uniform(0.6, 0.95)
                churn_risk = random.uniform(0.5, 0.9)
            elif topic == 'mortgage_payment_issue':
                delinquency_risk = random.uniform(0.4, 0.8)
                churn_risk = random.uniform(0.3, 0.7)
            else:
                delinquency_risk = random.uniform(0.1, 0.5)
                churn_risk = random.uniform(0.1, 0.4)

            # Generate advisor metrics
            empathy_score = random.uniform(6.0, 9.5)
            compliance_score = random.uniform(0.7, 1.0)

            analysis = {
                'analysis_id': analysis_id,
                'transcript_id': transcript['id'],
                'primary_intent': intent_map.get(topic, topic),
                'urgency_level': random.choice(['LOW', 'MEDIUM', 'HIGH']),
                'borrower_sentiment': random.choice(sentiments),
                'delinquency_risk': delinquency_risk,
                'churn_risk': churn_risk,
                'complaint_risk': random.uniform(0.1, 0.6),
                'refinance_likelihood': random.uniform(0.2, 0.8),
                'empathy_score': empathy_score,
                'compliance_adherence': compliance_score,
                'solution_effectiveness': random.uniform(0.6, 0.95),
                'escalation_needed': random.choice([True, False]),
                'issue_resolved': random.choice([True, True, False]),  # 2/3 resolved
                'first_call_resolution': random.choice([True, False]),
                'confidence_score': random.uniform(0.7, 0.95),
                'call_summary': f"Customer called regarding {topic.replace('_', ' ')}",
                'compliance_flags': [],
                'borrower_risks': {
                    'delinquency_risk': delinquency_risk,
                    'churn_risk': churn_risk,
                    'complaint_risk': random.uniform(0.1, 0.6),
                    'refinance_likelihood': random.uniform(0.2, 0.8)
                },
                'advisor_metrics': {
                    'empathy_score': empathy_score,
                    'compliance_adherence': compliance_score,
                    'solution_effectiveness': random.uniform(0.6, 0.95)
                }
            }

            analyses.append(analysis)

        return analyses

    def populate_database(self, days: int = 60, base_daily_calls: int = 20) -> Dict[str, int]:
        """Generate and populate database with synthetic data.

        Args:
            days: Number of days of data
            base_daily_calls: Base calls per day

        Returns:
            Summary of generated data
        """
        import sqlite3
        import json

        # Generate data
        transcripts = self.generate_transcripts(days, base_daily_calls)
        analyses = self.generate_analyses(transcripts)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert transcripts
            for t in transcripts:
                cursor.execute('''
                    INSERT OR REPLACE INTO transcripts
                    (id, customer_id, advisor_id, timestamp, topic, duration)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (t['id'], t['customer_id'], t['advisor_id'],
                     t['timestamp'], t['topic'], t['duration']))

                # Insert messages
                for msg in t['messages']:
                    cursor.execute('''
                        INSERT INTO messages (transcript_id, speaker, text, timestamp)
                        VALUES (?, ?, ?, ?)
                    ''', (t['id'], msg['speaker'], msg['text'],
                         t['timestamp']))

            # Insert analyses with matching timestamps
            for a in analyses:
                # Find matching transcript timestamp
                transcript = next(t for t in transcripts if t['id'] == a['transcript_id'])

                cursor.execute('''
                    INSERT OR REPLACE INTO analysis
                    (id, transcript_id, analysis_data, primary_intent, urgency_level,
                     borrower_sentiment, delinquency_risk, churn_risk, complaint_risk,
                     refinance_likelihood, empathy_score, compliance_adherence,
                     solution_effectiveness, compliance_issues, escalation_needed,
                     issue_resolved, first_call_resolution, confidence_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    a['analysis_id'],
                    a['transcript_id'],
                    json.dumps(a),  # Proper JSON serialization
                    a['primary_intent'],
                    a['urgency_level'],
                    a['borrower_sentiment'],
                    a['delinquency_risk'],
                    a['churn_risk'],
                    a['complaint_risk'],
                    a['refinance_likelihood'],
                    a['empathy_score'],
                    a['compliance_adherence'],
                    a['solution_effectiveness'],
                    len(a['compliance_flags']),
                    a['escalation_needed'],
                    a['issue_resolved'],
                    a['first_call_resolution'],
                    a['confidence_score'],
                    transcript['timestamp']  # Match transcript timestamp
                ))

            conn.commit()

            return {
                'transcripts_generated': len(transcripts),
                'analyses_generated': len(analyses),
                'days_of_data': days,
                'date_range': f"{transcripts[0]['timestamp'][:10]} to {transcripts[-1]['timestamp'][:10]}"
            }

        except Exception as e:
            conn.rollback()
            raise Exception(f"Database population failed: {str(e)}")

        finally:
            conn.close()

    def _generate_messages(self, topic: str) -> List[Dict[str, str]]:
        """Generate realistic message exchange for topic.

        Args:
            topic: Topic of conversation

        Returns:
            List of messages
        """
        templates = {
            'refinance_inquiry': [
                {'speaker': 'Customer', 'text': 'Hi, I would like to inquire about refinancing my mortgage.'},
                {'speaker': 'Advisor', 'text': 'I would be happy to help you with that. Can you provide your loan number?'},
                {'speaker': 'Customer', 'text': 'Sure, it is 12345678.'},
                {'speaker': 'Advisor', 'text': 'Thank you. Let me pull up your account.'}
            ],
            'hardship_assistance': [
                {'speaker': 'Customer', 'text': 'I am having trouble making my mortgage payments.'},
                {'speaker': 'Advisor', 'text': 'I understand, and I am here to help. Let us discuss your options.'},
                {'speaker': 'Customer', 'text': 'I recently lost my job and need assistance.'},
                {'speaker': 'Advisor', 'text': 'We have several hardship programs available that might help.'}
            ]
        }

        return templates.get(topic, [
            {'speaker': 'Customer', 'text': f'I need help with my {topic.replace("_", " ")}.'},
            {'speaker': 'Advisor', 'text': 'I will be glad to assist you with that.'}
        ])


def generate_synthetic_data(db_path: str, days: int = 60, base_daily_calls: int = 20) -> Dict[str, int]:
    """Convenience function to generate synthetic data.

    Args:
        db_path: Path to database
        days: Number of days
        base_daily_calls: Calls per day

    Returns:
        Generation summary
    """
    generator = SyntheticDataGenerator(db_path)
    return generator.populate_database(days, base_daily_calls)
