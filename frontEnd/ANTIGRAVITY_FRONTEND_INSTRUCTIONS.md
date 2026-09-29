# QueryMind Frontend Rewrite — Instructions for Antigravity

## 0. Read this entire file before touching anything

You are rewriting the **frontend implementation** of an existing project. The
project structure was set up by a teammate and must be preserved exactly.
The visual design and interaction spec below (Section 3 onward) is the
**source of truth** for how the app should look and behave. It was generated
from a Figma prototype, but **you are not building a Figma-style demo** — you
are building the real, working React application: real component state, real
navigation between screens, real form handling, real timers driving the
processing animation. Every screen must actually function, not just look
like a screenshot.

This file is organized as **phases** (Section 8). Work through them in
order, and keep a running `progress.md` file (see Section 1a and Section 8)
updated as you go so both of us always know what's done and what's left.

You do **not** need to paste your Step 1 inspection findings back to me as
a chat message — write them into `progress.md` instead (see Section 2) and
only interrupt me directly for things that are genuinely blocking (missing
information, a required new file/dependency, an ambiguous spec point). Do
not start writing feature code until Phase 0 (Section 8) is complete.

---

## 1. Hard rules (never break these)

### 1a. Directory / file structure
- Do **not** create new folders.
- Do **not** delete, rename, or move any existing folder.
- Do **not** create new files unless there is genuinely no reasonable way to
  implement something inside the existing files. If you believe a new file
  is required, **stop and ask** — tell me what you want to create, why, and
  which existing file can't reasonably hold it. Wait for my answer.
- Do **not** delete or rename any existing file.
- **One explicit exception**: create a single `progress.md` at the project
  root (`frontEnd/progress.md`). This is the only new file you may create
  without asking first. Use it to track:
  - **Context** — real facts you learn from inspecting the repo that
    aren't already covered in this instructions file (actual existing
    component/page names and what they do, existing helper functions,
    existing context providers, any conventions already in use). If this
    instructions file is missing directory context you needed in order to
    proceed, that's expected — record what you found here instead of
    guessing or waiting on me for things you can determine yourself by
    reading the code.
  - **Phase status** — for each phase in Section 8: not started / in
    progress / done / blocked, with a one-line note per item.
  - **Open questions** — anything still waiting on my answer.
  - **Assumptions made** — anything you decided yourself because it was a
    minor, reversible detail not worth stopping for (keep this list
    short — genuine ambiguity on anything visible or structural still goes
    to "Open questions" instead).
  Update `progress.md` at the end of every phase, not just at the end of
  the whole task.
- The current structure (must remain intact):
  ```
  frontEnd/
  ├── dist/
  ├── node_modules/
  ├── public/
  ├── src/
  │   ├── assets/
  │   ├── components/
  │   ├── context/
  │   ├── pages/
  │   ├── App.jsx
  │   ├── index.css
  │   └── main.jsx
  ├── .gitignore
  ├── .oxlintrc.json
  ├── index.html
  ├── package-lock.json
  ├── package.json
  ├── README.md
  └── vite.config.js
  ```

### 1b. Scope — frontend only
- My role on this team is frontend only. Do **not** modify, generate, or
  assume anything about backend code, API server code, database
  schemas/seed scripts, or any files outside `frontEnd/`.
- There is no real backend integration available yet. Anywhere the UI needs
  data (query results, connection status, history, saved queries, stats),
  use realistic **mock/local data and mock async delays** so the screens
  work and feel real, but keep every place that will eventually call a real
  API clearly marked, e.g. `// TODO: replace mock with real API call` and
  isolate that logic (e.g. in `src/context` or a small service file if one
  already exists) so wiring up the real backend later is a small, obvious
  change — not a rewrite.
- Do not invent backend endpoints, response shapes, or auth logic. If a
  screen needs something backend-shaped (like a login check), fake it
  client-side for now (e.g. any non-empty email/password navigates to the
  workspace) rather than guessing at a real auth flow.

### 1c. Dependencies
- Do not install or uninstall any package without asking first.
- Tell me what you'd like to add and why (e.g. a routing library, an
  animation library) before running any install command.
- Do not change `package.json` or `package-lock.json` except as a direct
  result of an install I've approved.

### 1d. Git safety
- Do **not** run `git commit`, `git push`, `git reset`, `git checkout`,
  `git stash`, create branches, or otherwise change Git state.
- Everything stays local and uncommitted until I personally review it in
  the browser and approve it.

### 1e. If you're unsure
- If anything in this document is ambiguous, or you hit a case it doesn't
  cover, **ask me** rather than guessing. Do not silently invent
  functionality, copy, or design details that aren't specified below.

---

## 2. Step 1 — Inspection only (do this first, change nothing)

Before writing or editing any code, inspect the existing frontend. Read
actual file contents, not just filenames. **Do not paste this inspection
back to me as a chat report** — write it into `progress.md` (Section 1a)
under a "Context" heading, structured however is clearest, covering:

1. `package.json` — React version, Vite version, JS or TS, all
   dependencies, any UI/animation/icon/routing/state libraries already
   installed
2. `vite.config.js`
3. `index.html`
4. `src/main.jsx`
5. `src/App.jsx`
6. `src/index.css`
7. Everything in `src/components/`
8. Everything in `src/pages/`
9. Everything in `src/context/`
10. Relevant files in `src/assets/`
11. `README.md` if it has relevant project info

Record in `progress.md`:
- **Current stack** — framework, versions, JS/TS, CSS approach, all
  relevant installed packages
- **Current structure** — for each existing component/page/context:
  filename, purpose, whether its content can be safely rewritten
- **Current functionality** — what actually works today (login,
  routing/navigation, any query UI, any API calls), classified as
  IMPLEMENTED / PARTIALLY IMPLEMENTED / PLACEHOLDER / NOT PRESENT
- **Existing design** — current look/colors/fonts/layout, and whether it
  can reasonably be reused or will effectively be fully replaced
- **Rewrite plan** — which existing files you'd rewrite the *contents* of
  for each of the 11 screens in Section 6, staying within the existing
  folder structure
- **Dependency recommendation** — what's already sufficient vs. what you
  think would genuinely help (e.g. a router if none exists, an HTTP
  client for the API layer in Section 5) — do not install anything, list
  it under "Open questions" instead and wait for approval
- **Open questions** — anything you cannot determine from the repo,
  or anything this instructions file doesn't give you enough context on;
  say so explicitly rather than guessing, and surface these to me directly
  in chat (not just in the file) since they block Phase 1

Once `progress.md` exists with this filled in and any blocking questions
have been sent to me, wait for my go-ahead before starting Phase 1.

---

## 3. Global design system

### 3a. Typography
- Primary font: **Oxygen** (Google Fonts), weights 300 / 400 / 700 — used
  for every heading, label, button, paragraph, placeholder.
- Mono font: **Oxygen Mono** (Google Fonts), regular weight only — used
  exclusively for data-like values: IDs, timestamps, connection strings,
  database/collection names, amounts, row counts.
- Load both via a Google Fonts CSS2 `@import` at the very top of
  `index.css`, before Tailwind's import.
- Set `-webkit-font-smoothing: antialiased` on `body`.

### 3b. Color palette (exact values — do not approximate)

**Backgrounds**
- Page background: `#080809`
- Sidebar: `#09090c`
- Card/surface: `rgba(13,13,17,0.65)` up to `rgba(18,18,24,0.97)` depending
  on focus state
