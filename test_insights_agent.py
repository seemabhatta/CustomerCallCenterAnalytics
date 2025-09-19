#!/usr/bin/env python3
"""
Quick test script for the Leadership Insights Agent
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.infrastructure.llm.llm_client_v2 import LLMClientV2, OpenAIProvider
from src.agents.leadership_insights_agent import LeadershipInsightsAgent


async def test_insights_agent():
    """Test the Leadership Insights Agent with a sample query."""

    print("🧪 Testing Leadership Insights Agent")
    print("=" * 50)

    try:
        # Initialize LLM client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return

        provider = OpenAIProvider(api_key=api_key)
        llm_client = LLMClientV2(provider=provider)

        # Initialize the agent
        agent = LeadershipInsightsAgent(llm_client)

        # Test query
        test_query = "What are our top compliance risks this week?"
        executive_role = "CCO"

        print(f"🎯 Query: {test_query}")
        print(f"👤 Role: {executive_role}")
        print()

        # Process the query
        response = await agent.process_query(
            query=test_query,
            executive_role=executive_role
        )

        print("📋 RESPONSE:")
        print("-" * 30)
        print(response.get('content', 'No content generated'))
        print()

        print("📊 METADATA:")
        print("-" * 30)
        metadata = response.get('metadata', {})
        print(f"Processing time: {metadata.get('total_processing_time_ms', 0)}ms")
        print(f"Confidence: {metadata.get('overall_confidence', 0)}%")
        print(f"Steps: {len(metadata.get('processing_steps', []))}")
        print()

        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_insights_agent())