# SPEC-01 Phase 1 Implementation — Issues & Handoff

Session: 2026-05-08
Status: Phase 1 Partial — implementation complete in code, NOT verified at runtime, structural defects outstanding
Decision: preserve work, halt for next session

---

## 1. What was attempted

Phase 1 P0 critical path per audit-report.md:
- Gap 1: audit_logs full module + `@audit` decorator + apply on accounts use cases
- Gap 2: design_sessions use cases (create/transition/decision/detail/retry/rerun/switch_mode) + repos + API + state_machine wiring
- Gap 3: Multi-tenant ORM auto-filter (TenantAwareManager + bypass())
- Gap 4: INV-01-03 enforcement on conversations.ChatMessage (domain validator + DB CHECK constraint via RunSQL)

Methodology requested: TDD. Test files were created but not executed (no venv in shell).

---

## 2. Files added/modified (by agent, this session — UNCOMMITTED)

### audit_logs
- `apps/audit_logs/application/{ports.py, dtos.py, use_cases/{record_audit_log.py, query_audit_logs.py}}` (new)
- `apps/audit_logs/infrastructure/repositories/audit_log_repository.py` (new)
- `apps/audit_logs/infrastructure/orm/{models.py, migrations/0001_initial.py}` (modified/new)
- `apps/audit_logs/presentation/{views.py, urls.py}` (new)
- `apps/audit_logs/tests/{unit, integration}/...` (new — 4 test files)

### design_sessions
- `apps/design_sessions/application/use_cases/{create_session, transition_session, record_decision, get_session_detail, retry_step, rerun_from_step, switch_mode}.py` (new)
- `apps/design_sessions/infrastructure/repositories/{session_repository, brief_repository, decision_log_repository}.py` (new)
- `apps/design_sessions/infrastructure/orm/{models.py, migrations/0001_initial.py}` (modified/new)
- `apps/design_sessions/presentation/{views.py, urls.py, project_session_urls.py}` (new/modified)
- `apps/design_sessions/domain/entities.py` (modified — re-exports enums from value_objects)
- `apps/design_sessions/tests/integration/...` (new — 6 test files)

### conversations
- `apps/conversations/domain/entities.py` (modified — INV-01-03 validator)
- `apps/conversations/infrastructure/orm/{models.py, migrations/0001_initial.py}` (modified — RunSQL CHECK constraint)
- `apps/conversations/tests/integration/test_chat_message_invariant.py` (new)

### shared
- `shared/application/decorators/audit.py` (new)
- `shared/infrastructure/orm/{managers.py, base_model.py}` (new/modified)
- `shared/infrastructure/orm/tests/test_tenant_aware_manager.py` (new)

### config
- `config/urls_user.py` (modified — mount design_sessions URLs)

### accounts (decorator applied)
- `apps/accounts/application/use_cases/{authenticate, register_user, update_profile}.py` (modified — `@audit` decorator)

---

## 3. Outstanding structural defects (BLOCKERS for runtime)

### 3.1 Pre-existing duplicate enums (root cause)
- `apps/design_sessions/domain/value_objects.py` defines `SessionStatus`, `SessionMode`, `PipelineStep` with rich behavior (`_TRANSITIONS`, `can_transition_to`, `get_session_status`, `get_step_range`).
- `apps/design_sessions/domain/entities.py` originally redefined the same enums with simpler bodies. This session changed entities.py to re-export from value_objects.
- **Defect**: value_objects.py's `SessionStatus._TRANSITIONS = {QUEUED: {RESEARCHING, FAILED}, ...}` is declared inside the Enum class body. At class-body time `QUEUED` is a string `"queued"`, not an enum member. Python's Enum metaclass surfaces `_TRANSITIONS` as a dict, but Pyright (and at runtime, lookups by enum member) treat the dict as an Enum-member candidate. This causes:
  - Type union `dict[int, SessionStatus] | Literal[1..17]` for PipelineStep, breaking `<`, `>`, `/` operators
  - Lookups like `_TRANSITIONS[self]` may KeyError at runtime when keys are strings but caller passes enum members

**Fix recommendation (next session)**: Move `_TRANSITIONS` and `_STEP_RANGES` OUT of the Enum class body into module-level dicts indexed by enum member after class definition. Convert `can_transition_to`, `get_session_status`, `get_step_range` to read from those module-level constants. This is a ~30-line refactor in `value_objects.py`.

### 3.2 Type mismatch in transition_session.py
- Line 74-81: `StateTransitionError(current_state=session.status, ...)` — exception expects `current_state: str`, but `session.status` is a `SessionStatus` enum.
- **Fix**: pass `session.status.value` (string) instead.