- Card border default: `rgba(255,255,255,0.05)`; hover: `rgba(255,255,255,0.09)`
- Divider lines: `rgba(255,255,255,0.04)`
- Table row dividers: `rgba(255,255,255,0.028)`

**Primary accent — crimson/magenta**
- Button fill: `rgba(184,39,76,0.88)` → hover `rgba(200,42,82,1.0)`
- Button border: `rgba(184,39,76,0.45)`
- Button hover glow: `box-shadow: 0 0 22px rgba(184,39,76,0.28)`
- Input focused border: `rgba(184,39,76,0.38)`; focused bg: `rgba(184,39,76,0.04)`;
  focused glow: `0 0 18px rgba(184,39,76,0.09)`
- Surface tint: `rgba(184,39,76,0.09)`
- Composer rim gradient start: `rgba(184,39,76,0.55)`
- Login bottom-left ambient orb: `rgba(139,26,66,0.14)`
- Canvas corner gradient (login): `rgba(139,26,66,0.13)`
- Sidebar active indicator: `#b8274c`, glow `0 0 8px rgba(184,39,76,0.6)`
- Logo outer ring: `rgba(184,39,76,0.35)`; inner ring: `rgba(184,39,76,0.55)`
  or `0.6`; center dot: `rgba(184,39,76,0.9)`

**Secondary accent — ice blue**
- Node active color: `#4a9eba`; active border: `rgba(74,158,186,0.38)`;
  active bg: `rgba(74,158,186,0.09)`
- Node glow: `0 0 22px rgba(74,158,186,0.18)`
- Flow particle: `rgba(74,158,186,1)` fading to transparent
- Processing screen ambient overlay: `rgba(74,158,186,0.04)`
- "select" type badge: bg `rgba(74,158,186,0.07)`, border `rgba(74,158,186,0.15)`,
  text `rgba(74,158,186,0.65)`
- Login top-right orb: `rgba(74,158,186,0.06)`; workspace top-left drift orb:
  `rgba(74,158,186,0.05)`
- Analyst role badge: bg `rgba(74,158,186,0.09)`, border `rgba(74,158,186,0.2)`,
  text `rgba(74,158,186,0.78)`

**Success green**
- Dot/check: `#2a9d5c`; status dot glow: `0 0 10px rgba(42,157,92,0.6)`
- Success banner: bg `rgba(42,157,92,0.07)`, border `rgba(42,157,92,0.2)`
- Connections card border: `rgba(42,157,92,0.16)`
- Confirm button: bg `rgba(42,157,92,0.12)`, border `rgba(42,157,92,0.28)`,
  text `rgba(42,157,92,0.88)`

**Danger red**
- Overdue badge: bg `rgba(192,57,43,0.12)`, border `rgba(192,57,43,0.22)`,
  text `#e74c3c`
- Delete button: bg `rgba(192,57,43,0.13)`, border `rgba(192,57,43,0.35)`,
  text `#e74c3c`
- Delete card border: `rgba(192,57,43,0.2)`
- Delete-screen pulsing dot: `#c0392b`, glow `rgba(192,57,43,0.7)`
- Update "before" value: bg `rgba(192,57,43,0.07)`, border `rgba(192,57,43,0.14)`
- Error banner: bg `rgba(192,57,43,0.07)`, border `rgba(192,57,43,0.2)`

**Warning amber**
- "update" type badge: bg `rgba(243,156,18,0.07)`, border `rgba(243,156,18,0.15)`,
  text `rgba(243,156,18,0.65)`
- Pending status badge: bg `rgba(243,156,18,0.1)`, border `rgba(243,156,18,0.18)`,
  text `#f39c12`

**Text hierarchy**
- Primary: `#e8e8ea` / `#e0e0e6`
- Body: `rgba(224,224,230,0.72)`
- Secondary: `rgba(224,224,230,0.55)` → `0.42`
- Muted: `rgba(224,224,230,0.32)` → `0.28`
- Very muted: `rgba(224,224,230,0.22)` → `0.18`
- Sidebar inactive: `rgba(224,224,230,0.28)`; active: `rgba(224,224,230,0.92)`
  / `#e0e0e6`

### 3c. Global animations (define as CSS keyframes, reuse everywhere)
- `breathe` — scale `1→1.07`, opacity `0.45→0.85`. Used on ambient orbs
  (6–8s) and the delete-screen warning dot (2.2s).
- `drift` — translate through a slow diamond path: `(0,0) → (10px,-16px) →
  (-6px,12px) → (14px,6px) → (0,0)`, 22s. Workspace top-left blue orb.
- `slideUp` — `translateY(18px)→0`, opacity `0→1`. Entrance animation for
  almost every content block.
- `fadeRow` — `translateX(-10px)→0`, opacity `0→1`. Staggered entrance for
  table rows / history / saved-query cards.
- `spinSlow` — `0→360deg`. Loading spinners inside buttons.
- `pingSlow` — scale `1→2.4`, opacity `0.7→0`. Three pulsing dots inside an
  active processing node.
- `flowDot` — `translateY(-18px→+18px)`, opacity `0→1→1→0`. The dot that
  travels down a connector between processing nodes.
- `successPop` — scale `0.75→1.06→1.0`, opacity `0→1`. Success checkmark
  circle.
- `nodeActivate` — box-shadow animates from none to
  `0 0 28px rgba(74,158,186,0.45), 0 0 56px rgba(74,158,186,0.12)` then
  settles to about half intensity. Plays when a processing node activates.

### 3d. Scrollbar
Width/height 3px. Track transparent. Thumb `rgba(255,255,255,0.07)`, hover
`rgba(255,255,255,0.14)`. Border-radius 2px.

---

## 4. Ambient Canvas component

Build this as one reusable component (inside `src/components/`, using an
existing file if one already fits that role) drawn with the Canvas 2D API
via `requestAnimationFrame`. It's used inline on Login and standalone on
the Query Workspace and Processing screens (the Processing screen needs its
own particle system for the node-to-node flow — see Screen 3).

- 65 particles: random start position, velocity ±0.22px/frame on both axes,
  radius 0.35–1.45px, base alpha 0.04–0.21, bounce off all four edges.
- Connection lines: every pair within 112px draws a line at
  `rgba(255,255,255, 0.038*(1-distance/112))`, lineWidth 0.5 — invisible at
  112px, full alpha at 0px.
- `cursorInfluence` prop: track `mousemove` on the parent element; particles
  within 160px of the cursor get alpha boosted by `(1-dist/160)*0.28`; on
  `mouseleave` reset cursor position to `(-9999,-9999)` immediately.
- `crimsonGlow` prop: each frame, draw a radial gradient centered at
  `(width*0.5, height)`, radius `height*0.7`, from `rgba(184,39,76,0.045)`
  to transparent.
- Canvas: `position:absolute; inset:0; width:100%; height:100%;
  pointer-events:none`. Resize with the window. Clean up the animation
  frame and event listeners on unmount.

---

## 5. API & data layer — build this as if the backend already existed

There's no live backend yet, but "complete frontend" means every screen's
data flow should be **structured exactly like it will be once the backend
is real** — not just inline mock arrays scattered through components.

