"""Tests for the synthetic data generator used in demos and CLI tooling."""

from src.analytics.forecasting.synthetic_data_generator import SyntheticDataGenerator


def test_generate_transcripts_have_rich_dialogue():
    """Synthetic transcripts should include multi-turn conversations lasting several minutes."""

    generator = SyntheticDataGenerator(db_path=":memory:", seed=7)
    transcripts = generator.generate_transcripts(days=1, base_daily_calls=3)

    assert transcripts, "Expected synthetic transcripts to be generated"

    sample = transcripts[0]

    assert sample["duration"] >= 210  # roughly 3.5 minutes minimum
    assert len(sample["messages"]) >= 12
    assert sample["messages"][-1]["speaker"] == "System"


def test_generate_analyses_structured_sentiment():
    """Synthetic analyses should return structured borrower sentiment data."""

    generator = SyntheticDataGenerator(db_path=":memory:", seed=123)
    transcripts = generator.generate_transcripts(days=1, base_daily_calls=5)

    # Guard against unexpected empty output if random rounding drops to zero
    assert transcripts, "Expected synthetic transcripts to be generated"

    analyses = generator.generate_analyses(transcripts)

    assert len(analyses) == len(transcripts)

    sample = analyses[0]
    sentiment = sample["borrower_sentiment"]

    assert isinstance(sentiment, dict)
    assert {"overall", "start", "end", "trend"}.issubset(sentiment.keys())
    assert sentiment["trend"] in {"improving", "declining", "stable"}
    assert isinstance(sentiment["overall"], str) and sentiment["overall"].strip()

    assert sample.get("topics_discussed"), "Expected topics_discussed to be populated"
    assert sample.get("product_opportunities"), "Expected product_opportunities to be populated"
