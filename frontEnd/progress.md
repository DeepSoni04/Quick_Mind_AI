# QueryMind Frontend Rewrite — Progress Tracking

## Context

### 1. Current Stack
- **Framework**: React 19.2.8 (`react`, `react-dom`)
- **Build Tool**: Vite 8.2.0 with `@vitejs/plugin-react` 6.0.4
- **Language**: JavaScript (JSX, ES Modules), no TypeScript
- **Routing**: `react-router-dom` 7.18.2 is installed in `package.json` and currently configured in `src/App.jsx`
- **Icon Library**: `lucide-react` 1.31.0 is installed
- **Linter**: `oxlint` 1.75.0 (`.oxlintrc.json` present)
- **Styling**: Vanilla CSS (no Tailwind CSS installed). `src/index.css` contains 366 lines of custom CSS properties (indigo/purple palette), glassmorphism styles, and typography imports (Inter & JetBrains Mono). Component and page styles are in separate `.css` files.

### 2. Current Structure
```
frontEnd/
├── dist/
├── node_modules/
├── public/
│   └── favicon.svg
├── src/
│   ├── assets/
│   │   ├── hero.png
│   │   ├── react.svg
│   │   └── vite.svg
│   ├── components/
│   │   ├── Sidebar.css
│   │   └── Sidebar.jsx
│   ├── context/
│   │   └── AuthContext.jsx
│   ├── pages/
│   │   ├── AdminPage.css / AdminPage.jsx
│   │   ├── ChatPage.css / ChatPage.jsx
│   │   ├── DashboardPage.css / DashboardPage.jsx
│   │   ├── DatabasesPage.css / DatabasesPage.jsx
│   │   ├── HistoryPage.css / HistoryPage.jsx
│   │   ├── LoginPage.css / LoginPage.jsx
│   │   └── SettingsPage.css / SettingsPage.jsx
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── .gitignore
├── .oxlintrc.json
├── ANTIGRAVITY_FRONTEND_INSTRUCTIONS.md
├── index.html
├── package-lock.json
├── package.json
├── README.md
└── vite.config.js
```

### 3. Current Functionality Assessment
| Screen / Feature | Current Status | Notes |
|---|---|---|
| Screen 1: Login | PARTIALLY IMPLEMENTED | Basic email/password check with mock auth delay in `LoginPage.jsx`. Does not match spec styling, colors, logo, breathing orbs, or canvas. |
| Screen 2: Query Workspace | PARTIALLY IMPLEMENTED | `ChatPage.jsx` has a chat-style prompt input, but lacks the query composer (gradient rim, Enter/Shift+Enter handler, char counter), example pills with dot colors, and type detection. |
| Screen 3: Processing | NOT PRESENT | No 4-stage pipeline animation, canvas flow particles, stage timers (1500/3000/4500/5200ms), or status pingers. |
| Screen 4: Result | PARTIALLY IMPLEMENTED | `ChatPage.jsx` renders simple mock tables, but lacks the spec's 18-row dataset, staggered row animation, exact typography/palette, and action buttons. |
| Screen 5: Update Preview | NOT PRESENT | No before/after department diff card, 1800ms execution timer, or success state. |
| Screen 6: Delete Confirm | NOT PRESENT | No destructive action warning card, pulsing red dot, 2100ms delete timer, or success state. |
| Screen 7: Query History | PARTIALLY IMPLEMENTED | `HistoryPage.jsx` has a table with mock history, but does not match spec's row card design, badges (select/update/delete), or rerun-through-processing click handler. |
| Screen 8: Saved Queries | NOT PRESENT | Current `DashboardPage.jsx` shows generic metrics and charts instead of the 6-card Saved Queries grid. |
| Screen 9: Connections | PARTIALLY IMPLEMENTED | `DatabasesPage.jsx` has database cards and an add modal, but does not match the active connection card (MongoDB, stats grid, Manage toggle) and add slot. |
| Screen 10: Add Connection | PARTIALLY IMPLEMENTED | Basic modal exists in `DatabasesPage.jsx`, but lacks the standalone page layout, back link, static MongoDB type, and realistic test connection state machine. |
| Screen 11: Settings | PARTIALLY IMPLEMENTED | Form exists in `SettingsPage.jsx`, but does not match spec sections (Query Behaviour toggles/selects, Account with Heer Sachdev, About v0.1.0-alpha). |
| Sidebar Navigation | PARTIALLY IMPLEMENTED | 260px collapsible sidebar with 6 items; needs rewrite to 64px fixed sidebar, 5 specific nav items (Query, History, Saved, Connect, Settings), custom SVG icons, and crimson active indicator. |
| API / Data Layer | NOT PRESENT | Mock data is scattered inline in components; needs a unified service/data layer with async delay simulation. |