- Create one data/service layer (e.g. `src/services/` or wherever fits the
  existing structure best — ask if none of the existing folders are a
  natural home for this and you'd otherwise need a new folder, since new
  folders need my approval per Section 1a). One function per operation the
  app needs, e.g. `login()`, `submitQuery(text)`, `getHistory()`,
  `getSavedQueries()`, `getConnections()`, `addConnection(data)`,
  `testConnection(data)`, `disconnectConnection(id)`, `getSettings()`,
  `updateSettings(data)`.
- Each function should be `async`, return a `Promise`, and simulate a
  realistic network delay (e.g. `setTimeout`) before resolving with mock
  data — so every screen already has real loading and error states wired
  up, not just a synchronous prop.
- Document the expected request/response shape for each function in a
  comment directly above it, as if it were hitting a real REST endpoint
  (method, rough path, request body, response body). This is what makes
  swapping in the real backend later a one-file change instead of a
  rewrite.
- Read the API base URL from an environment variable (e.g.
  `VITE_API_BASE_URL`) even though it's unused for now — set up `.env` /
  `.env.example` with a placeholder value so the wiring is ready. Ask me
  before adding a new `.env` file if you're unsure whether that counts as
  a new file needing approval under Section 1a — my expectation is that a
  `.env.example` for this purpose is fine, but check if in doubt.
- Every screen that fetches data should handle three real states: loading,
  error, and success — not just the happy path. Use the visual language
  already defined for each screen (spinners, error banners) rather than
  inventing new ones.
- Do not call a real external API anywhere. Do not guess at authentication
  headers, tokens, or a real backend URL. Do not touch anything outside
  `frontEnd/`.

---

## 6. Screens

### Screen 1 — Login
Full viewport, `position:relative; overflow:hidden`, background `#080809`.

- Behind everything: the Ambient Canvas, plus two gradients drawn inside
  its own loop for this screen specifically: bottom-left
  `createRadialGradient(0,h,0,0,h,440)` → `rgba(139,26,66,0.13)` →
  transparent; top-right `createRadialGradient(w,0,0,w,0,340)` →
  `rgba(74,158,186,0.05)` → transparent.
- Two breathing orbs on top of the canvas: bottom-left 520×520px at
  `left:-80px; bottom:-120px`, radial-gradient `rgba(139,26,66,0.14)` at
  center to transparent at 68%, `breathe 6s ease-in-out infinite`;
  top-right 380×380px at `right:-80px; top:-80px`, radial-gradient
  `rgba(74,158,186,0.06)` to transparent at 70%, `breathe 8s ease-in-out
  infinite reverse`.
- Centered panel: `z-index:10`, `max-width:820px`, 2-column CSS grid
  (`1fr 1fr`), `min-height:500px`, `margin:0 24px`; border
  `1px solid rgba(255,255,255,0.05)`, `border-radius:16px`,
  `overflow:hidden`, `backdrop-filter: blur(2px)`,
  `background: rgba(8,8,9,0.6)`.
- **Left half (branding)** — `padding:56px 52px`, `background:
  rgba(255,255,255,0.01)`.
  - Logo SVG 40×40 (`viewBox 0 0 40 40`): outer circle r=18 stroke
    `rgba(184,39,76,0.35)` width 1; inner circle r=11 stroke
    `rgba(184,39,76,0.55)` width 1; center dot r=3.5 fill
    `rgba(184,39,76,0.9)`; four axis lines (top/bottom/left/right) stroke
    `rgba(184,39,76,0.4)` width 1.2 round linecap.
  - "QueryMind" heading: 40px / 700 / `#e8e8ea` / letter-spacing -0.025em /
    line-height 1.1 / margin-bottom 10px.
  - Tagline: "Natural language access to your database." — 15px, `rgba(224,224,230,0.4)`,
    weight 300, line-height 1.65, max-width 240px, margin-bottom 52px.
  - Three feature bullets (flex column, gap 14; each: flex row, gap 10,
    align center; 4×4px crimson dot `rgba(184,39,76,0.65)`; text 13px
    `rgba(224,224,230,0.32)` weight 300):
    "Ask in plain English or Hinglish" / "Safe execution with confirmation" /
    "Connected to MongoDB".
- **Right half (form)** — `border-left:1px solid rgba(255,255,255,0.04)`,
  `padding:56px 52px`.
  - Eyebrow: "Authenticated Access" — 11px, letter-spacing 0.16em,
    uppercase, `rgba(224,224,230,0.28)`, margin-bottom 34px.
  - Form (flex column, gap 20). Field labels: 11px, letter-spacing 0.1em,
    uppercase, `rgba(224,224,230,0.38)`, margin-bottom 8px.
  - Email / Password inputs: default `background: rgba(255,255,255,0.02)`,
    `border:1px solid rgba(255,255,255,0.06)`, `border-radius:7px`,
    `padding:12px 15px`, color `#e8e8ea`, 14px, Oxygen; focused:
    `background: rgba(184,39,76,0.04)`, `border-color: rgba(184,39,76,0.38)`,
    `box-shadow: 0 0 18px rgba(184,39,76,0.09)`; `transition: all 0.28s ease`.
  - Submit button "Access QueryMind": `background: rgba(184,39,76,0.88)`,
    `border:1px solid rgba(184,39,76,0.45)`, `border-radius:7px`,
    `padding:13px 20px`, color `#fff`, 14px / 700 / letter-spacing 0.04em;
    hover `background: rgba(200,40,82,1)`, `box-shadow: 0 0 22px rgba(184,39,76,0.28)`;
    `transition: all 0.2s ease`. Since there's no real backend yet, clicking
    with the fields filled navigates straight to the workspace (client-side
    only — no API call). Mark this clearly as a stand-in for real auth.

### Screen 2 — Query Workspace
Full height, flex column, centered, background `#080809`, `overflow:hidden`.

- Background: Ambient Canvas with `cursorInfluence` and `crimsonGlow` both
  on; plus a drift orb, `position:absolute; top:-40px; left:-40px`,
  320×320px, radial-gradient `rgba(74,158,186,0.05)` to transparent at 70%,
  `drift 22s ease-in-out infinite`.
- Content block: `position:relative; z-index:10; max-width:700px;
  padding:0 36px`.
- **Header** (`slideUp 0.55s ease-out both`): eyebrow "Student Database ·
  MongoDB" — 11px, letter-spacing 0.2em, uppercase, `rgba(224,224,230,0.27)`,
  margin-bottom 12px; H1 "Ask your database anything." — 34px / 700 /
  `#e8e8ea` / letter-spacing -0.025em / line-height 1.12, margin-bottom 44px.
