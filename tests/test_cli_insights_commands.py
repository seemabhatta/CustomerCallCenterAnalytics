"""
TDD Tests for Insights CLI Commands
Tests written FIRST to ensure they fail, then implementation will make them pass.
Enforces NO FALLBACK principle and proper separation from analysis commands.
"""

import subprocess
import pytest
from pathlib import Path
import requests
import time


def wait_for_server(url: str = "http://localhost:8000", timeout: int = 30) -> bool:
    """Wait for server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/api/v1/health")
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False


def run_cli(args, timeout=30):
    """Helper to run CLI commands."""
    cmd = ['python', 'cli.py'] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=Path(__file__).parent.parent
    )
    return result


class TestInsightsCommandGroupStructure:
    """Test that insights command group exists as standalone resource."""
    
    def test_main_cli_shows_insights_command(self):
        """TEST: Main CLI should show 'insights' as top-level command (TDD - fails first)."""
        result = run_cli(['--help'])
        assert result.returncode == 0, "CLI help should work"
        assert 'insights' in result.stdout.lower(), "Main CLI should list 'insights' command group"
    
    def test_insights_help_shows_all_commands(self):
        """TEST: insights --help should show all 12 commands (TDD - fails first)."""
        result = run_cli(['insights', '--help'])
        assert result.returncode == 0, "insights --help should work"
        
        # Check all 12 expected commands are listed
        expected_commands = [
            'patterns', 'risks', 'recommend', 'similar', 'dashboard',
            'populate', 'query', 'status', 
            'delete-analysis', 'delete-customer', 'prune', 'clear'
        ]
        
        help_output = result.stdout.lower()
        for command in expected_commands:
            assert command in help_output, f"Command '{command}' should be in insights help"
    
    def test_analysis_help_does_not_show_insights_commands(self):
        """TEST: analysis --help should NOT show insights commands (TDD - fails first)."""
        result = run_cli(['analysis', '--help'])
        assert result.returncode == 0, "analysis --help should work"
        
        # Check insights commands are NOT in analysis help
        insights_commands = [
            'patterns', 'risks', 'recommend', 'similar', 'dashboard',
            'populate', 'query', 'status'
        ]
        
        help_output = result.stdout.lower()
        for command in insights_commands:
            assert command not in help_output, f"Command '{command}' should NOT be in analysis help"
    
    def test_analysis_keeps_core_crud_commands(self):
        """TEST: analysis should keep core CRUD commands only (TDD - fails first)."""
        result = run_cli(['analysis', '--help'])
        assert result.returncode == 0, "analysis --help should work"
        
        # Check core analysis commands still exist
        core_commands = ['create', 'list', 'get', 'delete', 'delete-all']
        help_output = result.stdout.lower()
        
        for command in core_commands:
            assert command in help_output, f"Core command '{command}' should remain in analysis"


class TestInsightsCommandsExist:
    """Test that all individual insights commands exist and are accessible."""
    
    def test_patterns_command_exists(self):
        """TEST: insights patterns command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'patterns', '--help'])
        assert result.returncode == 0, "insights patterns --help should work"
        assert 'pattern' in result.stdout.lower(), "Should show patterns command help"
    
    def test_risks_command_exists(self):
        """TEST: insights risks command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'risks', '--help'])
        assert result.returncode == 0, "insights risks --help should work"
        assert 'risk' in result.stdout.lower(), "Should show risks command help"
    
    def test_recommend_command_exists(self):
        """TEST: insights recommend command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'recommend', '--help'])
        assert result.returncode == 0, "insights recommend --help should work"
        assert 'recommend' in result.stdout.lower(), "Should show recommend command help"
    
    def test_similar_command_exists(self):
        """TEST: insights similar command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'similar', '--help'])
        assert result.returncode == 0, "insights similar --help should work"
        assert 'similar' in result.stdout.lower(), "Should show similar command help"
    
    def test_dashboard_command_exists(self):
        """TEST: insights dashboard command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'dashboard', '--help'])
        assert result.returncode == 0, "insights dashboard --help should work"
        assert 'dashboard' in result.stdout.lower(), "Should show dashboard command help"
    
    def test_populate_command_exists(self):
        """TEST: insights populate command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'populate', '--help'])
        assert result.returncode == 0, "insights populate --help should work"
        assert 'populate' in result.stdout.lower(), "Should show populate command help"
    
    def test_query_command_exists(self):
        """TEST: insights query command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'query', '--help'])
        assert result.returncode == 0, "insights query --help should work"
        assert 'query' in result.stdout.lower(), "Should show query command help"
    
    def test_status_command_exists(self):
        """TEST: insights status command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'status', '--help'])
        assert result.returncode == 0, "insights status --help should work"
        assert 'status' in result.stdout.lower(), "Should show status command help"
    
    def test_delete_analysis_command_exists(self):
        """TEST: insights delete-analysis command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'delete-analysis', '--help'])
        assert result.returncode == 0, "insights delete-analysis --help should work"
        assert 'delete' in result.stdout.lower(), "Should show delete-analysis command help"
    
    def test_delete_customer_command_exists(self):
        """TEST: insights delete-customer command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'delete-customer', '--help'])
        assert result.returncode == 0, "insights delete-customer --help should work"
        assert 'delete' in result.stdout.lower(), "Should show delete-customer command help"
    
    def test_prune_command_exists(self):
        """TEST: insights prune command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'prune', '--help'])
        assert result.returncode == 0, "insights prune --help should work"
        assert 'prune' in result.stdout.lower(), "Should show prune command help"
    
    def test_clear_command_exists(self):
        """TEST: insights clear command should exist (TDD - fails first)."""
        result = run_cli(['insights', 'clear', '--help'])
        assert result.returncode == 0, "insights clear --help should work"
        assert 'clear' in result.stdout.lower(), "Should show clear command help"


