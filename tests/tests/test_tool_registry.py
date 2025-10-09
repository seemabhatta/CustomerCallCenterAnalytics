"""
Test cases for YAML-driven tool registry.
Tests the tool configuration loading and role-based tool assignment.
Follows TDD principles: test first, then implement.
"""
import pytest
import yaml
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_tool_config():
    """Sample tool configuration YAML for testing."""
    return {
        'roles': {
            'advisor': {
                'display_name': 'Mortgage Advisor Assistant',
                'modes': {
                    'borrower': {
                        'prompt_file': 'prompts/advisor_agent/borrower_system_prompt.md',
                        'tools': [
                            'get_transcripts',
                            'get_transcript',
                            'get_analysis_by_transcript',
                            'get_plan_by_transcript',
                            'get_workflows_for_plan',
                            'execute_workflow_step'
                        ],
                        'tool_filters': {
                            'workflow_types': ['BORROWER'],
                            'access_level': 'advisor'
                        }
                    },
                    'selfreflection': {
                        'prompt_file': 'prompts/advisor_agent/selfreflection_system_prompt.md',
                        'tools': [
                            'get_transcripts',
                            'get_analysis_by_transcript',
                            'query_knowledge_graph'
                        ],
                        'tool_filters': {
                            'scope': 'self',
                            'advisor_id': '${current_user}'
                        }
                    }
                }
            },
            'leadership': {
                'display_name': 'Leadership Analytics Assistant',
                'modes': {
                    'borrower': {
                        'prompt_file': 'prompts/leadership_agent/borrower_system_prompt.md',
                        'tools': [
                            'get_transcripts',
                            'get_transcript',
                            'get_analysis_by_transcript',
                            'get_plan_by_transcript',
                            'ask_intelligence_question'
                        ],
                        'tool_filters': {
                            'workflow_types': ['BORROWER', 'ADVISOR', 'COMPLIANCE'],
                            'access_level': 'leadership'
                        }
                    }
                }
            }
        },
        'tool_registry': {
            'get_transcripts': {
                'description': 'List recent customer call transcripts',
                'parameters': [
                    {'name': 'limit', 'type': 'int', 'default': 10}
                ]
            },
            'get_transcript': {
                'description': 'Get specific transcript details',
                'parameters': [
                    {'name': 'transcript_id', 'type': 'str', 'required': True}
                ]
            },
            'get_analysis_by_transcript': {
                'description': 'Get detailed analysis of a call',
                'parameters': [
                    {'name': 'transcript_id', 'type': 'str', 'required': True}
                ]
            },
            'execute_workflow_step': {
                'description': 'Execute a workflow step',
                'parameters': [
                    {'name': 'workflow_id', 'type': 'str', 'required': True},
                    {'name': 'step_number', 'type': 'int', 'required': True}
                ]
            }
        }
    }