- **Query composer** (`slideUp 0.55s ease-out 0.08s both`), tracks
  hover and focus:
  - Gradient rim (`position:absolute; inset:-1px; border-radius:12px;
    pointer-events:none`): focused →
    `linear-gradient(135deg, rgba(184,39,76,0.55), rgba(74,158,186,0.25), rgba(184,39,76,0.45))`;
    hovered → `linear-gradient(135deg, rgba(184,39,76,0.18), rgba(255,255,255,0.05))`;
    default → transparent. `transition: all 0.38s ease`.
  - Inner container: focused `background: rgba(18,18,24,0.97)`, border
    `1px solid rgba(184,39,76,0.25)`, shadow
    `0 0 44px rgba(184,39,76,0.07), inset 0 1px 0 rgba(255,255,255,0.04)`;
    hovered border `rgba(255,255,255,0.07)`; default `background:
    rgba(13,13,17,0.8)`, border `rgba(255,255,255,0.05)`, shadow
    `inset 0 1px 0 rgba(255,255,255,0.025)`. `border-radius:12px;
    padding:22px 22px 16px; transition: all 0.3s ease`.
  - Textarea: full width, no background/border/outline, color `#e8e8ea`,
    18px, Oxygen, weight 300, `resize:none`, line-height 1.62,
    letter-spacing -0.01em, `rows=3`, placeholder "Which students have
    unpaid fees this semester?". **Enter submits (without Shift); Shift+Enter
    inserts a newline** — implement this as real keydown handling.
  - Bottom bar (`border-top: rgba(255,255,255,0.04); padding-top:14px;
    margin-top:14px`, flex row, space-between): left hint text 11px
    `rgba(224,224,230,0.18)` — "Enter to run · Shift+Enter for newline" when
    empty, "{n} chars · Enter to run" while typing (real character count);
    right "Run Query" button — active (non-empty text) `background:
    rgba(184,39,76,0.82)`, border `rgba(184,39,76,0.45)`, color `#fff`,
    hover `background: rgba(200,42,82,1)`, `box-shadow: 0 0 18px rgba(184,39,76,0.3)`;
    inactive (empty) `background: rgba(255,255,255,0.04)`, border
    `rgba(255,255,255,0.06)`, color `rgba(224,224,230,0.2)`, `cursor:default`.
    12px / 700 / letter-spacing 0.04em, `border-radius:6px; padding:8px 18px`,
    plus a small right-arrow SVG (`d="M2 6h8M7 3l3 3-3 3"`).
- **Example pills** (`slideUp 0.55s ease-out 0.16s both`, margin-top 28px):
  label "Try an example" — 10px, letter-spacing 0.15em, uppercase,
  `rgba(224,224,230,0.22)`, margin-bottom 12px. Four pills, flex-wrap, gap 8,
  `padding:7px 14px; border-radius:100px`; default `background:
  rgba(255,255,255,0.02)`, border `rgba(255,255,255,0.05)`, color
  `rgba(224,224,230,0.38)`; hover `background: rgba(255,255,255,0.035)`,
  border `rgba(255,255,255,0.09)`, color `rgba(224,224,230,0.68)`;
  `transition: all 0.18s ease`; left colored dot 5×5px (blue for select
  `rgba(74,158,186,0.35)`, amber for update `rgba(243,156,18,0.4)`, red for
  delete `rgba(192,57,43,0.4)`). Clicking a pill fills and focuses the
  textarea with its text. The four examples:
  1. "Which students have unpaid fees this semester?" — select (blue)
  2. "Show all students enrolled in Computer Science." — select (blue)
  3. "Change Rahul's department to Computer Science." — update (amber)
  4. "Delete all inactive student records." — delete (red)
- **Query type detection** (real logic, not cosmetic): if the query starts
  with delete/remove/erase/purge → `delete`; if it starts with
  change/update/set/modify, or contains "'s department" / "'s name" →
  `update`; otherwise → `select`. This type drives which screen you land on
  after processing (result vs. update-preview vs. delete-confirm).

### Screen 3 — Processing
Full height, flex column, centered, background `#080809`, `overflow:hidden`.
This is the most animated screen — implement the timers as real
`setTimeout`/state transitions, not a fixed animation loop that ignores
state.

- A dedicated `<canvas>` (`position:absolute; inset:0`, full size,
  `pointer-events:none`) runs its own particle/flow system for this screen.
- Ambient overlay div (`inset:0; pointer-events:none`): radial-gradient
  `ellipse 60% 50% at 50% 50%`, `rgba(74,158,186,0.04)` to transparent at 70%.
- Canvas node Y positions (proportional to canvas height): USER `h*0.18`,
  QUERYMIND AI `h*0.39`, MONGODB `h*0.61`, RESULT `h*0.82`.
- Dashed connectors between adjacent nodes, from `(cx, nY[i]+30)` to
  `(cx, nY[i+1]-30)`: active segment `rgba(74,158,186,0.14)`, dash `[4,7]`;
  inactive `rgba(255,255,255,0.04)`, same dash.
- Flow particles: array of `{t, speed, seg, alpha}`, spawned every 190ms on
  the currently active segment; `speed = 0.012 + random()*0.009`;
  `alpha = 0.55 + random()*0.45`; Y interpolated `fromY + (toY-fromY)*t`;
  alpha fades in over the first 12% of travel and out over the last 12%;
  each particle draws a 5px radius radial glow (`rgba(74,158,186,alpha)` to
  transparent) plus a 14px tail at 28% alpha; removed once `t > 1`. Active
  segment advances every 1500ms in sync with the stage timer below.
- Query text at top (`position:absolute; top:44px`, `slideUp 0.5s ease-out
  both`): eyebrow "Processing" — 11px, letter-spacing 0.18em, uppercase,
  `rgba(224,224,230,0.25)`, margin-bottom 9px; the actual query in italic,
  15px, `rgba(224,224,230,0.55)`, weight 300, line-height 1.55, max-width
  580px, centered.
- **Stage timing (real React state, not purely CSS):**
  - mount → `stage = 0`
  - 1500ms → `stage = 1`
  - 3000ms → `stage = 2`
  - 4500ms → `stage = 3`, `complete = true`
  - 5200ms → navigate to `result` / `update-preview` / `delete-confirm`
    depending on the query's detected type
- **Node cards** (`slideUp 0.5s ease-out 0.1s both`, flex column, centered):
  each card is flex row, align center, gap 14, `padding:12px 26px;
  min-width:230px; border-radius:9px; transition: all 0.7s ease`.
  - USER node (always active): `background: rgba(184,39,76,0.08)`, border
    `rgba(184,39,76,0.28)`, dot `rgba(184,39,76,0.9)` with glow, label
    `rgba(224,224,230,0.82)` 11px/700/letter-spacing 0.13em/uppercase.
  - Other nodes, **active**: `background: rgba(74,158,186,0.09)`, border
    `rgba(74,158,186,0.38)`, dot `#4a9eba` with `box-shadow: 0 0 10px #4a9eba`,
    label `#c8dde8`; plays `nodeActivate` on activation.
  - Other nodes, **inactive**: `background: rgba(255,255,255,0.02)`, border
    `rgba(255,255,255,0.06)`, dot `rgba(255,255,255,0.12)`, label
    `rgba(224,224,230,0.28)`.
  - Right side of each card: AI/MONGODB nodes when active-and-not-complete
    show three 3×3px dots color `#4a9eba`, each `pingSlow 1.6s ease-in-out`
    staggered `[0s, 0.22s, 0.44s]` infinite; RESULT node when
    `complete=true` shows a checkmark SVG 15×15 (`d="M2 7l4 4 6-6"`), stroke
    `#2a9d5c`, width 2.2.
  - **Connectors** between nodes: 38px tall, flex column centered. Vertical
    line 1px wide: when `stage > i`, `linear-gradient(to bottom,
    rgba(74,158,186,0.5), rgba(74,158,186,0.12))`; otherwise
    `rgba(255,255,255,0.05)`; `transition: all 0.6s ease`. Flowing dot
    (only while `stage === i` and not complete): 5×5px circle, color
    `#b8274c` for the USER→AI connector and `#4a9eba` for the rest, glow to
    match, `flowDot 1.1s ease-in-out infinite`.