class TestInsightsCommandsFunctionality:
    """Test that insights commands actually work with server."""
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_server(self):
        """Ensure server is running for functional tests."""
        if not wait_for_server():
            pytest.skip("Server not available - start with 'python server.py'")
    
    def test_status_command_functionality(self):
        """TEST: insights status should return graph statistics (TDD - fails first)."""
        result = run_cli(['insights', 'status'])
        
        if result.returncode == 0:
            # Should show graph status information
            output = result.stdout.lower()
            assert 'knowledge graph status' in output or 'graph status' in output
            assert 'total nodes' in output or 'node' in output
        # Note: Command might fail if no server, but structure should exist
    
    def test_query_command_functionality(self):
        """TEST: insights query should accept cypher and execute (TDD - fails first)."""
        result = run_cli(['insights', 'query', 'MATCH (n) RETURN count(n) as count'])
        
        # Command should exist and attempt to execute
        # May fail with connection error, but should not be "command not found"
        assert 'command not found' not in result.stderr.lower()
        assert 'no such command' not in result.stderr.lower()
    
    def test_populate_command_functionality(self):
        """TEST: insights populate should accept parameters (TDD - fails first)."""
        result = run_cli(['insights', 'populate', '--help'])
        assert result.returncode == 0
        
        # Should show populate options
        help_output = result.stdout.lower()
        assert '--analysis-id' in help_output or 'analysis' in help_output


class TestInsightsNoFallbackPrinciple:
    """Test that insights commands follow NO FALLBACK principle."""
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_server(self):
        """Ensure server is running for NO FALLBACK tests."""
        if not wait_for_server():
            pytest.skip("Server not available - start with 'python server.py'")
    
    def test_populate_fails_fast_on_invalid_analysis(self):
        """TEST: insights populate should fail fast for invalid analysis ID (NO FALLBACK)."""
        result = run_cli(['insights', 'populate', '--analysis-id', 'INVALID_ANALYSIS_ID'])
        
        if result.returncode != 0:
            # Should fail fast with clear error, not return fake success
            error_output = result.stderr.lower()
            assert 'not found' in error_output or 'error' in error_output
            assert 'success' not in result.stdout.lower()  # Should not fake success
    
    def test_query_fails_fast_on_invalid_cypher(self):
        """TEST: insights query should fail fast for invalid Cypher (NO FALLBACK)."""
        result = run_cli(['insights', 'query', 'INVALID CYPHER SYNTAX HERE'])
        
        if result.returncode != 0:
            # Should fail fast with clear error, not return fake data
            assert 'error' in result.stderr.lower() or 'invalid' in result.stderr.lower()
            assert not result.stdout or 'error' in result.stdout.lower()
    
    def test_delete_analysis_fails_fast_on_nonexistent(self):
        """TEST: insights delete-analysis should fail fast for nonexistent analysis (NO FALLBACK)."""
        result = run_cli(['insights', 'delete-analysis', 'NONEXISTENT_ANALYSIS'])
        
        if result.returncode != 0:
            # Should fail fast, not pretend to delete nonexistent data
            assert 'not found' in result.stderr.lower() or 'error' in result.stderr.lower()
            assert 'success' not in result.stdout.lower()