@pytest.fixture
def temp_config_file(sample_tool_config):
    """Create temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_tool_config, f)
        config_path = f.name
    yield config_path
    os.unlink(config_path)


@pytest.fixture
def mock_tool_functions():
    """Mock tool functions for testing."""
    async def get_transcripts(limit: int = 10):
        return {'transcripts': []}

    async def get_transcript(transcript_id: str):
        return {'id': transcript_id}

    async def get_analysis_by_transcript(transcript_id: str):
        return {'analysis': 'data'}

    async def get_plan_by_transcript(transcript_id: str):
        return {'plan': 'data'}

    async def get_workflows_for_plan(plan_id: str):
        return [{'id': 'workflow1'}]

    async def execute_workflow_step(workflow_id: str, step_number: int):
        return {'executed': True}

    async def query_knowledge_graph(question: str):
        return {'answer': 'data'}

    async def ask_intelligence_question(question: str, persona: str = None):
        return {'insight': 'data'}

    return {
        'get_transcripts': get_transcripts,
        'get_transcript': get_transcript,
        'get_analysis_by_transcript': get_analysis_by_transcript,
        'get_plan_by_transcript': get_plan_by_transcript,
        'get_workflows_for_plan': get_workflows_for_plan,
        'execute_workflow_step': execute_workflow_step,
        'query_knowledge_graph': query_knowledge_graph,
        'ask_intelligence_question': ask_intelligence_question
    }


# ============================================================================
# Test Cases for Tool Configuration Loading
# ============================================================================

class TestToolConfigLoading:
    """Test loading and parsing of tool configuration from YAML."""

    def test_load_config_from_file(self, temp_config_file):
        """Test loading tool configuration from YAML file."""
        # This will be implemented by get_tool_config() function
        from src.infrastructure.config.tool_registry import get_tool_config

        config = get_tool_config(temp_config_file)

        assert config is not None
        assert 'roles' in config
        assert 'tool_registry' in config
        assert 'advisor' in config['roles']
        assert 'leadership' in config['roles']

    def test_config_caching(self, temp_config_file):
        """Test that config is cached after first load."""
        from src.infrastructure.config.tool_registry import get_tool_config, _clear_cache

        _clear_cache()
        config1 = get_tool_config(temp_config_file)
        config2 = get_tool_config(temp_config_file)

        # Should be the same object (cached)
        assert config1 is config2

    def test_invalid_yaml_raises_error(self):
        """Test that invalid YAML raises appropriate error."""
        from src.infrastructure.config.tool_registry import get_tool_config, _clear_cache

        _clear_cache()  # Clear cache before test

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [[[")
            invalid_path = f.name

        try:
            with pytest.raises(yaml.YAMLError):
                get_tool_config(invalid_path)
        finally:
            os.unlink(invalid_path)

    def test_missing_config_file_raises_error(self):
        """Test that missing config file raises FileNotFoundError."""
        from src.infrastructure.config.tool_registry import get_tool_config, _clear_cache

        _clear_cache()  # Clear cache before test

        with pytest.raises(FileNotFoundError):
            get_tool_config('/nonexistent/config.yaml')

    def test_missing_roles_section_raises_error(self):
        """Test that config without 'roles' section raises ValueError."""
        from src.infrastructure.config.tool_registry import get_tool_config, _clear_cache

        _clear_cache()  # Clear cache before test

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'tool_registry': {}}, f)
            invalid_path = f.name

        try:
            with pytest.raises(ValueError, match="missing 'roles' section"):
                get_tool_config(invalid_path)
        finally:
            os.unlink(invalid_path)


# ============================================================================
# Test Cases for Tool List Extraction
# ============================================================================

class TestToolListExtraction:
    """Test extracting tool lists for specific role+mode combinations."""

    def test_get_tools_for_advisor_borrower(self, temp_config_file):
        """Test getting tool list for advisor+borrower mode."""
        from src.infrastructure.config.tool_registry import get_tools_for_role_mode

        tools = get_tools_for_role_mode('advisor', 'borrower', temp_config_file)

        assert isinstance(tools, list)
        assert 'get_transcripts' in tools
        assert 'get_transcript' in tools
        assert 'execute_workflow_step' in tools
        assert len(tools) == 6

    def test_get_tools_for_advisor_selfreflection(self, temp_config_file):
        """Test getting tool list for advisor+selfreflection mode."""
        from src.infrastructure.config.tool_registry import get_tools_for_role_mode

        tools = get_tools_for_role_mode('advisor', 'selfreflection', temp_config_file)

        assert isinstance(tools, list)
        assert 'get_transcripts' in tools
        assert 'query_knowledge_graph' in tools
        # Should NOT have execute_workflow_step (only in borrower mode)
        assert 'execute_workflow_step' not in tools
        assert len(tools) == 3

    def test_get_tools_for_leadership(self, temp_config_file):
        """Test getting tool list for leadership role."""
        from src.infrastructure.config.tool_registry import get_tools_for_role_mode

        tools = get_tools_for_role_mode('leadership', 'borrower', temp_config_file)

        assert isinstance(tools, list)
        assert 'ask_intelligence_question' in tools
        assert 'query_knowledge_graph' not in tools
        # Leadership should NOT have execute_workflow_step
        assert 'execute_workflow_step' not in tools

    def test_invalid_role_raises_error(self, temp_config_file):
        """Test that invalid role raises ValueError."""
        from src.infrastructure.config.tool_registry import get_tools_for_role_mode

        with pytest.raises(ValueError, match="Role 'invalid_role' not found"):
            get_tools_for_role_mode('invalid_role', 'borrower', temp_config_file)

    def test_invalid_mode_raises_error(self, temp_config_file):
        """Test that invalid mode raises ValueError."""
        from src.infrastructure.config.tool_registry import get_tools_for_role_mode

        with pytest.raises(ValueError, match="Mode 'invalid_mode' not found"):
            get_tools_for_role_mode('advisor', 'invalid_mode', temp_config_file)


# ============================================================================
# Test Cases for Tool Function Resolution
# ============================================================================

class TestToolFunctionResolution:
    """Test resolving tool names to actual function objects."""

    def test_resolve_tool_names_to_functions(self, temp_config_file, mock_tool_functions):
        """Test mapping tool names to actual function objects."""
        from src.infrastructure.config.tool_registry import resolve_tools_to_functions

        tool_names = ['get_transcripts', 'get_transcript', 'execute_workflow_step']
        functions = resolve_tools_to_functions(tool_names, mock_tool_functions)

        assert isinstance(functions, list)
        assert len(functions) == 3
        assert callable(functions[0])
        assert callable(functions[1])
        assert callable(functions[2])

    def test_unknown_tool_raises_error(self, mock_tool_functions):
        """Test that unknown tool name raises ValueError."""
        from src.infrastructure.config.tool_registry import resolve_tools_to_functions

        tool_names = ['get_transcripts', 'unknown_tool']

        with pytest.raises(ValueError, match="Unknown tool: unknown_tool"):
            resolve_tools_to_functions(tool_names, mock_tool_functions)

    def test_empty_tool_list_returns_empty_functions(self, mock_tool_functions):
        """Test that empty tool list returns empty function list."""
        from src.infrastructure.config.tool_registry import resolve_tools_to_functions

        functions = resolve_tools_to_functions([], mock_tool_functions)

        assert isinstance(functions, list)
        assert len(functions) == 0


# ============================================================================
# Test Cases for Tool Filters
# ============================================================================

class TestToolFilters:
    """Test tool filtering rules."""

    def test_get_tool_filters_for_advisor(self, temp_config_file):
        """Test getting tool filters for advisor role."""
        from src.infrastructure.config.tool_registry import get_tool_filters

        filters = get_tool_filters('advisor', 'borrower', temp_config_file)

        assert filters is not None
        assert filters['workflow_types'] == ['BORROWER']
        assert filters['access_level'] == 'advisor'

    def test_get_tool_filters_for_leadership(self, temp_config_file):
        """Test getting tool filters for leadership role."""
        from src.infrastructure.config.tool_registry import get_tool_filters

        filters = get_tool_filters('leadership', 'borrower', temp_config_file)

        assert filters is not None
        assert 'BORROWER' in filters['workflow_types']
        assert 'ADVISOR' in filters['workflow_types']
        assert 'COMPLIANCE' in filters['workflow_types']
        assert filters['access_level'] == 'leadership'

    def test_mode_without_filters_returns_empty_dict(self):
        """Test that mode without filters returns empty dict."""
        from src.infrastructure.config.tool_registry import get_tool_filters, _clear_cache

        _clear_cache()  # Clear cache before test

        # Create config without filters for a mode
        config = {
            'roles': {
                'test_role': {
                    'modes': {
                        'test_mode': {
                            'prompt_file': 'test.md',
                            'tools': ['get_transcripts']
                            # No tool_filters
                        }
                    }
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            filters = get_tool_filters('test_role', 'test_mode', config_path)
            assert filters == {}
        finally:
            os.unlink(config_path)


# ============================================================================
# Test Cases for Integration with Agent Creation
# ============================================================================

class TestAgentToolIntegration:
    """Test integration of tool registry with agent creation."""

    def test_get_complete_tool_config_for_agent(self, sample_tool_config, mock_tool_functions):
        """Test getting complete tool configuration for agent creation."""
        from src.infrastructure.config.tool_registry import get_agent_tool_config, _clear_cache

        _clear_cache()  # Clear cache before test

        # Create temp config file from sample
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_tool_config, f)
            config_path = f.name

        try:
            config = get_agent_tool_config('advisor', 'borrower', config_path, mock_tool_functions)

            assert 'tool_names' in config
            assert 'tool_functions' in config
            assert 'tool_filters' in config

            assert isinstance(config['tool_names'], list)
            assert isinstance(config['tool_functions'], list)
            assert isinstance(config['tool_filters'], dict)

            # Verify tool names match tool functions
            assert len(config['tool_names']) == len(config['tool_functions'])

            # Verify all functions are callable
            for func in config['tool_functions']:
                assert callable(func)
        finally:
            os.unlink(config_path)