- **Stage label** (`position:absolute; bottom:52px`, text-center, key
  changes with `stage` so `slideUp` re-plays each time): stage 0
  "Understanding your question"; stage 1 "Finding relevant data"; stage 2
  "Running database operation"; complete → "Operation complete" in
  `rgba(42,157,92,0.75)`.

### Screen 4 — Result
Full height, flex column, background `#080809`, `overflow:hidden`.

- **Header** (`slideUp 0.45s ease-out both`, `padding:26px 36px 22px`,
  `border-bottom: rgba(255,255,255,0.04)`, flex row, space-between):
  - Left: status row — 6×6px dot `#2a9d5c` glow `0 0 8px rgba(42,157,92,0.65)`
    + "{n} records found" 11px, letter-spacing 0.15em, uppercase,
    `rgba(42,157,92,0.78)`, margin-bottom 7px; query in italic below, 14px,
    `rgba(224,224,230,0.42)`, weight 300, max-width 560px.
  - Right buttons: "New Query" — `padding:8px 16px; background:
    rgba(255,255,255,0.03); border: rgba(255,255,255,0.06); border-radius:6px`,
    color `rgba(224,224,230,0.38)`, hover color `0.65`/border `0.1`,
    navigates to workspace. "Export PDF" — flex row gap 7, `background:
    rgba(184,39,76,0.09); border: rgba(184,39,76,0.2)`, color
    `rgba(224,224,230,0.72)`, `border-radius:6px`, download-arrow SVG, hover
    `background 0.16 / border 0.32`.
- **Table**: scrollable, `padding:0 36px 36px`, `border-collapse:collapse`,
  `margin-top:22px`. Headers (TH): left-align, `padding:9px 14px`, 10px/700/
  letter-spacing 0.13em/uppercase, `rgba(224,224,230,0.28)`, `border-bottom:
  1px solid rgba(255,255,255,0.05)`, Oxygen Mono. Columns: Student ID /
  Name / Program / Semester / Fee Amount / Due Date / Status.
  - Each row: hover `background: rgba(255,255,255,0.018)`, `transition:0.15s`;
    `fadeRow 0.38s ease-out [i*0.04s] both` (real staggered index, not a
    fixed guess).
  - Cells (`padding:11px 14px; border-bottom: rgba(255,255,255,0.028)`):
    Student ID 11px Oxygen Mono `rgba(224,224,230,0.38)`; Name 13px
    `#e0e0e6` weight 400; Program 13px `rgba(224,224,230,0.58)`; Semester
    12px Oxygen Mono `rgba(224,224,230,0.45)`; Fee Amount 13px Oxygen Mono
    `rgba(224,224,230,0.8)`; Due Date 12px Oxygen Mono
    `rgba(224,224,230,0.45)`; Status → badge.
  - Status badges: Overdue → `background: rgba(192,57,43,0.12); border:
    rgba(192,57,43,0.22)`, text `#e74c3c`; Pending → `background:
    rgba(243,156,18,0.1); border: rgba(243,156,18,0.18)`, text `#f39c12`.
    `padding:3px 11px; border-radius:100px; font-size:11px; font-weight:700;
    letter-spacing:0.06em`.
  - Mock dataset — 18 rows using these names: Priya Sharma, Arjun Patel,
    Meera Nair, Rohan Verma, Kavya Reddy, Sanjay Gupta, Ananya Singh, Vikram
    Joshi, Pooja Iyer, Rahul Mehta, Ishita Kapoor, Devraj Pandey, Shruti
    Menon, Karan Malhotra, Nidhi Agrawal, Tarun Bhatia, Palak Saxena, Ayush
    Chauhan. Programs: B.Tech CSE / EE / Mech / Civil, MCA, MBA, B.Sc IT,
    B.Com. Semesters 1st–7th. Fees ₹32,000–₹78,000. Due dates Jul–Aug 2026.
    Mix of Overdue/Pending statuses.

### Screen 5 — Update Preview
Full height, flex column, centered, background `#080809`, `padding:0 32px`.
Content `max-width:540px`, `slideUp 0.48s ease-out both`.

- Header: eyebrow "Update Record" — 10px, letter-spacing 0.2em, uppercase,
  `rgba(74,158,186,0.55)`, margin-bottom 8px; query in italic below, 14px,
  `rgba(224,224,230,0.42)`, weight 300.
- Record card: `background: rgba(13,13,17,0.85); border:
  rgba(255,255,255,0.07); border-radius:11px; overflow:hidden`, margin-bottom
  26px.
  - Card header (`border-bottom: rgba(255,255,255,0.04); padding:20px 26px`):
    "Rahul Mehta" 18px/700 `#e8e8ea`; "STU-2024-023" 12px
    `rgba(224,224,230,0.32)` Oxygen Mono.
  - Card body (`padding:24px 26px`): section label "Department" 10px
    uppercase letter-spacing 0.14em `rgba(224,224,230,0.28)` margin-bottom
    16px. Before/after row (flex, align center, gap 14, wrap): before value
    "Information Technology" — `background: rgba(192,57,43,0.07); border:
    rgba(192,57,43,0.14); border-radius:6px; padding:9px 16px`, 13px,
    `rgba(224,224,230,0.55)`, `text-decoration: line-through` color
    `rgba(192,57,43,0.4)`; arrow SVG (`viewBox 0 0 20 10`) stroke
    `rgba(224,224,230,0.2)` width 1.5; after value "Computer Science" —
    `background: rgba(42,157,92,0.07); border: rgba(42,157,92,0.22);
    border-radius:6px; padding:9px 16px`, 13px, `#e0e0e6`, weight 700.
  - Card footer (`border-top: rgba(255,255,255,0.04); background:
    rgba(255,255,255,0.01); padding:12px 26px`): "This will modify 1 record." —
    12px `rgba(224,224,230,0.28)`.
- Buttons (flex row, gap 12): Cancel (flex:1) — `background:
  rgba(255,255,255,0.03); border: rgba(255,255,255,0.06); border-radius:7px`,
  color `rgba(224,224,230,0.45)`, navigates to workspace. Confirm Change
  (flex:2): default `background: rgba(42,157,92,0.12); border:
  rgba(42,157,92,0.28)`, color `rgba(42,157,92,0.88)`, weight 700; on click,
  **actually transition to a processing state for 1800ms** (real timer):
  `background: rgba(74,158,186,0.1); border: rgba(74,158,186,0.28)`, color
  `rgba(74,158,186,0.7)`, `cursor:default`, 13px spinner (`border:1.5px solid
  rgba(74,158,186,0.25); border-top-color:#4a9eba; spinSlow 0.85s linear
  infinite`), text "Executing change…".