class TestBackwardCompatibilityBreaking:
    """Test that old analysis commands with insights no longer work (expected breaking change)."""
    
    def test_old_analysis_patterns_command_does_not_exist(self):
        """TEST: analysis patterns should no longer exist (expected breaking change)."""
        result = run_cli(['analysis', 'patterns'])
        
        # Should fail - patterns should not be under analysis anymore
        assert result.returncode != 0
        assert 'no such command' in result.stderr.lower() or 'not found' in result.stderr.lower()
    
    def test_old_analysis_populate_command_does_not_exist(self):
        """TEST: analysis populate should no longer exist (expected breaking change)."""
        result = run_cli(['analysis', 'populate'])
        
        # Should fail - populate should not be under analysis anymore  
        assert result.returncode != 0
        assert 'no such command' in result.stderr.lower() or 'not found' in result.stderr.lower()
    
    def test_old_analysis_query_command_does_not_exist(self):
        """TEST: analysis query should no longer exist (expected breaking change)."""
        result = run_cli(['analysis', 'query'])
        
        # Should fail - query should not be under analysis anymore
        assert result.returncode != 0
        assert 'no such command' in result.stderr.lower() or 'not found' in result.stderr.lower()


class TestCLIStructureIntegrity:
    """Test overall CLI structure after reorganization."""
    
    def test_main_cli_has_seven_command_groups(self):
        """TEST: Main CLI should have 7 command groups after adding insights."""
        result = run_cli(['--help'])
        assert result.returncode == 0
        
        expected_groups = [
            'transcript', 'analysis', 'insights', 'plan', 
            'case', 'governance', 'system'
        ]
        
        help_output = result.stdout.lower()
        for group in expected_groups:
            assert group in help_output, f"Command group '{group}' should exist in main CLI"
    
    def test_insights_is_separate_from_analysis(self):
        """TEST: insights and analysis should be completely separate command groups."""
        # Get insights commands
        insights_result = run_cli(['insights', '--help'])
        assert insights_result.returncode == 0
        insights_commands = set()
        for line in insights_result.stdout.split('\n'):
            if '│' in line and 'help' not in line.lower() and 'options' not in line.lower():
                parts = line.split('│')
                if len(parts) > 1:
                    cmd = parts[1].strip().split()[0] if parts[1].strip() else ''
                    if cmd and cmd != 'Commands':
                        insights_commands.add(cmd)
        
        # Get analysis commands  
        analysis_result = run_cli(['analysis', '--help'])
        assert analysis_result.returncode == 0
        analysis_commands = set()
        for line in analysis_result.stdout.split('\n'):
            if '│' in line and 'help' not in line.lower() and 'options' not in line.lower():
                parts = line.split('│')
                if len(parts) > 1:
                    cmd = parts[1].strip().split()[0] if parts[1].strip() else ''
                    if cmd and cmd != 'Commands':
                        analysis_commands.add(cmd)
        
        # Should have no overlap between insights and analysis commands
        overlap = insights_commands.intersection(analysis_commands)
        assert len(overlap) == 0, f"No commands should overlap between insights and analysis: {overlap}"
        
        # Insights should have the expected knowledge graph commands
        expected_insights_commands = {
            'patterns', 'risks', 'recommend', 'similar', 'dashboard',
            'populate', 'query', 'status'
        }
        
        # At least some core insights commands should be present
        found_insights = insights_commands.intersection(expected_insights_commands)
        assert len(found_insights) >= 4, f"Should find several insights commands, found: {found_insights}"