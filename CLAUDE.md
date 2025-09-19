# References

Vision - docs\01. vision_v2.md
HighLevel Achitecture - docs\02. HighLevelArchitecture.png
OPENAPI Cheatsheet- docs\OPENAI_CHEATSHEET.md
- OPENAI KEY is in .env file not in Environment
- always commit after fixing a bug
- Final Logical Architecture

  The Complete Flow:

  1. TRANSCRIPT (Input)
     └─> Raw customer conversation

  2. ANALYZE (Understanding)
     └─> LLM extracts: intent, urgency, risks, compliance issues

  3. PLAN (Strategy)
     └─> LLM generates high-level actions:
         • "Remove PMI for customer"
         • "Provide hardship assistance"
         • "Coach advisor on compliance"

  4. WORKFLOW (Tactical Breakdown)
     └─> LLM decomposes each action into detailed steps:
         • Step 1: Check LTV in Black Knight (navigate to...)
         • Step 2: Update escrow module (process...)
         • Step 3: Generate PMI letter (using template...)
         • Step 4: Send notification (via email to...)

  5. EXECUTE (Operations)
     └─> LLM selects tools + System executes:
         • Step 1 → ServicingSystemExecutor
         • Step 2 → ServicingSystemExecutor
         • Step 3 → DocumentGeneratorExecutor
         • Step 4 → EmailExecutor + CRMExecutor

  📊 What Each Layer Owns:

  | Layer    | Responsibility           | Output                      |
  |----------|--------------------------|-----------------------------|
  | Analyze  | Understand WHAT happened | Issues, risks, sentiment    |
  | Plan     | Decide WHAT to do        | Strategic actions           |
  | Workflow | Define HOW to do it      | Detailed steps with context |
  | Execute  | DO it with tools         | Completed actions           |

  ✅ Core Principles Maintained:

  - Fully Agentic: LLM makes all decisions at each layer
  - No Hardcoding: No if-then-else logic or registries
  - Fail Fast: No fallbacks, fail if LLM can't decide
  - Clean Separation: Each layer has single responsibility

  🔄 Data Enrichment at Each Step:

  Transcript: "I want to remove PMI"
      ↓
  Analyze: {intent: "PMI_REMOVAL", urgency: "high", risk: "low"}
      ↓
  Plan: {action: "Process PMI removal request"}
      ↓
  Workflow: {steps: [{action: "Verify LTV", system: "Black Knight", path: "Loan > Details"}]}
      ↓
  Execute: {tool: "ServicingSystemExecutor", result: "LTV verified at 78%"}

  This is the clean, logical flow that transforms vague requests into executed actions!

- Pluggable Architecture
    -Instead of replacing existing executors, we're creating an extensible plugin architecture where the system can support hundreds of different executor types - both
    human-centric and system-centric.

  Key Design Principles for Executors

  1. Additive, Not Replacement
    - Keep all existing executors (email, CRM, disclosure, task, training)
    - Add mortgage-specific system executors (servicing_api, origination_api, title_api, etc.)
    - Future-proof for adding hundreds more executor types
  2. Generic Abstraction Layer
    - Replace vendor-specific names ("Black Knight MSP") with generic terms ("Mortgage Servicing System")
    - Use industry-standard terminology that any mortgage professional would understand
    - Abstract away implementation details while keeping business logic clear
  3. Mixed Execution Models
    - Support both API calls (system-to-system) and human actions (emails, tasks)
    - Single workflow can combine multiple executor types
    - Example: API call to check PMI eligibility → Generate document → Email customer → Update CRM
  4. Pluggable Architecture Benefits
    - New executors can be added without modifying core logic
    - Each executor is self-contained with its own mock implementation
    - LLM agent intelligently routes to appropriate executor based on action context
    - Scalable to hundreds of specialized tools (credit bureaus, insurance providers, county records, etc.)

    Real-World Example

    For a PMI removal request:
    1. servicing_api - Check loan-to-value ratio
    2. appraisal_api - Get current property value
    3. compliance_api - Verify regulatory requirements
    4. document_api - Generate PMI removal letter
    5. email - Send confirmation to borrower
    6. crm - Log customer interaction
    7. accounting_api - Adjust monthly payment

    This approach makes the demo more realistic by showing how modern mortgage servicing combines automated system integrations with human touchpoints, all orchestrated
    by an intelligent LLM agent.
