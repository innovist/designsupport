# SPEC-01 Gap Audit Report

Generated: 2026-05-08
Auditor: Explore agent (read-only)
SPEC version: 0.1.0 (draft)
Implementation status: ~15%

## A. Module-by-Module Status

### A.1 accounts — COMPLETE
Domain, application (4 use cases + DTOs + container), infrastructure (Argon2id + JWT + repo), presentation (4 endpoints) all present. Tests scaffold only.

### A.2 design_sessions — CORE COMPLETE / PARTIAL
- state_machine.py (413 LOC) implements 9 states + 17-step mapping + decision logging.
- ports.py defined.
- ORM models present.
- **Gaps (P0)**: no use cases (CreateSession, TransitionSession, RecordDecision, GetSessionDetail, RetryStep, RerunFromStep), no repositories, no API routes.

### A.3 workspaces — PARTIAL
- ports.py complete, ORM models present.
- **Gaps (P0)**: 5 use cases (create_workspace, add_member, remove_member, change_role, list_user_workspaces) missing; repos missing; endpoints missing.

### A.4 audit_logs — MINIMAL
- Domain entity + ORM model present.
- **Gaps (P0)**: ports.py missing; record_audit_log, query_audit_logs use cases missing; decorator missing; repository missing.

### A.5 design_projects — MINIMAL
- Domain entity + ORM model present.
- **Gaps (P0)**: 3 use cases (create, list, archive) missing; repository missing; endpoints missing.

### A.6 conversations — MINIMAL
- Domain entities (Conversation, ChatMessage with evidence_refs) present.
- **Gaps (P0)**: ports.py missing; 3 use cases missing; repository missing; INV-01-03 (evidence_refs OR is_hypothesis) not enforced.

### A.7 user_assets — MINIMAL
- Domain entities present; shared object_storage has upload_immutable + SHA-256.
- **Gaps (P0)**: ports.py missing; 4 use cases missing; repository missing; upload flow not wired; REQ-01-SKETCH-002 overwrite rejection not enforced end-to-end.

## B. Cross-Cutting

### B.1 Multi-tenancy — PARTIAL
- TenantScopedModel abstract class + TenantMiddleware + TenantContext present.
- **Gap (P0/P1)**: no QuerySet manager auto-filtering by tenant_id/workspace_id (REQ-01-TENANT-001 violation).

### B.2 Audit decorator — MISSING (P0)
- shared/application/decorators/ empty.

### B.3 Sketch immutability — PARTIAL
- Storage layer logic exists; not wired to a use case (P0).

### B.4 State machine — IMPLEMENTED, NOT WIRED (P0)
- No use case calls orchestrator; INV-01-07 semantics (decision_required + current_step) not asserted.

### B.5 Async pipeline — MINIMAL (P0)
- celery_app.py present; no tasks defined; structured logging not injected with task/session context.

### B.6 Hardcoding guard — PASS
- No hardcoded API keys in apps/*. Model names appear only in seed files and tests (acceptable).

### B.7 Mock/Placeholder/Fallback — PASS (no false fallbacks; only empty directories awaiting implementation).

### B.8 REQ-01-STRUCT — PARTIAL
- Code review passes for STRUCT-001/003/007.
- **Gap (P1)**: tools/import_linter.toml missing; CI checks not wired.

### B.9 Legacy migration — DEFERRED
- Legacy `app/` retained intact; user opted for parallel coexistence (no migration in this run).

## C. CONSISTENCY-REVIEW issues affecting SPEC-01
- DecisionLog vs ConceptDecision (RUN-deferred, not blocking).
- Auto-mode uncertainty threshold (REQ-01-ORCH-005) — to be defined when state machine is wired.

## D. Prioritized Gaps

### Phase 1 scope (selected by user)
P0-1. audit_logs full module + decorator + decorator application across all use cases
P0-2. design_sessions use cases (create, transition, record_decision, get_detail, retry_step, rerun_from_step), repository, API endpoints — wire state_machine
P0-3. Multi-tenant ORM auto-filtering (TenantAwareQuerySet + manager + applied to all business models)
P0-4. INV-01-03 enforcement at conversations.ChatMessage save path (validator + DB constraint)

### Phase 2/3 (deferred)
- workspaces, design_projects, conversations (full), user_assets full implementations
- Celery task definitions, async pipeline, structured-logging context injection
- import-linter config, CI guards, @MX tags, 85% coverage

## E. Risks
1. Tenant data leakage if ORM auto-filter not enforced (P0)
2. Audit trail absence — compliance failure (P0)
3. State machine inert until wired (P0)
4. Sketch overwrite path — INV-01-01 violation (deferred to Phase 2)
5. Async API blocking — operational (deferred to Phase 2)

## F. Decision (this session)
- Phase 1 only.
- Legacy `app/` untouched.
- TDD mode (per quality.yaml): tests first per use case.
