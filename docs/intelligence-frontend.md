# Intelligence Frontend Dashboards

This document captures the new control tower dashboards that surface the GenAI + Prophet
intelligence layer exposed by the backend.

## Overview

- **ControlTowerView** (leadership): executive briefing, dollar impact snapshot, decision queue,
  and risk waterfall visualisations.
- **ServicingOpsView** (operations): queue outlook, SLA monitor, advisor heatmap, coaching alerts,
  and staffing balance.
- **MarketingView** (growth): high-value segments, campaign playbook, churn watchlist, journey
  insights, and message optimizer.
- **IntelligenceStatusBar**: shared banner displaying cache/health telemetry with controls for
  inspecting and clearing cached insights.

All views consume the dedicated `intelligenceApi` client and React Query hooks implemented in
`frontend/src/api/intelligenceHooks.ts`.

## Key Files

| File | Purpose |
| ---- | ------- |
| `frontend/src/api/client.ts` | REST client with typed helpers for 21 intelligence endpoints. |
| `frontend/src/api/intelligenceHooks.ts` | React Query hooks for leadership/servicing/marketing personas and cache controls. |
| `frontend/src/views/ControlTowerView.tsx` | Leadership dashboard. |
| `frontend/src/views/ServicingOpsView.tsx` | Servicing operations dashboard. |
| `frontend/src/views/MarketingView.tsx` | Marketing dashboard with churn/messaging tools. |
| `frontend/src/components/IntelligenceStatusBar.tsx` | Shared status banner + cache inspector. |
| `frontend/src/utils/formatters.ts` | Number/date formatting helpers reused across views. |
| `frontend/src/__tests__/intelligenceContracts.test.ts` | Type-level smoke test for query keys and contracts. |

## Navigation & UX

- New top-level tabs (`control-tower`, `servicing-intel`, `marketing-intel`) are available for
  leadership and admin roles via `App.tsx`.
- Each persona view renders the shared `IntelligenceStatusBar` (cache metrics, manual refresh,
  cache purge) and persona-specific cards.
- Message optimizer provides a simple form for submitting draft copy for GenAI refinement.

## Testing Notes

- `npm run build` currently fails because of pre-existing TypeScript errors around unused symbols
  in legacy views (`ExecutionTree`, `NewPipeline2View`, `WorkflowView`, etc.). The new intelligence
  modules type-check independently.
- `frontend/src/__tests__/intelligenceContracts.test.ts` provides compile-time coverage for the new
  contracts and query keys; hook-specific runtime tests will require bringing in a test harness
  (Vitest + Testing Library) in a follow-up.

## Follow-up Ideas

1. Introduce Vitest + Testing Library to exercise the persona views and hooks end-to-end.
2. Wire the message optimizer response into a reusable `CopyCard` component with copy-to-clipboard.
3. Extend the marketing dashboard with a micro-chart for ROI attribution once chart library is
   aligned (likely Recharts usage).
4. Audit `NewPipeline2View`/`ExecutionTree` to resolve existing TypeScript errors so CI builds can
   pass without suppressions.

