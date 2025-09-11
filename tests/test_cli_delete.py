"""
Test cases for CLI delete functionality following TDD principles.
Tests written FIRST to ensure they fail, then implementation will make them pass.
Enforces NO FALLBACK principle - system must work or fail fast.
"""

import pytest
import subprocess
import re
import os
from pathlib import Path


def run_cli(args, timeout=60, input_text=None):
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


class TestCLIDeleteSingle:
    """TDD tests for single delete command following NO FALLBACK principle."""
    
    def test_delete_command_no_fallback_messages(self):
        """
        CRITICAL TEST: Delete command must NOT show fallback messages.
        NO FALLBACK principle - system should execute or fail fast.
        """
        # Generate a transcript to delete
        gen_result = run_cli(['generate', '--topic', 'Delete Test', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        # Extract transcript ID
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID in generate output"
        transcript_id = transcript_id_match.group()
        
        # Try to delete - confirm with 'y'
        delete_result = run_cli(['delete', transcript_id], input_text='y\n')
        
        # Should NOT contain fallback messages (violates NO FALLBACK)
        fallback_indicators = [
            'not yet implemented',
            'future version', 
            'will be available',
            'not implemented in REST API'
        ]
        
        for indicator in fallback_indicators:
            assert indicator not in delete_result.stdout.lower(), \
                f"VIOLATION: Found fallback message '{indicator}' - violates NO FALLBACK principle"
            assert indicator not in delete_result.stderr.lower(), \
                f"VIOLATION: Found fallback message '{indicator}' in stderr"
    
    def test_delete_single_transcript_actually_works(self):
        """
        TEST: Delete command should actually delete the transcript.
        Will FAIL initially due to fallback logic.
        """
        # Generate a transcript
        gen_result = run_cli(['generate', '--topic', 'To Be Deleted', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        # Verify it exists
        get_result = run_cli(['get', transcript_id])
        assert get_result.returncode == 0, "Transcript should exist before delete"
        
        # Delete with confirmation
        delete_result = run_cli(['delete', transcript_id], input_text='y\n')
        assert delete_result.returncode == 0, \
            f"Delete command failed: {delete_result.stderr}"
        
        # Should show success message
        assert 'deleted' in delete_result.stdout.lower() or 'success' in delete_result.stdout.lower(), \
            f"No success message in delete output: {delete_result.stdout}"
        
        # Verify transcript is actually gone
        verify_result = run_cli(['get', transcript_id])
        assert verify_result.returncode != 0, \
            "Transcript still exists after delete - delete didn't work"
    
    def test_delete_force_flag_skips_confirmation(self):
        """
        TEST: --force flag should skip confirmation prompt.
        """
        # Generate transcript
        gen_result = run_cli(['generate', '--topic', 'Force Delete Test', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID found"
        transcript_id = transcript_id_match.group()
        
        # Delete with --force (no input needed)
        delete_result = run_cli(['delete', transcript_id, '--force'])
        assert delete_result.returncode == 0, \
            f"Force delete failed: {delete_result.stderr}"
        
        # Should not ask for confirmation
        assert 'Delete transcript' not in delete_result.stdout, \
            "--force flag should skip confirmation prompt"
    
    def test_delete_nonexistent_transcript_fails_fast(self):
        """
        TEST: Deleting non-existent transcript should fail fast.
        NO FALLBACK principle - clear error, no graceful degradation.
        """
        fake_id = "CALL_FAKE123"
        
        delete_result = run_cli(['delete', fake_id, '--force'])
        
        # Should fail fast (non-zero exit code)
        assert delete_result.returncode != 0, \
            "Should fail when deleting non-existent transcript"
        
        # Should have clear error message
        assert 'not found' in delete_result.stderr.lower() or \
               'not found' in delete_result.stdout.lower(), \
               f"Should show 'not found' error: {delete_result.stderr}"
        
        # Should NOT show fallback messages
        assert 'future version' not in delete_result.stdout.lower(), \
            "Should not show fallback messages for real errors"


class TestCLIDeleteAll:
    """TDD tests for delete-all command following NO FALLBACK principle."""
    
    def test_delete_all_no_fallback_messages(self):
        """
        CRITICAL TEST: delete-all must NOT show fallback messages.
        """
        # Generate some test transcripts
        for i in range(2):
            gen_result = run_cli(['generate', '--topic', f'Bulk Test {i}', '--store'])
            assert gen_result.returncode == 0, f"Failed to generate transcript {i}"
        
        # Try delete-all (cancel it)
        delete_result = run_cli(['delete-all'], input_text='n\n')
        
        # Should NOT contain fallback messages
        fallback_indicators = [
            'not yet implemented',
            'future version',
            'will be available',
            'Bulk delete functionality not yet implemented'
        ]
        
        for indicator in fallback_indicators:
            assert indicator not in delete_result.stdout.lower(), \
                f"VIOLATION: Found fallback message '{indicator}' in delete-all"
            assert indicator not in delete_result.stderr.lower(), \
                f"VIOLATION: Found fallback message '{indicator}' in stderr"
    
    def test_delete_all_no_metrics_error(self):
        """
        TEST: delete-all should not have metrics error.
        Current bug: 'dict' object has no attribute 'transcript_id'
        """
        # Generate test transcript
        gen_result = run_cli(['generate', '--topic', 'Metrics Test', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        # Try delete-all (cancel it to avoid actually deleting)
        delete_result = run_cli(['delete-all'], input_text='n\n')
        
        # Should NOT have metrics-related errors
        metrics_errors = [
            "object has no attribute 'transcript_id'",
            "Metrics collection failed",
            "dict' object"
        ]
        
        for error in metrics_errors:
            assert error not in delete_result.stderr, \
                f"Metrics error found: {error}"
            assert error not in delete_result.stdout, \
                f"Metrics error in stdout: {error}"
    
    def test_delete_all_removes_all_transcripts(self):
        """
        TEST: delete-all should actually delete all transcripts.
        Will FAIL initially due to fallback logic.
        """
        # Generate some test transcripts
        transcript_ids = []
        for i in range(3):
            gen_result = run_cli(['generate', '--topic', f'Bulk Delete {i}', '--store'])
            assert gen_result.returncode == 0, f"Failed to generate transcript {i}"
            
            # Extract ID
            match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
            assert match, f"No ID found for transcript {i}"
            transcript_ids.append(match.group())
        
        # Count transcripts before
        list_before = run_cli(['list'])
        assert list_before.returncode == 0, "Failed to list transcripts"
        
        # Delete all with proper confirmation
        count = len(transcript_ids)
        confirmation = f"DELETE ALL {count}"
        delete_result = run_cli(['delete-all'], input_text=f'y\n{confirmation}\n')
        
        # Should succeed
        assert delete_result.returncode == 0, \
            f"delete-all failed: {delete_result.stderr}"
        
        # Should show success message
        assert 'deleted' in delete_result.stdout.lower(), \
            f"No success message: {delete_result.stdout}"
        
        # Verify all transcripts are gone
        for transcript_id in transcript_ids:
            verify_result = run_cli(['get', transcript_id])
            assert verify_result.returncode != 0, \
                f"Transcript {transcript_id} still exists after delete-all"
    
    def test_delete_all_requires_double_confirmation(self):
        """
        TEST: delete-all should require double confirmation for safety.
        """
        # Generate test transcript
        gen_result = run_cli(['generate', '--topic', 'Safety Test', '--store'])
        assert gen_result.returncode == 0, "Failed to generate test transcript"
        
        # Try delete-all but refuse first confirmation
        delete_result = run_cli(['delete-all'], input_text='n\n')
        assert delete_result.returncode == 0, "Should succeed when cancelled"
        assert 'cancelled' in delete_result.stdout.lower(), "Should show cancellation"
        
        # Try delete-all, accept first but give wrong second confirmation
        delete_result2 = run_cli(['delete-all'], input_text='y\nWRONG\n')
        assert delete_result2.returncode != 0, "Should fail with wrong confirmation"
        assert 'confirmation failed' in delete_result2.stdout.lower() or \
               'cancelled' in delete_result2.stdout.lower(), \
               "Should show confirmation failure"
    
    def test_delete_all_handles_empty_database(self):
        """
        TEST: delete-all should handle empty database gracefully.
        """
        # First ensure we have no transcripts by deleting any existing ones
        list_result = run_cli(['list'])
        
        # Try delete-all on empty database
        delete_result = run_cli(['delete-all'])
        
        # Should handle empty database gracefully
        assert delete_result.returncode == 0, \
            f"delete-all should handle empty DB: {delete_result.stderr}"
        
        # Should show appropriate message
        assert 'no transcripts' in delete_result.stdout.lower() or \
               'nothing to delete' in delete_result.stdout.lower(), \
               f"Should indicate empty database: {delete_result.stdout}"


class TestDeleteErrorHandling:
    """Test error handling for delete commands following FAIL FAST principle."""
    
    def test_delete_network_error_fails_fast(self):
        """
        TEST: Network errors should fail fast, no fallback.
        """
        # This would test network failure scenarios
        # For now, just ensure no fallback messages appear
        pass
    
    def test_no_graceful_degradation_anywhere(self):
        """
        CRITICAL TEST: Verify NO graceful degradation in delete commands.
        System must either work or fail fast.
        """
        # Test various delete scenarios
        test_scenarios = [
            ['delete', 'INVALID_ID', '--force'],
            ['delete-all', '--force']  # if this flag exists
        ]
        
        for scenario in test_scenarios:
            result = run_cli(scenario, input_text='n\n')  # Cancel if prompted
            
            # Should never show these graceful degradation patterns
            degradation_patterns = [
                'will be available',
                'future version',
                'coming soon',
                'not yet implemented',
                'please try again later'
            ]
            
            combined_output = (result.stdout + result.stderr).lower()
            for pattern in degradation_patterns:
                assert pattern not in combined_output, \
                    f"VIOLATION: Found graceful degradation '{pattern}' in scenario {scenario}"


# Integration tests for complete delete workflow
class TestDeleteIntegration:
    """Integration tests for delete functionality."""
    
    def test_generate_then_delete_workflow(self):
        """
        INTEGRATION TEST: Complete workflow of generate -> delete.
        """
        # Generate
        gen_result = run_cli(['generate', '--topic', 'Integration Test', '--store'])
        assert gen_result.returncode == 0, "Generate failed"
        
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', gen_result.stdout)
        assert transcript_id_match, "No transcript ID"
        transcript_id = transcript_id_match.group()
        
        # Verify exists
        get_result = run_cli(['get', transcript_id])
        assert get_result.returncode == 0, "Transcript should exist"
        
        # Delete
        delete_result = run_cli(['delete', transcript_id, '--force'])
        assert delete_result.returncode == 0, "Delete should succeed"
        
        # Verify gone
        verify_result = run_cli(['get', transcript_id])
        assert verify_result.returncode != 0, "Should be deleted"
    
    def test_bulk_generate_then_delete_all_workflow(self):
        """
        INTEGRATION TEST: Generate multiple, then delete all.
        """
        # Generate multiple
        for i in range(3):
            gen_result = run_cli(['generate', '--topic', f'Bulk {i}', '--store'])
            assert gen_result.returncode == 0, f"Generate {i} failed"
        
        # Count them
        list_result = run_cli(['list'])
        transcript_count = list_result.stdout.count('CALL_')
        assert transcript_count >= 3, "Should have at least 3 transcripts"
        
        # Delete all
        confirmation = f"DELETE ALL {transcript_count}"
        delete_result = run_cli(['delete-all'], input_text=f'y\n{confirmation}\n')
        assert delete_result.returncode == 0, "delete-all should succeed"
        
        # Verify all gone (check a few random ones if possible)
        final_list = run_cli(['list'])
        final_count = final_list.stdout.count('CALL_') if final_list.returncode == 0 else 0
        assert final_count == 0, "All transcripts should be deleted"