"""
Test cases for CLI topic functionality following TDD principles.
Tests written FIRST to ensure they fail, then implementation will make them pass.
"""

import pytest
import subprocess
import re
import os
from pathlib import Path


def run_cli(args, timeout=60):
    """Helper to run CLI commands with proper environment."""
    cmd = ['python', 'cli.py'] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=Path(__file__).parent.parent,  # Run from project root
        env={**os.environ, 'PYTHONPATH': str(Path(__file__).parent.parent)}
    )
    return result


class TestCLITopicFunctionality:
    """TDD tests for CLI topic functionality following NO FALLBACK principle."""
    
    def test_generate_with_topic_flag_exists(self):
        """
        TEST: CLI generate command should have --topic flag.
        This test will FAIL initially since we still have --scenario flag.
        """
        result = run_cli(['generate', '--help'])
        
        assert result.returncode == 0, f"Help command failed: {result.stderr}"
        
        # Should have --topic flag (will fail initially)
        assert '--topic' in result.stdout, \
            "CLI generate command missing --topic flag"
        
        # Should NOT have --scenario flag after fix
        assert '--scenario' not in result.stdout, \
            "CLI still has old --scenario flag - should be removed"
    
    def test_generate_with_topic_stores_topic_field(self):
        """
        TEST: Generate with --topic should store topic in database.
        This will FAIL initially since --topic flag doesn't exist yet.
        """
        test_topic = "PMI Removal Test"
        
        # Generate with --topic flag (will fail since flag doesn't exist)
        result = run_cli(['generate', '--topic', test_topic, '--store'])
        
        assert result.returncode == 0, \
            f"Generate with --topic failed: {result.stderr}"
        
        # Should show the topic in output
        assert test_topic in result.stdout or 'CALL_' in result.stdout, \
            f"Topic not reflected in generate output: {result.stdout}"
        
        # Verify topic is actually stored by listing
        list_result = run_cli(['list', '--limit', '1'])
        assert list_result.returncode == 0, "List command failed"
        
        # Topic should appear in list (not blank)
        assert test_topic in list_result.stdout, \
            f"Topic '{test_topic}' not shown in list output: {list_result.stdout}"
    
    def test_list_displays_topic_correctly_no_fallback(self):
        """
        TEST: List command should display topic field without fallback.
        Following NO FALLBACK principle - should fail fast if topic missing.
        """
        # First generate a transcript with topic
        test_topic = "Account Balance Inquiry"
        gen_result = run_cli(['generate', '--topic', test_topic, '--store'])
        
        assert gen_result.returncode == 0, "Generate failed"
        
        # List should show the topic
        list_result = run_cli(['list', '--limit', '1'])
        assert list_result.returncode == 0, "List failed"
        
        # Should show actual topic, NOT 'N/A' or blank
        assert test_topic in list_result.stdout, \
            f"Topic '{test_topic}' missing from list"
        
        # Should NOT show fallback indicators (violates NO FALLBACK)
        assert 'N/A' not in list_result.stdout, \
            "Shows 'N/A' fallback - violates NO FALLBACK principle"
        
        # Topic column should not be blank
        lines = list_result.stdout.split('\n')
        topic_line = next((line for line in lines if 'CALL_' in line), None)
        assert topic_line, "No transcript line found in list output"
        
        # Parse the line to check topic column is not empty
        parts = topic_line.split()
        assert len(parts) >= 3, "Insufficient columns in list output"
        topic_column = parts[2] if len(parts) > 2 else ""
        assert topic_column and topic_column != "", \
            "Topic column is blank in list output"
    
    def test_no_fallback_behavior_when_topic_missing(self):
        """
        TEST: System should fail fast when topic is corrupted/missing.
        NO FALLBACK principle: Never show graceful degradation.
        
        This test verifies that if topic data is corrupted,
        the system fails fast instead of showing 'N/A' or blank.
        """
        # This test will fail initially if fallback logic exists
        # We'll implement this after removing fallback logic
        
        # Generate transcript first
        result = run_cli(['generate', '--topic', 'Test Topic', '--store'])
        assert result.returncode == 0, "Generate failed"
        
        # If we had a way to corrupt the topic field in database,
        # the list command should fail fast instead of showing fallback
        # For now, we'll test that the system doesn't use fallback text
        
        list_result = run_cli(['list'])
        assert list_result.returncode == 0, "List command failed"
        
        # Should never contain fallback text (violates NO FALLBACK)
        fallback_indicators = ['N/A', 'Unknown', 'Missing', 'Default']
        for indicator in fallback_indicators:
            assert indicator not in list_result.stdout, \
                f"Found fallback indicator '{indicator}' - violates NO FALLBACK principle"
    
    def test_topic_flag_compatibility_with_other_flags(self):
        """
        TEST: --topic flag should work with other flags like --store, --show.
        This ensures complete functionality after the change.
        """
        test_topic = "Refinance Inquiry"
        
        # Test --topic with --store and --show
        result = run_cli(['generate', '--topic', test_topic, '--store', '--show'])
        
        assert result.returncode == 0, \
            f"Generate with multiple flags failed: {result.stderr}"
        
        # Should show topic in output
        assert test_topic in result.stdout, \
            "Topic not shown with --show flag"
        
        # Should confirm storage
        storage_indicators = ['Stored', 'stored', 'database']
        has_storage = any(indicator in result.stdout for indicator in storage_indicators)
        assert has_storage, "Missing storage confirmation"
    
    def test_scenario_flag_removed_completely(self):
        """
        TEST: Old --scenario flag should be completely removed.
        This ensures clean transition without confusion.
        """
        # Try using old --scenario flag - should fail
        result = run_cli(['generate', '--scenario', 'Test'])
        
        # Should fail with unrecognized option error
        assert result.returncode != 0, \
            "Old --scenario flag still works - should be removed"
        
        # Error should mention unrecognized option
        error_indicators = ['unrecognized', 'no such option', 'invalid']
        has_error = any(indicator in result.stderr.lower() for indicator in error_indicators)
        assert has_error, \
            f"Should show unrecognized option error for --scenario: {result.stderr}"


