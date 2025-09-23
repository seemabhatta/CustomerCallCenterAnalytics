"""
Transcript Service - Business logic for transcript operations
Clean separation from routing layer
"""
from typing import List, Optional, Dict, Any
from ..storage.transcript_store import TranscriptStore
from ..call_center_agents.transcript_agent import TranscriptAgent


class TranscriptService:
    """Service for transcript operations - contains ALL business logic."""
    
    def __init__(self, api_key: str, db_path: str = "data/call_center.db"):
        self.api_key = api_key
        self.db_path = db_path
        self.store = TranscriptStore(db_path)
        self.generator = TranscriptAgent()
    
    async def list_all(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """List all transcripts with optional limit and metadata."""
        transcripts = self.store.get_all()
        total_available = len(transcripts)

        if limit:
            transcripts = transcripts[:limit]

        return {
            "transcripts": [t.to_dict() for t in transcripts],
            "metadata": {
                "requested": limit if limit is not None else total_available,
                "returned": len(transcripts),
                "total_available": total_available,
                "completeness": "complete" if len(transcripts) == total_available else "partial"
            }
        }
    
    async def create(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new transcript."""
        # Extract parameters - support both topic and legacy scenario
        topic = request_data.get("topic") or request_data.get("scenario", "payment_inquiry")
        urgency = request_data.get("urgency", "medium")
        financial_impact = request_data.get("financial_impact", False)
        customer_sentiment = request_data.get("customer_sentiment", "neutral")
        customer_id = request_data.get("customer_id", "CUST_001")
        
        # Generate transcript
        transcript = self.generator.generate(
            topic=topic,
            urgency=urgency,
            financial_impact=financial_impact,
            customer_sentiment=customer_sentiment,
            customer_id=customer_id
        )
        
        # Store if requested
        should_store = request_data.get("store", True)
        if should_store:
            self.store.store(transcript)

            # Store transcript in knowledge graph for two-layer memory architecture
            try:
                from ..storage.queued_graph_store import add_customer_sync, add_transcript_sync

                # Add customer first (idempotent operation)
                add_customer_sync(transcript.customer_id)

                # Add transcript node
                success = add_transcript_sync(
                    transcript_id=transcript.id,
                    topic=topic,
                    message_count=len(transcript.messages)
                )

                print(f"📊 Transcript stored in knowledge graph: {success}")

            except Exception as e:
                # Log but don't fail - graph storage is supplementary
                print(f"⚠️  Failed to store transcript in knowledge graph: {str(e)}")

        return transcript.to_dict()
    
    async def get_by_id(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript by ID."""
        transcript = self.store.get_by_id(transcript_id)
        if not transcript:
            return None
        return transcript.to_dict()
    
    async def delete(self, transcript_id: str) -> bool:
        """Delete transcript by ID."""
        return self.store.delete(transcript_id)
    
    async def search(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search transcripts with various parameters."""
        customer = search_params.get("customer")
        topic = search_params.get("topic")
        text = search_params.get("text")
        
        if customer:
            results = self.store.search_by_customer(customer)
        elif topic:
            results = self.store.search_by_topic(topic)
        elif text:
            results = self.store.search_by_text(text)
        else:
            raise ValueError("Must specify customer, topic, or text parameter")
        
        return [t.to_dict() for t in results]
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get transcript statistics and metrics."""
        transcripts = self.store.get_all()
        
        if not transcripts:
            return {
                "total_transcripts": 0,
                "total_messages": 0,
                "unique_customers": 0,
                "avg_messages_per_transcript": 0.0,
                "top_topics": {},
                "sentiments": {},
                "speakers": {}
            }
        
        total = len(transcripts)
        total_messages = sum(len(t.messages) for t in transcripts)
        
        # Collect statistics
        customers = set()
        topics = {}
        sentiments = {}
        speakers = {}
        
        for transcript in transcripts:
            # Customer IDs
            if hasattr(transcript, 'customer_id'):
                customers.add(transcript.customer_id)
            
            # Topics/scenarios
            topic = getattr(transcript, 'topic', getattr(transcript, 'scenario', 'Unknown'))
            topics[topic] = topics.get(topic, 0) + 1
            
            # Sentiments
            sentiment = getattr(transcript, 'sentiment', 'Unknown')
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            # Speakers
            for msg in transcript.messages:
                speakers[msg.speaker] = speakers.get(msg.speaker, 0) + 1
        
        return {
            "total_transcripts": total,
            "total_messages": total_messages,
            "unique_customers": len(customers),
            "avg_messages_per_transcript": total_messages/total,
            "top_topics": dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]),
            "sentiments": sentiments,
            "speakers": dict(sorted(speakers.items(), key=lambda x: x[1], reverse=True)[:10])
        }