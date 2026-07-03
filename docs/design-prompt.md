# Design prompt — Tucuso-term web UI

> Feed this whole prompt to Claude (artifact/design mode). Deliverable spec is at the end.

---

You are designing the web UI for **Tucuso-term**, a community EN⇄ES glossary for **volunteer, non-professional interpreters working the Venezuela earthquake response**. It is a Flask-served, offline-capable PWA. This is a **field tool, not a brochure**: it will be used mid-conversation, under stress, on cheap Android phones, during blackouts, sometimes at 2 a.m. in a shelter lit by one lamp.

## The one moment that matters

A volunteer is interpreting between an English-speaking rescue medic and a Spanish-speaking family. They hit a word they don't know ("crush injury"). They have **≤10 seconds**, one hand free, 15% battery, and maybe no signal. If your design nails this moment — type 3 letters, see the validated equivalent huge and unambiguous — everything else is allowed to be merely good.

## Users

1. **The interpreter (90% of traffic)** — bilingual-ish volunteer, not a professional. Needs: instant lookup, both directions (ES→EN, EN→ES), confidence that the term is validated, register warnings so they don't say something vulgar in a hospital.
2. **The contributor** — same person, calmer moment. Submits a missing term or corrects one. Has NO account (by design — political-safety reasons). Gets an anonymous tracking code instead; that code is their only link to their submission.
3. **The reviewer (2–5 people total)** — trusted bilingual moderator, logs in via one-time magic link. Processes a queue: approve / veto (veto requires a reason). Two distinct approvals publish a term.

## Hard constraints (violating any = failed design)

- **Dark theme is the default and primary art direction** (OLED battery, blackout use). A light toggle is optional, dark is what you polish.
- **≤500 KB total first load; target ≤50 KB.** No web fonts (system font stack only), no icon fonts, no images except one inline SVG logo, no CSS/JS frameworks, no external origins of any kind (also a privacy requirement).
- Must look right and work on a **360×640, 2 GB-RAM Android browser**; every interactive target ≥44px; must remain fully usable **without JavaScript** (forms are server-rendered POSTs; JS only enhances).
- **Spanish is the primary UI language**; English appears as content, not chrome.
- WCAG AA contrast minimum; visible focus states; semantic HTML.
- No gamification, no reputation, no avatars, no social features, no analytics — ever. Do not add "engagement" patterns; this tool succeeds when the visit is short.

## Information architecture (5 screens)

### 1. Home / Search (the app)
- Search field is the hero: full-width, autofocused, `type="search"`, placeholder showing both directions ("aplastamiento… / crush injury…").
- Results appear as large cards: **the source term and its equivalent in the other language are co-stars, both big** (the equivalent is the answer — don't bury it in metadata). Direction shown with a ⇄ mark and small `ES`/`EN` badges.
- Each card: term pair, category chip, register chip (see "register colors"), optional zone chip with a subtle warning tone, validation badge.
- Filter row (category select) collapses out of the way; power users only.
- Empty states are designed, not blank: pre-search shows 4–6 category shortcuts + a one-line trust promise ("Cada término publicado fue validado por dos revisores bilingües"); no-results shows "Sin resultados para «X»" + a prominent "Proponer este término" CTA that pre-fills the submit form.

### 2. Term detail
- Layout answers in order: ① the term, ② its equivalent (nearly as large), ③ example sentence in context, ④ metadata (category, register, zone with regional-use caveat, source, validation line "publicado · 2 revisores · 2026-07-03 · v2").
- If register is `vulgar` or `coloquial`, show an unmissable inline caution strip, not a tooltip.
- One clear secondary action: "Sugerir corrección".
- Version count links to nothing yet, but display it — history is a trust feature.

### 3. Submit / Correct (forms)
- One column, generous spacing, labels above fields, ES microcopy, no multi-step wizard.
- Explain the deal up front in one calm sentence: no account needed, two humans review everything, nothing publishes automatically.
- **The token moment is a designed ritual**: after submit, show the tracking code full-width in a highlighted panel with a copy button and the sentence "Guárdelo: es su único vínculo con este envío. Expira en 30 días." This is the screen's climax — make it feel like receiving a receipt, impossible to dismiss accidentally.
- Honeypot field stays visually absent. Rate-limit rejection (429) gets friendly copy, not an error tone.

### 4. Status check
- Single input (paste code) → one of three big, color-coded states: **en revisión** (neutral), **publicado** (success, link to the live term), **rechazado** (calm, with the veto reason if present). Unknown/expired code: neutral copy, no blame.

### 5. Moderation queue (reviewers only)
- Density over beauty, but keep the card pattern: each pending item shows everything needed to decide without navigation (term, equivalent-if-any, definition, example, source label — `tucuso-original-draft` items visibly marked "borrador asistido — revisar con cuidado").
- Approve = big affirmative button; Veto = secondary button that **reveals a required reason field** (friction is intentional).
- Show queue progress ("12 pendientes") and my-vote state ("Ya votó") plainly. After voting, the card collapses with a subtle confirmation — reviewers process dozens; respect their rhythm.

## System states (design all of them)

- **Offline**: persistent amber banner "Sin conexión — glosario local del 2026-07-03" (the snapshot date matters: stale data is a safety issue). Search keeps working; submit forms swap to a "no disponible sin conexión — no se perderá lo escrito" treatment.
- **Stale snapshot** (online but old cache): thinner variant of the banner.
- **Loading**: none. Server renders fast and pages are tiny; do not add skeletons or spinners. Absence of loading UI is a feature.

## Visual language

- **Mood: field equipment.** Think headlamp, radio, triage tag — calm, legible, sturdy. Not "startup dark mode".
- Palette: near-black warm background (#111418 family), one accent (current: #5eb0ff) used *only* for interactive elements, plus a semantic trio: green = validated/published, amber = caution/regional/offline, red = veto/vulgar-register. Semantic colors always paired with a word, never color-alone.
- Register chips: formal/neutral = quiet outline; coloquial = amber outline; vulgar = red fill + explicit label.
- Type: system stack, big. Base 16–17px, term pairs on cards 20–24px, term detail headline 28–32px. Line-height generous. Spanish words are long — design for "Concientización/sensibilización pública" wrapping gracefully.
- Spacing/radius: 6–8px radii, cards separated by hairlines not shadows; zero decoration that costs bytes.
- The ⇄ glyph is the brand. Use it in the logo, empty states, and between term pairs. No other iconography unless inline SVG and genuinely clarifying.

## Deliverable

A single self-contained HTML file (inline CSS, minimal inline JS for demo interactions only) presenting all five screens as high-fidelity, mobile-width (~380px) mockups side by side or stacked, using realistic content: aplastamiento/crush injury, colapso estructural/structural collapse, damnificado/disaster victim, one vulgar-register modismo example, one pending-review item. Include the offline-banner variant of Home. Annotate design decisions in small margin notes. Everything must render offline from the one file — if you reach for a CDN, stop.