# Integration test to verify topic field in database
class TestTopicFieldIntegration:
    """Integration tests to verify topic field is properly stored and retrieved."""
    
    def test_topic_end_to_end_workflow(self):
        """
        INTEGRATION TEST: Complete workflow with topic field.
        Generate -> Store -> List -> Verify topic appears correctly.
        """
        test_topic = "End-to-End Test Topic"
        
        # Step 1: Generate with --topic
        gen_result = run_cli(['generate', '--topic', test_topic, '--store'])
        assert gen_result.returncode == 0, "Generate step failed"
        
        # Extract transcript ID from output
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID in generate output"
        transcript_id = transcript_id_match.group()
        
        # Step 2: List and verify topic appears
        list_result = run_cli(['list', '--limit', '5'])
        assert list_result.returncode == 0, "List step failed"
        assert test_topic in list_result.stdout, \
            f"Topic missing from list: {list_result.stdout}"
        
        # Step 3: Get specific transcript and verify topic
        get_result = run_cli(['get', transcript_id])
        assert get_result.returncode == 0, "Get step failed"
        
        # Should contain topic information
        assert test_topic in get_result.stdout, \
            f"Topic missing from get command: {get_result.stdout}"
        
        # Step 4: Search by topic should work
        search_result = run_cli(['search', '--topic', test_topic])
        assert search_result.returncode == 0, "Search by topic failed"
        assert transcript_id in search_result.stdout, \
            "Search didn't find the transcript by topic"


# Edge cases and error conditions
class TestTopicFieldEdgeCases:
    """Test edge cases for topic field following NO FALLBACK principle."""
    
    def test_empty_topic_fails_fast(self):
        """
        TEST: Empty topic should fail fast, not store blank.
        NO FALLBACK principle: Don't accept empty/invalid data gracefully.
        """
        # Try to generate with empty topic
        result = run_cli(['generate', '--topic', '', '--store'])
        
        # Should either:
        # 1. Fail with error (preferred - fail fast)
        # 2. Or require non-empty topic
        
        if result.returncode != 0:
            # Failed fast - good!
            assert 'topic' in result.stderr.lower() or 'empty' in result.stderr.lower(), \
                "Should mention topic/empty in error message"
        else:
            # If it succeeded, topic should not be empty in list
            list_result = run_cli(['list', '--limit', '1'])
            assert list_result.returncode == 0, "List failed"
            
            # Should not show blank topic column
            lines = list_result.stdout.split('\n')
            data_lines = [line for line in lines if 'CALL_' in line]
            if data_lines:
                # Topic column should not be empty
                parts = data_lines[0].split()
                topic_col = parts[2] if len(parts) > 2 else ""
                assert topic_col != "", "Empty topic stored - should fail fast"