# Research: SPEC-05-UX-WORKSPACE

Codebase analysis for user workspace UI, layout, interactions, and i18n.

## Current Frontend

### Template Structure

**Templates:** `templates/` directory
- `templates/pages/new_session.html` - New session creation page
- `templates/pages/settings.html` - Settings page
- `templates/partials/dashboard/session-modal.html` - Session modal

**Static Assets:** `static/` directory
- `static/js/pages/dashboard.js` + sub-modules (crawlers, init, overview, projects, reports, sessions, state)
- `static/js/pages/home.js` - Home page
- `static/js/pages/library.js` - Library page
- `static/js/pages/new_session.js` - New session page
- `static/js/i18n.js` - Internationalization
- `static/i18n/en.json`, `ko.json`, `zh-CN.json`, `zh-TW.json` - Translation files

### Current Dashboard Architecture

**Dashboard modules** (vanilla JS):
- `dashboard/state.js` - State management
- `dashboard/overview.js` - Overview panel
- `dashboard/projects.js` - Project management
- `dashboard/sessions.js` - Session management
- `dashboard/crawlers.js` - Crawler management
- `dashboard/reports.js` - Report viewer

### Current i18n

**4 languages supported:** ko, en, zh-CN, zh-TW
- Matches SPEC-05 language requirements
- Translation files exist but content completeness unknown

### SPEC-05 Target Layout

**3-Panel Layout:**
1. Project Navigator (left sidebar)
2. Design Studio - 7 Board system (center)
3. Decision Panel (right sidebar)

**7 Boards in Design Studio:**
1. Purpose Input Board
2. Trend & Knowledge Board
3. Concept Board
4. Reference Search Board
5. Sketch Input Board
6. Generation Board
7. Spec Builder Board

### Current vs Target UI

| Component | Current | SPEC-05 Target | Gap |
|-----------|---------|----------------|-----|
| Layout | Single-page dashboard | 3-panel workspace | Major restructure |
| Design boards | None | 7-board system | Entirely new |
| Sketch input | None | 3-split (Original/Interpretation/Actions) | New |
| Reference search | None | 3-split (Source Clusters/Grid/Analysis) | New |
| Spec builder | Report viewer | Decision record viewer | Repurpose |
| Loading | Unknown | Skeleton loading (spinner forbidden) | Verify/enforce |
| Navigation | Tab-based | Project-based sidebar | Major change |

### SPEC-05 UI Components

#### Sketch Input Board (3-split)
- Original panel: User sketch display (immutable)
- Interpretation panel: AI analysis of sketch
- Actions panel: preserve_original / expand_concept controls

#### Reference Search UI (3-split)
- Source Clusters panel: Grouped by source/provider
- Grid panel: Image grid with license badges
- Analysis panel: Selected reference details

#### Spec Builder
- Decision record viewer (not editor)
- Shows all decisions made during design session
- Links to evidence/references for each decision

### UX Requirements

**Skeleton Loading (MANDATORY):**
- Spinner forbidden for content loading
- Skeleton placeholders during API calls
- Progressive content reveal

**WCAG 2.1 AA Compliance:**
- Keyboard navigation
- Screen reader support
- Color contrast ratios
- Focus indicators

**17-Step to Screen Mapping (SPEC-05 §5.1):**

| Step | Screen/Board |
|------|-------------|
| 1. Purpose input | Purpose Input Board |
| 2. Trend research | Trend & Knowledge Board |
| 3. Knowledge structuring | Trend & Knowledge Board |
| 4. Trend analysis | Trend & Knowledge Board |
| 5. Concept generation | Concept Board |
| 6. Concept selection | Concept Board |
| 7. Reference search | Reference Search Board |
| 8. Reference analysis | Reference Search Board |
| 9. Abstraction analysis | Concept Board |
| 10. Sketch input | Sketch Input Board |
| 11. Sketch analysis | Sketch Input Board |
| 12. Sketch prompt | Sketch Input Board |
| 13. Image generation | Generation Board |
| 14. Image review | Generation Board |
| 15. Comparison | Generation Board (sub-state) |
| 16. Spec writing | Spec Builder Board |
| 17. Review | Spec Builder Board |

## Key Gaps

| Gap | Severity | Description |
|-----|----------|-------------|
| No 3-panel layout | CRITICAL | Entire workspace layout is new |
| No design boards | CRITICAL | 7-board system is entirely new |
| No sketch input UI | HIGH | Sketch board with 3-split layout |
| No reference search UI | HIGH | Reference board with 3-split layout |
| No skeleton loading | HIGH | Spinner forbidden, skeleton required |
| Dashboard restructure | HIGH | Current dashboard → workspace layout |
| i18n completeness | MEDIUM | Verify all 4 language files have full coverage |
| WCAG compliance | MEDIUM | Accessibility audit needed |

## Frontend Technology

**Current:** Vanilla HTML/JS/CSS (no framework)
**SPEC-05 target:** Vanilla HTML/JS/CSS (consistent with current)

No framework migration needed. This is a positive alignment.

## Migration Strategy

1. **Phase 1:** Restructure dashboard to 3-panel layout
2. **Phase 2:** Build 7-board system with skeleton loading
3. **Phase 3:** Add Sketch Input and Reference Search boards
4. **Phase 4:** i18n key audit and WCAG compliance check
5. **Phase 5:** Connect boards to backend API endpoints
