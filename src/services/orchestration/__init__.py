"""
Orchestration Module - Prefect-based pipeline automation

Provides end-to-end orchestration from transcript to execution:
- Main pipeline flow: transcript → analysis → plan → workflows → execution
- Human-in-the-loop approval workflows
- NO FALLBACK LOGIC - fails fast on any errors
- Complete audit trail and monitoring
"""