- Success state (after the real 1800ms timer fires): screen replaces with a
  52×52px circle (`background: rgba(42,157,92,0.1); border:
  rgba(42,157,92,0.3); successPop 0.5s ease-out both`) containing a
  checkmark SVG (`d="M4 10l5 5 8-8"`, stroke `#2a9d5c`, width 2.5); "Change
  completed" 20px/700 `#e8e8ea` (`slideUp 0.4s ease-out 0.12s both`); "1
  record updated" 14px `rgba(224,224,230,0.38)` (`slideUp 0.4s ease-out
  0.22s both`); "New Query" button (`slideUp 0.4s ease-out 0.32s both`).

### Screen 6 — Delete Confirm
Same structural layout as Update Preview, red instead of blue/green accents.

- Header: flex row, gap 9, margin-bottom 9px — pulsing red dot 7×7px
  `background:#c0392b`, glow `0 0 10px rgba(192,57,43,0.7)`, `breathe 2.2s
  ease-in-out infinite`; "Destructive Action" 10px, letter-spacing 0.2em,
  uppercase, `rgba(192,57,43,0.7)`. Query in italic below, 14px,
  `rgba(224,224,230,0.42)`, weight 300.
- Warning card: `background: rgba(13,13,17,0.85); border:
  rgba(192,57,43,0.2); border-radius:11px; overflow:hidden; box-shadow: 0 0
  32px rgba(192,57,43,0.04)`.
  - Card header (`padding:22px 26px`): "This will permanently delete " in
    `#e8e8ea` + "126 records" in `#e74c3c` + "." — 20px/700/line-height
    1.35. Sub: "This action cannot be undone." — 13px
    `rgba(224,224,230,0.32)` weight 300.
  - Card body (`padding:22px 26px`, flex column gap 14, rows separated by
    1px `rgba(255,255,255,0.035)` dividers): Collection → "students"
    (`rgba(224,224,230,0.68)`, Oxygen Mono); Condition → "status = inactive"
    (Oxygen Mono); Records affected → "126" in `#e74c3c`, weight 700,
    Oxygen Mono.
- Buttons: Cancel same as Update Preview. "Delete 126 Records" (flex:2):
  default `background: rgba(192,57,43,0.13); border: rgba(192,57,43,0.35)`,
  color `#e74c3c`, weight 700; on click, real 2100ms processing state:
  `background: rgba(192,57,43,0.08); border: rgba(192,57,43,0.18)`, color
  `rgba(231,76,60,0.45)`, `cursor:default`, red spinner (`border-top-color:
  #e74c3c`), text "Deleting…".
- Success state: same structure as Update Preview but "Operation completed" /
  "126 records deleted".

### Screen 7 — Query History
Header: "Query History" (h2) + "Previous natural-language queries — click
to re-run" (sub). Scrollable list, `padding:16px 24px`.

- Each row: flex row, align center, gap 16, `padding:15px 20px;
  border-radius:8px; cursor:pointer`; `fadeRow 0.38s ease-out [i*0.045s]
  both`; hover `background: rgba(255,255,255,0.02); border: 1px solid
  rgba(255,255,255,0.04)`.
  - Left — type badge pill (`border-radius:100px; padding:3px 10px;
    font-size:9px; font-weight:700; letter-spacing:0.13em; uppercase;
    min-width:54px; text-align:center`): select → `rgba(74,158,186,0.07)` bg
    / `rgba(74,158,186,0.15)` border / `rgba(74,158,186,0.65)` text; update →
    amber equivalents; delete → red equivalents.
  - Center — query text 14px `rgba(224,224,230,0.72)`, ellipsis/nowrap,
    `flex:1`; collection below 11px Oxygen Mono `rgba(224,224,230,0.24)`.
  - Right — time 12px `rgba(224,224,230,0.28)` margin-bottom 3px; count
    11px Oxygen Mono in the type's accent color, formatted "18 rows" /
    "1 updated" / "n deleted".
  - Far right — 11×11px arrow SVG, `rgba(224,224,230,0.12)` default,
    `rgba(224,224,230,0.35)` hover.
  - Clicking a row re-runs that query (goes through Processing exactly like
    a fresh query, using its stored type).
- Mock data (9 rows): "Which students have unpaid fees this semester?" —
  select, 2 min ago, 18 rows, students · "Show all inactive student
  accounts." — select, 14 min ago, 126 rows, students · "Find students
  enrolled in Computer Science this semester." — select, 1 hour ago, 84
  rows, students · "Change Rahul Mehta's department to Computer Science." —
  update, 2 hours ago, 1 updated, students · "Show top 10 students by
  CGPA." — select, Yesterday, 10 rows, students · "List all students with
  attendance below 75%." — select, Yesterday, 37 rows, attendance · "How
  many students are in the 3rd semester?" — select, 2 days ago, 142 rows,
  students · "Update fee status for Ishita Kapoor to paid." — update, 2
  days ago, 1 updated, students · "Show all students in the MBA
  programme." — select, 3 days ago, 96 rows, students.

### Screen 8 — Saved Queries
Header: "Saved Queries" (h2) + "Quick-access queries — click to run" (sub).
Grid: `repeat(auto-fill, minmax(290px, 1fr))`, gap 12, `padding:24px 36px`.

- Each card (`slideUp 0.4s ease-out [i*0.06s] both`): default `background:
  rgba(13,13,17,0.65); border: rgba(255,255,255,0.05); border-radius:11px;
  padding:20px 22px; cursor:pointer`; hover `background: rgba(15,15,20,0.9);
  border: rgba(255,255,255,0.09); transform: translateY(-2px)`;
  `transition: all 0.2s ease`.
  - Top row: name 14px/700 `rgba(224,224,230,0.82)` default → `#e8e8ea`
    hover, plus right-aligned arrow SVG `rgba(224,224,230,0.15)` default →
    `rgba(224,224,230,0.4)` hover.
  - Query text 13px `rgba(224,224,230,0.38)` italic weight 300, line-height
    1.55, margin-bottom 14px.
  - Bottom row (space-between): collection name (Oxygen Mono 11px
    `rgba(224,224,230,0.2)`) + saved date (11px `rgba(224,224,230,0.2)`).
- Mock data (6 cards): "Unpaid Fees Report" — students, 12 Aug 2026 ·
  "Inactive Students" — students, 10 Aug 2026 · "CS Enrolment" — students, 8
  Aug 2026 · "Low Attendance Alert" — attendance, 5 Aug 2026 · "Top CGPA
  Students" — students, 3 Aug 2026 · "MBA Semester Fees" — students, 1 Aug
  2026. Clicking a card runs its query through Processing.

### Screen 9 — Connections
Header with "Add Connection" button: `background: rgba(184,39,76,0.09);
border: rgba(184,39,76,0.22); color: rgba(224,224,230,0.68); border-radius:
7px; padding:9px 18px`, plus SVG + text gap 8, hover `background 0.16 /
border 0.35`, navigates to Add Connection.

- Active connection card: `max-width:580px; slideUp 0.48s ease-out both;
  background: rgba(13,13,17,0.85); border: rgba(42,157,92,0.16);
  border-radius:12px`.
  - Card top (`padding:22px 28px`, `border-bottom`, flex row,
    space-between): left — status row (7×7px green dot `#2a9d5c` glow `0 0
    10px rgba(42,157,92,0.6)` + "Connected" 10px letter-spacing 0.15em
    uppercase `rgba(42,157,92,0.72)`); "Student Database" 18px/700
    `#e8e8ea`; "MongoDB" 12px Oxygen Mono `rgba(224,224,230,0.32)`. Right —
    "Manage" (toggles to "Done") button, `background: rgba(255,255,255,0.03);
    border: rgba(255,255,255,0.07); color: rgba(224,224,230,0.42); font-size:
    12px; border-radius:6px`. **This toggle must actually show/hide the
    manage panel below via real state.**
  - Stats grid (`padding:22px 28px; grid-template-columns:1fr 1fr; gap:10px`),
    four tiles — Collections (7), Last synced (3 min ago), Host
    (cluster0.mongodb.net), Database (college_db); each tile `background:
    rgba(255,255,255,0.02); border: rgba(255,255,255,0.04); border-radius:
    7px; padding:12px 16px`, label 10px uppercase letter-spacing 0.1em
    `rgba(224,224,230,0.28)`, value 13px Oxygen Mono
    `rgba(224,224,230,0.72)`.
  - Manage panel (when toggled, `slideUp 0.3s ease-out`,
    `border-top: rgba(255,255,255,0.04); padding:16px 28px 22px`, flex row
    gap 10): "Sync Schema" (neutral button) and "Disconnect" (`background:
    rgba(192,57,43,0.07); border: rgba(192,57,43,0.15); color:
    rgba(231,76,60,0.7)`).
