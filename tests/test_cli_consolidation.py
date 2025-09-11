"""
Test cases for consolidated CLI structure following TDD principles.
Tests written FIRST to ensure they fail, then implementation will make them pass.
Enforces NO FALLBACK principle - consolidated commands must work or fail fast.
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


class TestTranscriptCommand:
    """TDD tests for consolidated transcript command."""
    
    def test_transcript_command_exists(self):
        """
        TEST: transcript command should exist with subcommands.
        """
        result = run_cli(['transcript', '--help'])
        assert result.returncode == 0, "transcript command should exist"
        assert 'transcript' in result.stdout.lower(), "Should show transcript help"
    
    def test_transcript_create_subcommand(self):
        """
        TEST: transcript create should work like old generate command.
        """
        result = run_cli(['transcript', 'create', '--topic', 'Test Topic', '--store'])
        assert result.returncode == 0, f"transcript create failed: {result.stderr}"
        assert 'CALL_' in result.stdout, "Should generate transcript with ID"
    
    def test_transcript_list_subcommand(self):
        """
        TEST: transcript list should work like old list command.
        """
        result = run_cli(['transcript', 'list'])
        assert result.returncode == 0, f"transcript list failed: {result.stderr}"
        # Should show list of transcripts or empty message
    
    def test_transcript_get_subcommand(self):
        """
        TEST: transcript get should work like old get command.
        """
        # First create a transcript
        create_result = run_cli(['transcript', 'create', '--topic', 'Get Test', '--store'])
        assert create_result.returncode == 0, "Failed to create test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', create_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        # Get the transcript
        get_result = run_cli(['transcript', 'get', transcript_id])
        assert get_result.returncode == 0, f"transcript get failed: {get_result.stderr}"
        assert transcript_id in get_result.stdout, "Should show transcript details"
    
    def test_transcript_delete_subcommand(self):
        """
        TEST: transcript delete should work like old delete command.
        """
        # Create transcript
        create_result = run_cli(['transcript', 'create', '--topic', 'Delete Test', '--store'])
        assert create_result.returncode == 0, "Failed to create test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', create_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        # Delete it
        delete_result = run_cli(['transcript', 'delete', transcript_id, '--force'])
        assert delete_result.returncode == 0, f"transcript delete failed: {delete_result.stderr}"
    
    def test_transcript_search_subcommand(self):
        """
        TEST: transcript search should work like old search command.
        """
        result = run_cli(['transcript', 'search', '--query', 'test'])
        assert result.returncode == 0, f"transcript search failed: {result.stderr}"


class TestAnalysisCommand:
    """TDD tests for consolidated analysis command."""
    
    def test_analysis_command_exists(self):
        """
        TEST: analysis command should exist with subcommands.
        """
        result = run_cli(['analysis', '--help'])
        assert result.returncode == 0, "analysis command should exist"
        assert 'analysis' in result.stdout.lower(), "Should show analysis help"
    
    def test_analysis_create_subcommand(self):
        """
        TEST: analysis create should work like old analyze command.
        """
        # First create transcript
        transcript_result = run_cli(['transcript', 'create', '--topic', 'Analysis Test', '--store'])
        assert transcript_result.returncode == 0, "Failed to create test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', transcript_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        # Create analysis
        result = run_cli(['analysis', 'create', '--transcript', transcript_id])
        assert result.returncode == 0, f"analysis create failed: {result.stderr}"
        assert 'ANALYSIS_' in result.stdout, "Should show analysis results"
    
    def test_analysis_list_subcommand(self):
        """
        TEST: analysis list should work like old list-analyses command.
        """
        result = run_cli(['analysis', 'list'])
        assert result.returncode == 0, f"analysis list failed: {result.stderr}"
    
    def test_analysis_metrics_subcommand(self):
        """
        TEST: analysis metrics should work like old analysis-metrics command.
        """
        result = run_cli(['analysis', 'metrics'])
        assert result.returncode == 0, f"analysis metrics failed: {result.stderr}"
    
    def test_analysis_risk_report_subcommand(self):
        """
        TEST: analysis risk-report should work like old risk-report command.
        """
        result = run_cli(['analysis', 'risk-report'])
        assert result.returncode == 0, f"analysis risk-report failed: {result.stderr}"
    
    def test_analysis_delete_subcommand_exists(self):
        """
        TEST: analysis delete command should exist (TDD - fails first).
        """
        result = run_cli(['analysis', '--help'])
        assert result.returncode == 0, "analysis command should exist"
        assert 'delete' in result.stdout.lower(), "Should have delete subcommand"
    
    def test_analysis_delete_subcommand_with_confirmation(self):
        """
        TEST: analysis delete should work with confirmation like transcript delete (TDD - fails first).
        """
        # Create analysis first
        transcript_result = run_cli(['transcript', 'create', '--topic', 'Delete Test', '--store'])
        assert transcript_result.returncode == 0, "Failed to create test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', transcript_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        analysis_result = run_cli(['analysis', 'create', '--transcript', transcript_id])
        assert analysis_result.returncode == 0, "Failed to create test analysis"
        
        analysis_id_match = re.search(r'ANALYSIS_[A-Z0-9_]{8,}', analysis_result.stdout)
        assert analysis_id_match, "No analysis ID found"
        analysis_id = analysis_id_match.group()
        
        # Test delete with force flag
        delete_result = run_cli(['analysis', 'delete', analysis_id, '--force'])
        assert delete_result.returncode == 0, f"analysis delete failed: {delete_result.stderr}"
        assert 'deleted' in delete_result.stdout.lower(), "Should confirm deletion"
    
    def test_analysis_delete_all_subcommand_exists(self):
        """
        TEST: analysis delete-all command should exist (TDD - fails first).
        """
        result = run_cli(['analysis', '--help'])
        assert result.returncode == 0, "analysis command should exist"
        assert 'delete-all' in result.stdout.lower(), "Should have delete-all subcommand"
    
    def test_analysis_delete_all_with_force(self):
        """
        TEST: analysis delete-all should work with --force flag (TDD - fails first).
        """
        result = run_cli(['analysis', 'delete-all', '--force'])
        assert result.returncode == 0, f"analysis delete-all failed: {result.stderr}"
        assert 'deleted' in result.stdout.lower(), "Should confirm bulk deletion"
    
    def test_analysis_delete_nonexistent_fails_fast(self):
        """
        TEST: analysis delete with non-existent ID should fail fast (NO FALLBACK).
        """
        result = run_cli(['analysis', 'delete', 'ANALYSIS_NONEXISTENT', '--force'])
        assert result.returncode == 1, "Should fail for non-existent analysis"
        assert 'not found' in result.stdout.lower() or 'error' in result.stdout.lower(), "Should show clear error"


class TestPlanCommand:
    """TDD tests for consolidated plan command."""
    
    def test_plan_command_exists(self):
        """
        TEST: plan command should exist with subcommands.
        """
        result = run_cli(['plan', '--help'])
        assert result.returncode == 0, "plan command should exist"
        assert 'plan' in result.stdout.lower(), "Should show plan help"
    
    def test_plan_create_subcommand(self):
        """
        TEST: plan create should work like old create-plan commands.
        """
        # Create transcript and analysis first
        transcript_result = run_cli(['transcript', 'create', '--topic', 'Plan Test', '--store'])
        assert transcript_result.returncode == 0, "Failed to create test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', transcript_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        analysis_result = run_cli(['analysis', 'create', '--transcript', transcript_id])
        assert analysis_result.returncode == 0, "Failed to create analysis"
        
        analysis_id_match = re.search(r'ANALYSIS_[A-Z0-9_]+', analysis_result.stdout)
        assert analysis_id_match, "No analysis ID found"
        analysis_id = analysis_id_match.group()
        
        # Create plan
        result = run_cli(['plan', 'create', '--analysis', analysis_id])
        assert result.returncode == 0, f"plan create failed: {result.stderr}"
    
    def test_plan_list_subcommand(self):
        """
        TEST: plan list should work like old action-plan-queue command.
        """
        result = run_cli(['plan', 'list'])
        assert result.returncode == 0, f"plan list failed: {result.stderr}"
    
    def test_plan_metrics_subcommand(self):
        """
        TEST: plan metrics should work like old action-plan-summary command.
        """
        result = run_cli(['plan', 'metrics'])
        assert result.returncode == 0, f"plan metrics failed: {result.stderr}"


class TestCaseCommand:
    """TDD tests for new case command (missing from current CLI)."""
    
    def test_case_command_exists(self):
        """
        TEST: case command should exist (new functionality).
        """
        result = run_cli(['case', '--help'])
        assert result.returncode == 0, "case command should exist"
        assert 'case' in result.stdout.lower(), "Should show case help"
    
    def test_case_list_subcommand(self):
        """
        TEST: case list should provide case management functionality.
        """
        result = run_cli(['case', 'list'])
        assert result.returncode == 0, f"case list failed: {result.stderr}"


class TestGovernanceCommand:
    """TDD tests for consolidated governance command."""
    
    def test_governance_command_exists(self):
        """
        TEST: governance command should exist with subcommands.
        """
        result = run_cli(['governance', '--help'])
        assert result.returncode == 0, "governance command should exist"
        assert 'governance' in result.stdout.lower(), "Should show governance help"
    
    def test_governance_queue_subcommand(self):
        """
        TEST: governance queue should work like old get-approval-queue command.
        """
        result = run_cli(['governance', 'queue'])
        assert result.returncode == 0, f"governance queue failed: {result.stderr}"
    
    def test_governance_metrics_subcommand(self):
        """
        TEST: governance metrics should work like old approval-metrics command.
        """
        result = run_cli(['governance', 'metrics'])
        assert result.returncode == 0, f"governance metrics failed: {result.stderr}"


class TestSystemCommand:
    """TDD tests for consolidated system command."""
    
    def test_system_command_exists(self):
        """
        TEST: system command should exist with subcommands.
        """
        result = run_cli(['system', '--help'])
        assert result.returncode == 0, "system command should exist"
        assert 'system' in result.stdout.lower(), "Should show system help"
    
    def test_system_health_subcommand(self):
        """
        TEST: system health should work like old health command.
        """
        result = run_cli(['system', 'health'])
        assert result.returncode == 0, f"system health failed: {result.stderr}"
    
    def test_system_metrics_subcommand(self):
        """
        TEST: system metrics should work like old stats command.
        """
        result = run_cli(['system', 'metrics'])
        assert result.returncode == 0, f"system metrics failed: {result.stderr}"


class TestNoFallbackPrinciple:
    """Test that consolidated commands follow NO FALLBACK principle."""
    
    def test_invalid_subcommands_fail_fast(self):
        """
        TEST: Invalid subcommands should fail fast, not show fallback messages.
        """
        commands = [
            ['transcript', 'invalid-subcommand'],
            ['analysis', 'invalid-subcommand'],
            ['plan', 'invalid-subcommand'],
            ['case', 'invalid-subcommand'],
            ['governance', 'invalid-subcommand'],
            ['system', 'invalid-subcommand']
        ]
        
        for cmd in commands:
            result = run_cli(cmd)
            assert result.returncode != 0, f"{' '.join(cmd)} should fail for invalid subcommand"
            
            # Should NOT show fallback messages
            fallback_indicators = [
                'not yet implemented',
                'coming soon',
                'future version',
                'will be available'
            ]
            
            combined_output = (result.stdout + result.stderr).lower()
            for indicator in fallback_indicators:
                assert indicator not in combined_output, \
                    f"VIOLATION: Found fallback message '{indicator}' in {' '.join(cmd)}"
    
    def test_missing_required_args_fail_fast(self):
        """
        TEST: Missing required arguments should fail fast with clear errors.
        """
        failing_commands = [
            ['transcript', 'get'],  # Missing ID
            ['transcript', 'delete'],  # Missing ID
            ['analysis', 'create'],  # Missing --transcript
            ['plan', 'create'],  # Missing --analysis
            ['governance', 'approve']  # Missing ID
        ]
        
        for cmd in failing_commands:
            result = run_cli(cmd)
            assert result.returncode != 0, f"{' '.join(cmd)} should fail for missing args"
            
            # Should show clear error about missing arguments
            combined_output = (result.stdout + result.stderr).lower()
            assert 'missing' in combined_output or 'required' in combined_output or 'error' in combined_output, \
                f"Should show clear error for {' '.join(cmd)}"


class TestCleanCommandStructure:
    """Test that old commands are completely removed (no backward compatibility)."""
    
    def test_old_commands_completely_removed(self):
        """
        TEST: Old commands should be completely removed and show clear errors.
        """
        old_commands = [
            ['generate', '--topic', 'Test'],
            ['list'],
            ['analyze', '--help'],
            ['list-analyses']
        ]
        
        for old_cmd in old_commands:
            result = run_cli(old_cmd)
            
            # Should fail since commands are removed
            assert result.returncode == 2, f"Old command {' '.join(old_cmd)} should fail (removed)"
            
            # Should show "No such command" error
            combined_output = (result.stdout + result.stderr).lower()
            assert 'no such command' in combined_output, \
                f"Should show 'No such command' error for {' '.join(old_cmd)}"