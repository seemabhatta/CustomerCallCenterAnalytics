# Role-Based Agent System

## Overview

The system now supports role-based agents that use the same SimpleChatView UI but with different prompts and behavior based on the user's role.

## Architecture

### Components

1. **Role-Based Agent Factory** (`src/call_center_agents/role_based_agent.py`)
   - Creates agents with role-specific prompts
   - Maintains same tool set across roles
   - Loads prompts from `prompts/{role}_agent/system_prompt.txt`

2. **Updated API** (`server.py`)
   - Added `role` parameter to AdvisorChatRequest
   - Defaults to "advisor" for backward compatibility

3. **Updated Service** (`src/services/advisor_service.py`)
   - Accepts role parameter
   - Creates appropriate agent based on role

### Available Roles

#### Advisor Role (`role: "advisor"`)
- **Purpose**: Front-line staff helping with borrower workflows
- **Focus**: Operational execution, step-by-step guidance
- **Prompt**: `prompts/advisor_agent/system_prompt.txt`
- **Behavior**:
  - Helps execute workflows
  - Provides operational guidance
  - Manages individual customer cases

#### Leadership Role (`role: "leadership"`)
- **Purpose**: Executive insights and strategic decision-making
- **Focus**: Trends, patterns, strategic analysis
- **Prompt**: `prompts/leadership_agent/system_prompt.txt`
- **Behavior**:
  - Provides strategic insights
  - Analyzes patterns across calls
  - Focuses on metrics and trends

## Usage

### Single Universal Endpoint

**One endpoint handles all roles:**

```bash
POST /api/v1/advisor/chat
```

### Request Format

```json
{
  "advisor_id": "user_identifier",
  "message": "Your question or request",
  "role": "advisor",  // "advisor", "leadership", or any future role
  "session_id": "optional_session_id",
  "transcript_id": "optional_transcript_context",
  "plan_id": "optional_plan_context"
}
```

### Examples

#### Advisor Usage
```json
{
  "advisor_id": "advisor_001",
  "message": "Show me pending workflows for the last call",
  "role": "advisor"
}
```

#### Leadership Usage
```json
{
  "advisor_id": "exec_001",
  "message": "What are the customer satisfaction trends this month?",
  "role": "leadership"
}
```

#### Future Role Usage
```json
{
  "advisor_id": "user_001",
  "message": "Your request here",
  "role": "new_role"  // Any role with prompts/{new_role}_agent/system_prompt.txt
}
```

## Frontend Integration

The SimpleChatView can be used for both roles by:

1. **Setting the role parameter** based on user type
2. **Using the same UI components** - no changes needed
3. **Different behavior** automatically based on role-specific prompts

### Example Frontend Usage

```typescript
// Single function handles all roles
const sendChatMessage = async (userId: string, message: string, userRole: string) => {
  const request = {
    advisor_id: userId,
    message: message,
    role: userRole  // "advisor", "leadership", "supervisor", etc.
  };

  // Same API call, role-specific behavior
  return await chatService.sendMessage(request);
};

// Usage examples
await sendChatMessage("advisor_123", "Show pending workflows", "advisor");
await sendChatMessage("exec_456", "Performance trends", "leadership");
await sendChatMessage("sup_789", "Team metrics", "supervisor");  // Future role
```

## Adding New Roles

To add a new role:

1. **Create prompt file**: `prompts/{new_role}_agent/system_prompt.txt`
2. **Update agent factory**: Add role to `agent_names` mapping in `create_role_based_agent()`
3. **Test integration**: Use the test script to verify functionality

## Testing

Use the provided test script:

```bash
python3 test_role_integration.py
```

This tests both advisor and leadership roles to ensure proper integration.

## Benefits

1. **Single Endpoint**: One URL for all user types - no confusion
2. **Code Reuse**: Same UI and API for all roles
3. **Prompt Separation**: Easy to update role behavior without code changes
4. **Scalable**: Easy to add new roles without new endpoints
5. **Maintainable**: Clear separation between role logic and implementation
6. **Type Safety**: Same request/response models across roles
7. **Simplified API**: No need to remember different endpoints for different roles

## Migration from Multiple Endpoints

**Old (Complex):**
- `/api/v1/advisor/chat` for advisors
- `/api/v1/leadership/chat` for leadership
- `/api/v1/supervisor/chat` for supervisors (hypothetical)

**New (Simple):**
- `/api/v1/advisor/chat` with `role` parameter for everyone

This reduces API complexity and makes the system much easier to understand and maintain.