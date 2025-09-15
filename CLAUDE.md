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