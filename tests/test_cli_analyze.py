"""
Test cases for CLI analyze functionality following TDD principles.
Tests written FIRST to ensure they fail, then implementation will make them pass.
Enforces NO FALLBACK principle - system must show real data or fail fast.
"""

import pytest
import subprocess
import re
import os
from pathlib import Path


def run_cli(args, timeout=120, input_text=None):
    """Helper to run CLI commands with proper environment."""
    cmd = ['python', 'cli.py'] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        input=input_text,
        cwd=Path(__file__).parent.parent,  # Run from project root
        env={**os.environ, 'PYTHONPATH': str(Path(__file__).parent.parent)}
    )
    return result


class TestCLIAnalyzeFunctionality:
    """TDD tests for analyze command following NO FALLBACK principle."""
    
    def test_analyze_shows_real_intent_not_unknown(self):
        """
        CRITICAL TEST: Analyze must show real intent, never 'Unknown'.
        NO FALLBACK principle - system should show actual data or fail fast.
        """
        # Generate a transcript to analyze
        gen_result = run_cli(['generate', '--topic', 'Analyze Intent Test', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        # Extract transcript ID
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID in generate output"
        transcript_id = transcript_id_match.group()
        
        # Analyze transcript
        analyze_result = run_cli(['analyze', '-t', transcript_id])
        assert analyze_result.returncode == 0, \
            f"Analyze failed: {analyze_result.stderr}"
        
        # Should NOT show 'Unknown' for intent (violates NO FALLBACK)
        assert 'Intent: Unknown' not in analyze_result.stdout, \
            "VIOLATION: Shows 'Unknown' intent - violates NO FALLBACK principle"
        
        # Should show actual intent data
        assert 'Intent:' in analyze_result.stdout, "Missing intent field"
        
        # Should contain meaningful intent text (not empty or fallback)
        intent_line = None
        for line in analyze_result.stdout.split('\n'):
            if 'Intent:' in line:
                intent_line = line
                break
        
        assert intent_line, "No Intent line found"
        intent_value = intent_line.split('Intent:', 1)[1].strip()
        assert intent_value != 'Unknown', "Intent shows 'Unknown' fallback"
        assert intent_value != '', "Intent is empty"
        assert len(intent_value) > 3, f"Intent too short: '{intent_value}'"
    
    def test_analyze_shows_real_sentiment_not_unknown(self):
        """
        TEST: Analyze must show real sentiment, never 'Unknown'.
        """
        # Generate transcript
        gen_result = run_cli(['generate', '--topic', 'Sentiment Analysis Test', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        # Analyze
        analyze_result = run_cli(['analyze', '-t', transcript_id])
        assert analyze_result.returncode == 0, \
            f"Analyze failed: {analyze_result.stderr}"
        
        # Should NOT show 'Unknown' for sentiment
        assert 'Sentiment: Unknown' not in analyze_result.stdout, \
            "VIOLATION: Shows 'Unknown' sentiment - violates NO FALLBACK principle"
        
        # Should show actual sentiment
        assert 'Sentiment:' in analyze_result.stdout, "Missing sentiment field"
        
        sentiment_line = None
        for line in analyze_result.stdout.split('\n'):
            if 'Sentiment:' in line:
                sentiment_line = line
                break
        
        assert sentiment_line, "No Sentiment line found"
        sentiment_value = sentiment_line.split('Sentiment:', 1)[1].strip()
        assert sentiment_value != 'Unknown', "Sentiment shows 'Unknown' fallback"
        assert sentiment_value != '', "Sentiment is empty"
    
    def test_analyze_shows_real_confidence_not_zero(self):
        """
        TEST: Analyze must show real confidence score, not 0.00%.
        """
        # Generate transcript
        gen_result = run_cli(['generate', '--topic', 'Confidence Test', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        # Analyze
        analyze_result = run_cli(['analyze', '-t', transcript_id])
        assert analyze_result.returncode == 0, \
            f"Analyze failed: {analyze_result.stderr}"
        
        # Should NOT show 0.00% confidence
        assert 'Confidence: 0.00%' not in analyze_result.stdout, \
            "VIOLATION: Shows 0.00% confidence - likely fallback value"
        
        # Should show meaningful confidence
        assert 'Confidence:' in analyze_result.stdout, "Missing confidence field"
        
        confidence_line = None
        for line in analyze_result.stdout.split('\n'):
            if 'Confidence:' in line:
                confidence_line = line
                break
        
        assert confidence_line, "No Confidence line found"
        
        # Extract percentage value
        confidence_match = re.search(r'(\d+\.?\d*)%', confidence_line)
        assert confidence_match, f"No percentage in confidence line: {confidence_line}"
        
        confidence_value = float(confidence_match.group(1))
        assert confidence_value > 0, f"Confidence should be > 0: {confidence_value}%"
        assert confidence_value <= 100, f"Invalid confidence: {confidence_value}%"
    
    def test_analyze_no_fallback_violations_anywhere(self):
        """
        CRITICAL TEST: Analyze output must have NO fallback indicators.
        Tests NO FALLBACK principle comprehensively.
        """
        # Generate transcript
        gen_result = run_cli(['generate', '--topic', 'No Fallback Test', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        # Analyze
        analyze_result = run_cli(['analyze', '-t', transcript_id])
        assert analyze_result.returncode == 0, \
            f"Analyze failed: {analyze_result.stderr}"
        
        # Check for ANY fallback indicators (violates NO FALLBACK)
        fallback_indicators = [
            'Unknown',
            'N/A',
            'Not Available',
            '0.00%',
            'Default',
            'Missing',
            'Empty'
        ]
        
        output_lower = analyze_result.stdout.lower()
        for indicator in fallback_indicators:
            assert indicator.lower() not in output_lower, \
                f"VIOLATION: Found fallback indicator '{indicator}' in analyze output"
    
    def test_analyze_displays_rich_analysis_data(self):
        """
        TEST: Analyze should show rich data beyond basic intent/sentiment.
        System has rich analysis capabilities that should be displayed.
        """
        # Generate transcript
        gen_result = run_cli(['generate', '--topic', 'Rich Data Test', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        # Analyze with show-risk flag
        analyze_result = run_cli(['analyze', '-t', transcript_id, '--show-risk'])
        assert analyze_result.returncode == 0, \
            f"Analyze with --show-risk failed: {analyze_result.stderr}"
        
        # Should show rich analysis beyond basic fields
        rich_data_indicators = [
            'Risk',      # Risk assessment
            'Score',     # Various scores
            'Analysis',  # Analysis details
            'ID:'        # Analysis ID
        ]
        
        found_indicators = 0
        for indicator in rich_data_indicators:
            if indicator in analyze_result.stdout:
                found_indicators += 1
        
        assert found_indicators >= 2, \
            f"Should show rich analysis data. Found {found_indicators} indicators in: {analyze_result.stdout}"
    
    def test_analyze_with_invalid_transcript_fails_fast(self):
        """
        TEST: Analyzing invalid transcript should fail fast.
        NO FALLBACK - should error clearly, not show defaults.
        """
        fake_id = "CALL_FAKE123"
        
        analyze_result = run_cli(['analyze', '-t', fake_id])
        
        # Should fail fast (non-zero exit code)
        assert analyze_result.returncode != 0, \
            "Should fail when analyzing non-existent transcript"
        
        # Should have clear error message
        assert 'not found' in analyze_result.stderr.lower() or \
               'not found' in analyze_result.stdout.lower() or \
               'failed' in analyze_result.stderr.lower(), \
               f"Should show clear error: {analyze_result.stderr}"
        
        # Should NOT show analysis results with fallback values
        assert 'Intent: Unknown' not in analyze_result.stdout, \
            "Should not show fallback analysis for invalid transcript"
    
    def test_analyze_command_follows_no_fallback_principle(self):
        """
        META TEST: Verify analyze command architecture follows NO FALLBACK.
        This tests the principle at the code level.
        """
        # Generate transcript
        gen_result = run_cli(['generate', '--topic', 'Principle Test', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        # Analyze
        analyze_result = run_cli(['analyze', '-t', transcript_id])
        assert analyze_result.returncode == 0, \
            f"Analyze failed: {analyze_result.stderr}"
        
        # The output should reflect real AI analysis, not placeholder data
        output_lines = analyze_result.stdout.strip().split('\n')
        
        # Should have substantial output (not minimal fallback)
        assert len(output_lines) >= 5, \
            "Analyze output too short - likely showing minimal fallback data"
        
        # Should show actual analysis ID format
        analysis_id_found = False
        for line in output_lines:
            if 'Analysis ID:' in line and 'ANALYSIS_' in line:
                analysis_id_found = True
                break
        
        assert analysis_id_found, "Should show real Analysis ID"
        
        # Should show detailed, meaningful information
        total_content_length = len(analyze_result.stdout.replace(' ', '').replace('\n', ''))
        assert total_content_length > 100, \
            f"Analyze output too brief ({total_content_length} chars) - likely fallback data"


class TestAnalyzeIntegration:
    """Integration tests for analyze functionality."""
    
    def test_generate_then_analyze_workflow(self):
        """
        INTEGRATION TEST: Complete workflow of generate -> analyze.
        """
        # Generate
        gen_result = run_cli(['generate', '--topic', 'Integration Workflow', '--store'])
        assert gen_result.returncode == 0, "Generate failed"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID"
        transcript_id = transcript_id_match.group()
        
        # Analyze
        analyze_result = run_cli(['analyze', '-t', transcript_id])
        assert analyze_result.returncode == 0, "Analyze should succeed"
        
        # Should show real analysis data
        assert 'Intent:' in analyze_result.stdout, "Missing intent"
        assert 'Sentiment:' in analyze_result.stdout, "Missing sentiment"
        assert 'Confidence:' in analyze_result.stdout, "Missing confidence"
        
        # Should not show any fallback values
        assert 'Unknown' not in analyze_result.stdout, "Should not show fallback values"
    
    def test_analyze_multiple_transcripts_consistency(self):
        """
        TEST: Analyzing multiple transcripts should consistently show real data.
        """
        transcript_ids = []
        
        # Generate multiple transcripts
        for i in range(2):
            gen_result = run_cli(['generate', '--topic', f'Multi Test {i}', '--store'])
            assert gen_result.returncode == 0, f"Generate {i} failed"
            
            match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
            assert match, f"No ID for transcript {i}"
            transcript_ids.append(match.group())
        
        # Analyze each
        for i, transcript_id in enumerate(transcript_ids):
            analyze_result = run_cli(['analyze', '-t', transcript_id])
            assert analyze_result.returncode == 0, f"Analyze {i} failed"
            
            # Each should show real data (no fallbacks)
            assert 'Intent: Unknown' not in analyze_result.stdout, \
                f"Transcript {i} shows fallback intent"
            assert 'Sentiment: Unknown' not in analyze_result.stdout, \
                f"Transcript {i} shows fallback sentiment"
            assert 'Confidence: 0.00%' not in analyze_result.stdout, \
                f"Transcript {i} shows fallback confidence"


class TestAnalyzeErrorHandling:
    """Test error handling for analyze command following FAIL FAST principle."""
    
    def test_analyze_missing_transcript_fails_fast(self):
        """
        TEST: Missing transcript should fail fast, not show fallback analysis.
        """
        analyze_result = run_cli(['analyze', '-t', 'CALL_MISSING'])
        
        # Should fail fast
        assert analyze_result.returncode != 0, "Should fail for missing transcript"
        
        # Should not show analysis with fallback values
        assert 'Analysis Results:' not in analyze_result.stdout, \
            "Should not show analysis results for missing transcript"
    
    def test_analyze_invalid_format_fails_fast(self):
        """
        TEST: Invalid transcript ID format should fail fast.
        """
        analyze_result = run_cli(['analyze', '-t', 'INVALID_ID'])
        
        # Should fail fast
        assert analyze_result.returncode != 0, "Should fail for invalid ID format"
        
        # Should show clear error
        error_output = analyze_result.stderr + analyze_result.stdout
        assert 'invalid' in error_output.lower() or \
               'not found' in error_output.lower() or \
               'failed' in error_output.lower(), \
               "Should show clear error message"