- Add-another slot below the card (`margin-top:12px; border:1px dashed
  rgba(255,255,255,0.06); border-radius:12px; padding:20px 28px`, flex row
  gap 14, `cursor:pointer`, color `rgba(224,224,230,0.25)`, plus SVG + "Add
  another connection", 14px weight 300; hover border
  `rgba(184,39,76,0.22)`, text `rgba(224,224,230,0.45)`; navigates to Add
  Connection.

### Screen 10 — Add Connection
Back link "← Connections" at top — no bg/border, 12px,
`rgba(224,224,230,0.3)`, hover `0.58`, back-arrow SVG 10×10, navigates to
Connections. H2 "Add MongoDB Connection" — 22px/700 `#e8e8ea`.

- Form: `max-width:490px`, flex column gap 22, `slideUp 0.45s ease-out
  both`. Field labels 10px, letter-spacing 0.13em, uppercase,
  `rgba(224,224,230,0.36)`, margin-bottom 8px.
- Connection Name / Connection String / Database Name inputs: default
  `background: rgba(255,255,255,0.02); border: rgba(255,255,255,0.06);
  border-radius:7px; padding:11px 14px`, color `#e8e8ea`, 14px, Oxygen;
  focused `background: rgba(184,39,76,0.035); border: rgba(184,39,76,0.32);
  box-shadow: 0 0 16px rgba(184,39,76,0.07)`; `transition: all 0.25s ease`.
- Database Type field (static, non-editable): same container styling, shows
  8×8px green dot `#2a9d5c` + "MongoDB" text `rgba(224,224,230,0.65)`.
- Test flow (real state machine, not just a static banner): clicking "Test
  Connection" disables both buttons and shows a spinner + "Testing…" for a
  believable mock delay, then shows either:
  - success banner — `background: rgba(42,157,92,0.07); border:
    rgba(42,157,92,0.2); border-radius:7px; padding:12px 16px`, checkmark
    SVG 14×14 + "Connection successful — database reachable", 13px,
    `rgba(42,157,92,0.88)`, `slideUp 0.3s ease-out`
  - or error banner — `background: rgba(192,57,43,0.07); border:
    rgba(192,57,43,0.2)`, warning SVG + "Could not connect — check your
    connection string.", 13px, `rgba(231,76,60,0.88)`
  Ask me whether the mock test should always succeed, always fail, or
  randomly vary — don't decide that silently.
- Buttons (flex row, gap 12): "Test Connection" (flex:1) `background:
  rgba(255,255,255,0.03); border: rgba(255,255,255,0.07); color:
  rgba(224,224,230,0.45)`, disabled + spinner while testing. "Connect"
  (flex:2) `background: rgba(184,39,76,0.84); border: rgba(184,39,76,0.42);
  color:#fff; font-weight:700`, hover `background: rgba(200,42,82,1);
  box-shadow: 0 0 18px rgba(184,39,76,0.28)`, navigates to Connections.

### Screen 11 — Settings
Header: "Settings" (h2) + "QueryMind preferences" (sub). `max-width:560px`,
`slideUp 0.45s ease-out both`. Three sections.

- Section label: 10px, letter-spacing 0.18em, uppercase,
  `rgba(224,224,230,0.28)`, margin-bottom 14px. Section card: `background:
  rgba(13,13,17,0.65); border: rgba(255,255,255,0.05); border-radius:11px;
  overflow:hidden`. Row: flex, space-between, align center,
  `padding:15px 22px`, `border-bottom: rgba(255,255,255,0.035)` (last row no
  border). Label 14px `rgba(224,224,230,0.72)`; hint below 12px
  `rgba(224,224,230,0.25)` weight 300.
- Toggle component (40×22px, `border-radius:11px`): ON `background:
  rgba(184,39,76,0.58); border: rgba(184,39,76,0.4)`; OFF `background:
  rgba(255,255,255,0.08); border: rgba(255,255,255,0.1)`; thumb 16×16px
  circle `background:#e0e0e6`, `left:20px` ON / `left:2px` OFF,
  `transition: all 0.3s ease`. **Must be a real clickable toggle backed by
  state**, not a static image of a toggle.
- Select element: `background: rgba(255,255,255,0.04); border:
  rgba(255,255,255,0.08); border-radius:6px; padding:6px 12px; color:
  rgba(224,224,230,0.65); font-size:13px`, option background `#13131a`.
- **Query Behaviour** (4 rows): "Confirm before updates" (hint: "Show a
  preview before executing UPDATE operations") — toggle, default ON;
  "Confirm before deletes" (hint: "Show a warning before executing DELETE
  operations") — toggle, default ON; "Result row limit" (hint: "Maximum
  records returned per query") — select 50/100/250/500, default 100;
  "Query timeout" (hint: "Seconds before a slow query is cancelled") —
  select 15/30/60/120, default 30. These settings should actually be read
  from state/context (e.g. skip the update/delete preview screens when
  their toggle is off) rather than being decorative — confirm with me if
  wiring that up touches files outside what's reasonable for this pass.
- **Account** section (3 static rows): Name → "Heer Sachdev" (Oxygen Mono,
  `rgba(224,224,230,0.38)`); Email → "heer@college.edu" (same style); Role →
  "Analyst" badge (`background: rgba(74,158,186,0.09); border:
  rgba(74,158,186,0.2); color: rgba(74,158,186,0.78); border-radius:100px;
  padding:3px 11px; font-size:11px`).
- **About** section: Version → "v0.1.0-alpha" (Oxygen Mono,
  `rgba(224,224,230,0.28)`); footer text "MSc IT Application Development
  Project · 2026 / Natural language database assistant · MongoDB" — 12px,
  `rgba(224,224,230,0.2)`, line-height 1.65, weight 300.

### Sidebar (visible on every screen except Login)
Width 64px, height 100vh, `background:#09090c`, `border-right:1px solid
rgba(255,255,255,0.04)`, flex column, `padding:18px 0 14px`, `flex-shrink:0`.

- Top logo SVG 24×24 (`viewBox 0 0 28 28`): outer circle r=12 stroke
  `rgba(184,39,76,0.4)` width 1; inner circle r=7 stroke
  `rgba(184,39,76,0.6)` width 1; center dot r=2.5 fill `rgba(184,39,76,0.9)`.
  Separated from nav by `border-bottom: rgba(255,255,255,0.04);
  padding-bottom:18px; margin-bottom:26px`.
- 5 nav items — Query / History / Saved / Connect / Settings. Settings is
  pinned to the bottom via `margin-top:auto` on that item's wrapper. Each:
  full width, flex column, align center, gap 5px, `padding:13px 0`, no
  background/border, `cursor:pointer`, `transition: color 0.2s ease`.
  Active text `rgba(224,224,230,0.92)` / `#e0e0e6`; inactive
  `rgba(224,224,230,0.28)`; hover `rgba(224,224,230,0.6)`. Icon 17×17px SVG
  in `currentColor`. Label 9px, letter-spacing 0.07em, uppercase, weight
  700 (active) / 400 (inactive).
- Active indicator: `position:absolute; left:0; top:50%; transform:
  translateY(-50%); width:2px; height:22px; background:#b8274c; box-shadow:
  0 0 8px rgba(184,39,76,0.6); border-radius:0 2px 2px 0`.
- Icons: Query = magnifying glass with a plus/crosshair; History = clock
  with backward arrow; Saved = document with lines; Connect = database
  cylinder (three stacked ellipses); Settings = gear with center circle.
- Nav → screen mapping: Query → workspace/processing/result/update-preview/
  delete-confirm; History → history; Saved → saved; Connect →
  connections/add-connection; Settings → settings. The sidebar's "active"
  item should reflect whichever group the current screen belongs to.

---

## 7. Interaction summary (must all be real, working behaviour)

| Moment | Expected behaviour |
|---|---|
| Login loads | Canvas particles + breathing orbs animate immediately |
| Hover a login input | Border/glow transitions to crimson |
| Submit login | Navigate to Workspace |
| Workspace idle | Particle web drifts, blue orb wanders, crimson bloom breathes |
| Focus the composer textarea | Rim blazes crimson→blue→crimson, container deepens |
| Type in the textarea | Char count updates live; Run Query button becomes active |
| Press Enter / click Run Query | Navigate to Processing with the query + detected type |
| Processing loads | Query shown, 4 nodes render, flow particles begin |
| 1500 / 3000 / 4500 / 5200ms | Node activation stages fire on real timers, then auto-navigate |
| Result loads | Table rows stagger in |
| Update Confirm click | 1800ms real "processing" state, then success screen |
| Delete Confirm click | 2100ms real "processing" state, then success screen |
| History / Saved item click | Re-runs that query through Processing |
| Settings toggle click | Thumb slides, state actually persists for the session |
| Add Connection → Test | Real testing state → success/error banner |
| Sidebar nav click | Switches screens, active indicator moves |

---

## 8. Phased execution plan (master guide)

Work through these phases **in order**. Each phase has a goal, tasks, and
an exit condition. At the end of every phase: update `progress.md` (mark
that phase done, note anything left for later, log any assumptions or open
questions), then **stop and wait for me to look at it running locally**
before starting the next phase. Do not collapse multiple phases into one
uninterrupted batch of changes — this is the main way we catch a wrong
turn early instead of after everything is built.

If at any point this file doesn't give you enough detail to make a call —
about the existing code, a design detail, or which of two reasonable
approaches to take — put it in `progress.md` under "Open questions" and,
if it would block real progress, ask me directly. Don't guess and move on
silently for anything structural or visible; small reversible details
(e.g. exact px rounding) can go under "Assumptions made" instead.

### Phase 0 — Inspection & setup
- Do Section 2's inspection and write it into `progress.md`.
- Create the API/data layer skeleton from Section 5 with functions
  stubbed out (even before every screen consumes them).
- Decide (with me, if the repo doesn't already make it obvious) whether
  screen-switching uses a router already in the project or plain state —
  do not add a routing library without asking first.
- **Exit condition**: `progress.md` exists and is filled in for this
  phase; any blocking questions have been sent to me; I've said go.

### Phase 1 — Design system foundation
- Google Fonts import, color tokens, global keyframe animations, scrollbar
  styling (Section 3).
- The Ambient Canvas component (Section 4).
- **Exit condition**: a blank screen that at least shows the correct page
  background and the Ambient Canvas animating, with fonts loading
  correctly. Update `progress.md`.

### Phase 2 — Navigation shell
- Sidebar (Section 6, "Sidebar" subsection) and whatever screen-switching
  mechanism was decided in Phase 0.
- Wire it to placeholder/empty screens for all 11 destinations so
  navigation itself can be verified before any screen has real content.
- **Exit condition**: clicking every sidebar item switches to the right
  empty screen with the active indicator moving correctly. Update
  `progress.md`.

### Phase 3 — Login
- Full Screen 1 implementation per spec, using the login stub from the
  data layer.
- **Exit condition**: matches the spec visually and navigates to Workspace
  on submit. Update `progress.md`.

### Phase 4 — Query Workspace
- Composer, type detection, example pills (Screen 2).
- **Exit condition**: typing, Enter/Shift+Enter, character count, example
  pills, and Run Query button state all work for real. Update
  `progress.md`.

### Phase 5 — Processing
- Node chain, canvas flow particles, real timers, stage labels (Screen 3).
- **Exit condition**: running a query from Workspace plays through all
  four stages on the real timers and auto-navigates to the correct next
  screen based on query type. Update `progress.md`.

### Phase 6 — Result / Update Preview / Delete Confirm
- Screens 4, 5, 6, including the real 1800ms/2100ms confirm-action timers
  and success states.
- **Exit condition**: all three post-processing outcomes work end to end
  for a select/update/delete query respectively. Update `progress.md`.

### Phase 7 — History & Saved
- Screens 7 and 8, backed by the data layer's mock data.
- **Exit condition**: both lists render with correct staggered animation
  and clicking any item re-runs it through Processing. Update
  `progress.md`.

### Phase 8 — Connections & Add Connection
- Screens 9 and 10, including the manage-panel toggle and the test-connection
  state machine.
- **Exit condition**: connect/manage/disconnect/test flows all work with
  mock data and real state. Update `progress.md`.

### Phase 9 — Settings
- Screen 11, including real toggles/selects and (if reasonable within the
  existing structure) actually affecting update/delete confirmation
  behavior.
- **Exit condition**: settings persist for the session and, where wired,
  visibly change app behavior. Update `progress.md`.

### Phase 10 — Full QA pass
- Go back through Section 7 (Interaction summary) line by line and verify
  each one against the running app.
- Re-check every color/animation value in Sections 3, 4, and 6 for drift.
- Confirm every data-fetching screen has working loading/error states per
  Section 5.
- Finalize `progress.md`: everything should be marked done, with only
  genuinely deferred items (if any, and only ones I've agreed to defer)
  left open.
- **Exit condition**: Section 9 (Definition of done) is fully true. Tell
  me it's ready for review. Do not commit or push anything.

---

## 9. Definition of done for this pass

- Every one of the 11 screens plus the sidebar exists, matches the colors/
  type/animations above, and is reachable through real navigation.
- Every interaction in Section 7 actually works when clicked/typed/hovered
  — nothing is a static mockup image or a screen that "always looks like
  this" regardless of state.
- The data layer from Section 5 exists, every screen goes through it
  (nothing pulls mock data straight from an inline array in a component),
  and loading/error/success states all work.
- `progress.md` exists, is up to date, and accurately reflects what's
  done, what's left, and any open questions/assumptions.
- No folders added/removed. No files added/removed beyond `progress.md`
  and (if needed for Section 5) `.env`/`.env.example`, without my prior
  sign-off.
- No backend files touched, no files outside `frontEnd/` touched. No real
  external API calls made — mock data only, structured so a real backend
  can be wired in later with minimal changes.
- No dependency installed without approval. No git commit/push/reset/checkout.
- You've told me anything you're unsure about instead of guessing.

Once all of that is true, tell me it's ready for review — do not commit or
push anything. I'll check it locally and tell you what to fix or confirm
it's approved.
