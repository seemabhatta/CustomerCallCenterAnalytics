# Prompt Configuration System

## Overview

The prompt configuration system uses YAML to externalize role/mode prompt mappings, making it easy to manage and update agent configurations without code changes.

## Configuration File

**Location**: `config/prompt_mapping.yaml`

### Structure

```yaml
roles:
  advisor:
    display_name: "Mortgage Advisor Assistant"
    description: "AI assistant for mortgage advisors"
    modes:
      borrower:
        prompt_file: "prompts/advisor_agent/borrower_system_prompt.md"
        description: "Helps advisors with borrower workflows"
        icon: "User"
      selfreflection:
        prompt_file: "prompts/advisor_agent/selfreflection_system_prompt.md"
        description: "Helps advisors reflect on performance"
        icon: "CheckCircle"

settings:
  default_mode: "borrower"
  default_model: "gpt-4o-mini"
```

## Usage

### Loading Configuration

```python
from call_center_agents.role_based_agent import load_prompt_config

config = load_prompt_config()  # Cached after first load
```

### Creating Agents

```python
from call_center_agents.role_based_agent import create_role_based_agent

# Same API as before - now uses configuration
advisor_agent = create_role_based_agent("advisor", "borrower")
leadership_agent = create_role_based_agent("leadership", "selfreflection")
```

### Getting Prompt Information

```python
from call_center_agents.role_based_agent import (
    get_prompt_file_for_role_mode,
    get_agent_display_name
)

# Get prompt file path
prompt_file = get_prompt_file_for_role_mode("advisor", "borrower")
# Returns: "prompts/advisor_agent/borrower_system_prompt.md"

# Get display name
display_name = get_agent_display_name("advisor", "selfreflection")
# Returns: "Mortgage Advisor Assistant (Selfreflection Mode)"
```

## Adding New Roles/Modes

1. **Add to YAML configuration**:
   ```yaml
   roles:
     supervisor:  # New role
       display_name: "Supervisor Assistant"
       modes:
         borrower:
           prompt_file: "prompts/supervisor_agent/borrower_system_prompt.md"
           description: "Supervisory oversight for borrower workflows"
   ```

2. **Create prompt file**:
   - Create directory: `prompts/supervisor_agent/`
   - Add prompt file: `borrower_system_prompt.md`

3. **Use immediately**:
   ```python
   supervisor_agent = create_role_based_agent("supervisor", "borrower")
   ```

## Error Handling

The system provides comprehensive error handling:

- **Missing configuration file**: Falls back to legacy path construction
- **Invalid role/mode**: Raises `ValueError` with available options
- **Missing prompt file**: Raises `FileNotFoundError`

## Backward Compatibility

- All existing code continues to work unchanged
- Legacy path construction (`prompts/{role}_agent/{mode}_system_prompt.md`) still works as fallback
- Environment variables for model selection still override configuration

## Configuration Validation

The system validates:

- Required YAML structure
- Existence of prompt files
- Valid role/mode combinations

## Benefits

1. **Centralized Management**: All prompt mappings in one place
2. **Easy Extension**: Add new roles/modes without code changes
3. **Documentation**: YAML serves as living documentation
4. **Flexibility**: Support for metadata, descriptions, icons
5. **Future-Proof**: Easy to add new configuration options

## Future Enhancements

- UI integration to read available modes from configuration
- Hot-reloading of configuration changes
- Environment-specific configurations (dev/staging/prod)
- Validation rules and constraints