### 4. Existing Design vs. Spec
- **Current**: Indigo/violet primary (`#6366f1`), dark blue background (`#0a0a1a`), Inter and JetBrains Mono typography, standard glassmorphic card borders.
- **Spec**: High-contrast, hyper-refined dark theme:
  - Deep carbon background (`#080809`), sidebar (`#09090c`)
  - Primary accent: Crimson/magenta (`#b8274c`, `rgba(184,39,76,...)`)
  - Secondary accent: Ice blue (`#4a9eba`, `rgba(74,158,186,...)`)
  - Status colors: Emerald green (`#2a9d5c`), danger red (`#c0392b`, `#e74c3c`), warning amber (`#f39c12`)
  - Typography: Google Fonts `Oxygen` (300, 400, 700) and `Oxygen Mono` (400)
  - Full suite of CSS keyframes: `breathe`, `drift`, `slideUp`, `fadeRow`, `spinSlow`, `pingSlow`, `flowDot`, `successPop`, `nodeActivate`
  - Interactive Ambient Canvas particle network with 65 particles, 112px connection lines, cursor proximity glow, and bottom crimson radial bloom.

### 5. Proposed File Content Rewrite Plan
Staying strictly within the existing project structure without deleting any files or directories:
1. `src/index.css`: Rewrite with Oxygen font imports, exact hex/rgba CSS variables, CSS keyframe animations, and 3px custom scrollbar.
2. `src/components/Sidebar.jsx` & `Sidebar.css`: Rewrite to exact 64px layout, custom SVGs for Query/History/Saved/Connect/Settings, crimson active pill indicator, and bottom-pinned Settings.
3. `src/pages/LoginPage.jsx` & `LoginPage.css`: Rewrite to full Screen 1 specification (split panel, breathing ambient orbs, logo SVG, Oxygen typography, mock auth).
4. `src/pages/ChatPage.jsx` & `ChatPage.css`: Rewrite to host the Query Flow:
   - **Screen 2**: Query Workspace (composer, char counter, Enter/Shift+Enter, example pills, type detector).
   - **Screen 3**: Processing (4-node chain, flow particles, 1500/3000/4500/5200ms timers, stage text).
   - **Screen 4**: Result view (18-row mock dataset, staggered fade-in, status badge, Export/New Query buttons).
   - **Screen 5**: Update Preview view (before/after diff, 1800ms timer, success state).
   - **Screen 6**: Delete Confirm view (warning card, pulsing red dot, 2100ms timer, success state).
5. `src/pages/HistoryPage.jsx` & `HistoryPage.css`: Rewrite to Screen 7 specification (9 mock history items, type badges, rerun on click).
6. `src/pages/DashboardPage.jsx` & `DashboardPage.css`: Repurpose as **Screen 8: Saved Queries** (6 quick-access cards, click to rerun through processing).
7. `src/pages/DatabasesPage.jsx` & `DatabasesPage.css`: Rewrite as **Screen 9: Connections** & **Screen 10: Add Connection** (active connection card, Manage toggle, add-connection form with test connection state machine).
8. `src/pages/SettingsPage.jsx` & `SettingsPage.css`: Rewrite as **Screen 11: Settings** (Query Behaviour toggles/selects, Heer Sachdev account card, v0.1.0-alpha about section).
9. `src/pages/AdminPage.jsx`: Kept as a clean fallback or secondary view, preserving file structure.
10. `src/context/AuthContext.jsx` & `src/context/api.js`: Provide the unified data layer with async delays, error/loading states, and session persistence for settings.

### 6. Dependency Assessment
- **Existing**: `react` (19.2.8), `react-dom` (19.2.8), `react-router-dom` (7.18.2), `lucide-react` (1.31.0), `vite` (8.2.0).
- **Recommendation**: No new packages are needed. All icons can use `lucide-react` or the exact inline SVGs defined in the spec. Animations and particle systems will be built with vanilla CSS keyframes and HTML5 Canvas 2D API for maximum performance and fidelity.

---

## Phase Status