### 3.3 PipelineStep arithmetic in design_sessions/presentation/views.py
- Lines 177, 179, 193: `<`, `>`, `/` against PipelineStep — assumes int comparison but Pyright sees the broken Enum union (consequence of 3.1).
- **Fix**: after 3.1 is fixed, use `step.value` for arithmetic, or revisit the helper to use the proper API (`PipelineStep.get_session_status()` etc.).

### 3.4 update_profile.py audit decorator extractor
- Earlier diagnostic flagged "missing `identifier` parameter at line 50". Subsequent fix-pass agent reported the line was structurally sound. **Needs runtime verification** (pytest run).

### 3.5 Test executability
- All test files exist but were never executed.
- Imports such as `from apps.audit_logs.application.dtos import AuditLogEntryDTO` resolve at filesystem level but Pyright cannot validate (env has no venv). Runtime verification pending.

### 3.6 AuditLog.Meta inheritance
- Fixed in second pass: `class Meta(TimestampedModel.Meta): abstract = False`. Verify this did not break the abstract-model migration logic (Django sometimes complains about explicit abstract=False overrides).

### 3.7 error_handler import in audit_logs/presentation/views.py
- Was imported as `error_handler` (does not exist). Replaced with `custom_exception_handler` + local `_to_response()` helper. The helper mutates the dict via `.pop()` — minor but flagged.

---

## 4. Items NOT yet implemented (Phase 1 scope items still open)

- TenantAwareManager applied to all business models — needs audit pass: which models inherit `TenantScopedModel`? A startup system check was supposed to be added; verify presence and run on boot.
- Audit decorator failure-recording allowlist usage — only the success path was applied to accounts use cases.
- design_sessions API endpoints — created but Permission classes (Tenant Admin / Workspace Lead / Designer / Viewer matrix per REQ-01-TENANT-004) not wired to a concrete role decorator.
- structured-logging context injection (REQ-01-ASYNC-003) — out of Phase 1, but flagged for Phase 2.

---

## 5. Verification gates NOT executed (require venv)

- `python manage.py makemigrations --check --dry-run`
- `python manage.py migrate --plan`
- `pytest apps/audit_logs apps/design_sessions apps/conversations apps/accounts shared -x -q`
- `python manage.py check`

These must run in next session to confirm runtime correctness.

---

## 6. Recommended next-session order of operations

1. **Activate venv** (`conda activate agent01`) and confirm Django + pytest available.
2. **Fix value_objects.py Enum structure** (defect 3.1) — module-level constants, methods read from them.
3. **Re-run** `python manage.py check` to find any remaining import errors.
4. **Fix** transition_session.py (3.2) and views.py (3.3) — these become straightforward after 3.1.
5. **Run migrations** locally: `python manage.py makemigrations` then `migrate` against a clean dev DB.
6. **Run pytest** scoped to changed apps; collect failures, fix in batch (per user's whole-system rule).
7. **Verify accounts regression** — the `@audit` decorator must not break existing accounts tests.
8. **Run import-linter** if a tools/import_linter.toml is added in this round (P1 deferred — optional).
9. Decide whether to commit (single squashed commit recommended) or split per-module.

---

## 7. Files NOT touched (legacy preserved per user direction)

- `app/**` (legacy FastAPI) — entirely untouched
- `crawling_data/**`, `static/**`, `templates/**`, `docs/**` — untouched
- `app/services/pipeline_orchestrator.py`, `app/services/image_generation_service.py`, `app/services/ai_research_service.py` — untouched (AC-01-STRUCT-001..003 deferred)

---

## 8. Risks if shipping current state without next-session fixes

- **High**: design_sessions use cases will likely raise at runtime due to enum type mismatch (3.1, 3.2).
- **High**: design_sessions API endpoints will return 500 on first invocation.
- **Medium**: TenantAwareManager not yet enforced on every business model (REQ-01-TENANT-001 partial).
- **Medium**: audit decorator's failure-recording path untested.
- **Low**: INV-01-03 DB constraint is RunSQL-only (PostgreSQL); SQLite test DBs cannot validate it.

---

## 9. Decision log

| Decision | Rationale |
|----------|-----------|
| value_objects.py canonical for enums | Richer behavior (transitions). **Re-evaluate next session** — the broken `_TRANSITIONS` may justify reversing this and using entities.py simple enums + a separate `transitions.py` module |
| Audit decorator wraps inside `transaction.atomic()` | REQ-01-AUDIT-003 (rollback on failure) |
| TenantAwareManager via `objects` + `all_objects` escape hatch | Standard Django pattern; minimizes API surface change |
| INV-01-03 enforced at both domain + DB layers | Defense in depth per spec invariant strength |
| Phase 1 only; legacy app/ untouched | User-confirmed scope |
| No commit this session | User decision |

---

End of handoff document.