- [x] **Phase 0 — Inspection & Setup**: Context documented; repository inspected; approved by user.
- [x] **Phase 1 — Design System Foundation**: Google Fonts (Oxygen & Oxygen Mono) imported; full exact color palette & CSS keyframes defined in `src/index.css`; reusable `AmbientCanvas.jsx` component created with 65 particles, 112px connections, cursorInfluence, crimsonGlow, and loginGradients. Verified running cleanly on localhost:5173.
- [x] **Phase 2 — Navigation Shell**: 64px fixed Sidebar implemented with exact SVGs (Query, History, Saved, Connect, Settings), bottom-pinned Settings, and crimson active indicator (`#b8274c`, glow `0 0 8px rgba(184,39,76,0.6)`). All route transitions verified in browser subagent.
- [x] **Phase 3 — Login**: Screen 1 full visual & functional implementation. Concentric SVG logo, split glassmorphism panel, Ambient Canvas, breathing orbs, Oxygen typography, and mock auth submission verified in browser.
- [x] **Phase 4 — Query Workspace**: Screen 2 composer, char count, Enter/Shift+Enter keydown, example pills with color-coded dot badges (blue/amber/red), animated gradient rim, and type detection logic. Verified in browser subagent.
- [x] **Phase 5 — Processing**: Screen 3 implemented in ChatPage.jsx. 4-node chain (USER/QUERYMIND AI/MONGODB/RESULT) with real `setTimeout` stage timers (1500/3000/4500ms), `pingSlow` pulse dots, `flowDot` animated connectors, `nodeActivate` keyframe, and 5200ms auto-navigate to result/update-preview/delete-confirm based on query type.
- [x] **Phase 6 — Result / Update Preview / Delete Confirm**: Screens 4, 5, 6 implemented in ChatPage.jsx. 18-row student mock table with `fadeRow` staggered animation, Overdue/Pending badges. Update Preview with before/after diff, 1800ms spinner transition and `successPop` success state. Delete Confirm with pulsing red dot, 2100ms spinner, success state. All real timer-driven.
- [x] **Phase 7 — History & Saved**: Screen 7 (HistoryPage.jsx) with 9 history rows, type badges (select/update/delete), `fadeRow` stagger, click-to-rerun via sessionStorage + navigate. Screen 8 (DashboardPage.jsx repurposed) with 6 saved query cards, `slideUp` stagger, click-to-rerun.
- [x] **Phase 8 — Connections & Add Connection**: Screen 9 (ConnectionsScreen) with active MongoDB card, 4-tile stats grid, real Manage toggle showing/hiding Sync+Disconnect panel, dashed add-another slot. Screen 10 (AddConnectionScreen) with back link, 3 form fields, static MongoDB type, real `testConnection` state machine (testing→success/error banner), and Connect navigates to /connections.
- [x] **Phase 9 — Settings**: Screen 11 (SettingsPage.jsx) with custom 40×22px sliding Toggle components, select dropdowns for row-limit (50/100/250/500) and timeout (15/30/60/120s), Heer Sachdev account card, Analyst role badge, v0.1.0-alpha About section. All backed by `getSettings`/`updateSettings` mock API with session state.
- [x] **Phase 10 — Full QA Pass**: All 14 checks PASS in browser. Login flow, Processing 4-node pipeline, Result table, Update Preview diff, Delete Confirm, History, Saved Queries, Connections, Add Connection, Settings, Sidebar all verified live at localhost:5173.

---

## Open Questions

1. **Routing Mechanism**: `react-router-dom` (v7) is already present in `package.json` and `App.jsx`. Would you like us to continue using URL routing (`/login`, `/workspace`, `/history`, `/saved`, `/connections`, `/settings`), or do you prefer single-page state-based switching?
2. **File Placement for Components & API Layer**:
   - Per Section 1a (no new files/folders without approval), can we create:
     - `src/components/AmbientCanvas.jsx` for the reusable canvas particle system?
     - `src/context/api.js` for the unified mock API layer (or would you prefer `src/services/api.js`)?
     - `.env.example` in `frontEnd/` for `VITE_API_BASE_URL`?
   - For Screen 8 (Saved Queries) and Screen 10 (Add Connection): is repurposing `DashboardPage.jsx` for Saved Queries and housing Add Connection within `DatabasesPage.jsx` acceptable, or would you prefer new dedicated files `SavedQueriesPage.jsx` and `AddConnectionPage.jsx`?
3. **Add Connection Mock Test**: Section 6 Screen 10 asks: *"Ask me whether the mock test should always succeed, always fail, or randomly vary"*. Which behavior do you prefer? (Recommended: Succeed when fields are filled, fail if connection string is empty or contains "error").
4. **Settings Wire-Up**: In Screen 11, should the "Confirm before updates" and "Confirm before deletes" toggles actively bypass the preview/confirm screens and execute directly if toggled OFF?

---

## Assumptions Made
- Defaulting to preserving `react-router-dom` since it is already integrated into `App.jsx` and `Sidebar.jsx`.
- All inline SVGs provided in the instructions (logo, connectors, checkmarks, arrows) will be used directly to ensure 100% pixel fidelity with the spec.
