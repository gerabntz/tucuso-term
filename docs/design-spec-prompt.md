# Design-system prompt — Tucuso-term, light editorial theme (paste whole into Claude design)

You are producing high-fidelity UI for **Tucuso-term**, an offline-capable EN⇄ES emergency glossary used by volunteer interpreters in the Venezuela earthquake response, mostly **outdoors in daylight** on inexpensive Android phones. Mood: **a well-made reference book** — think field manual meets elegant dictionary: quiet, warm, typographic, authoritative. Explicitly NOT: app-like, gamified, neon, glossy, rounded, playful.

The design system below is **decided, not suggested**. Apply it exactly; your creative freedom is in composition, hierarchy, and microcopy polish — not in tokens.

## Design tokens

### Color — warm paper light theme (the only theme to design)

| Token | Value | Use — and nothing else |
|---|---|---|
| `--bg` | `#f6f4ef` | page background (warm paper; never stark white — daylight glare) |
| `--surface` | `#fdfcfa` | cards, header, form fields |
| `--surface-2` | `#edeae3` | pressed states, chip fills, table stripes |
| `--line` | `#d8d3c8` | hairline separators and borders (use instead of shadows, always) |
| `--text` | `#26292c` | primary text (soft ink, not pure black) |
| `--muted` | `#6b6e70` | metadata, labels (≥4.5:1; never below 14px) |
| `--accent` | `#3e5f5c` | interactive only: links, buttons, focus, active states (deep muted teal) |
| `--accent-ink` | `#f6f4ef` | text on accent-filled buttons |
| `--ok` | `#3c6e4f` | validated/published semantics only (forest, not lime) |
| `--ok-bg` | `#e7efe8` | quiet fill behind validation badges |
| `--warn` | `#8a6d2f` | caution: regional use, coloquial register, offline/stale (ochre) |
| `--warn-bg` | `#f2ead4` | offline banner and caution-strip fill |
| `--danger` | `#8c4a3f` | veto, vulgar register, destructive only (brick, not fire-engine) |
| `--danger-bg` | `#f0e0dc` | fill behind danger strips |

Rules: everything is low-saturation and warm; **no electric blue, no neon, no saturated highlight anywhere**. Semantic colors are always paired with a word — never color alone. Accent never decorates headings or emphasis. No gradients, no glassmorphism, **no shadows** (borders and background shifts carry all depth), no dark sections.

### Typography — editorial two-family system (zero bytes: system fonts only)

- Display/serif: the generic `Georgia, "Times New Roman", serif` stack — used for the wordmark, page titles, and **the glossary terms themselves** (terms are the content; the serif is what makes this feel like a dictionary, not an app).
- Text/sans: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` — body, forms, chips, buttons.

| Role | Family / size / weight / line-height |
|---|---|
| Base body | sans / 17px / 400 / 1.55 |
| Metadata, chips | sans / 13.5px / 400 / 1.4 (floor 13.5px) |
| Card term pair | **serif** / 22px / 700 / 1.3 |
| Term-detail headline | **serif** / 32px / 700 / 1.15 |
| Detail equivalent (the "answer") | **serif** / 26px / 700 / 1.25 |
| Section h2 | serif / 21px / 700 |
| Buttons | sans / 16px / 600 / letter-spacing 0.01em |

Spanish compounds are long ("Concientización/sensibilización pública") — every element must wrap gracefully at 360px; test headlines against that string.

### Space, shape, motion

- **Radius 0 everywhere. No rounded corners — including chips, buttons, inputs, banners.** Chips are small rectangles.
- 4px spacing grid; card padding 16px; page gutter 16px; max content width 44rem centered.
- Hairline rules (`--line`, 1px) structure the page like a well-set book: under the header, between result entries, above the footer. Cards may be borderless surfaces separated by rules rather than boxes — prefer the dictionary-entry look over the card-grid look.
- Touch targets ≥48×48px; adjacent targets ≥8px apart.
- Focus: 2px solid `--accent` outline, 2px offset, on everything focusable.
- Motion: essentially none. One 120ms opacity ease on moderation-card collapse. No transitions, skeletons, or spinners — absence of loading UI is a feature.

## Components (build these exactly)

- **Search field (hero)**: full-width, 56px tall, `--surface` with 1px `--line` border (sharp corners), placeholder "aplastamiento… / crush injury…", inline-SVG search glyph. Autofocused on Home.
- **Result entry** (dictionary style, not card): serif term (22px) + small-caps `ES`/`EN` marker in `--muted`; next line the equivalent at the same 22px serif preceded by `⇄` in `--ok` — **the equivalent is the answer; it never looks like metadata**. Below: 13.5px sans chip row (category · register · zone). Entries separated by 1px rules, no boxes.
- **Chips**: rectangular, 2px×8px padding, 13.5px sans. Category = `--surface-2` fill. Register: formal/neutral = `--line` outline; coloquial = `--warn` outline + the word; vulgar = `--danger-bg` fill, `--danger` text, explicit word "vulgar". Zone = `--warn` outline "uso regional".
- **Validation badge**: `--ok-bg` fill, `--ok` text: "✓ validado · 2 revisores". Seed rows: "fuente oficial". Pending (queue only): `--warn-bg`/"en revisión".
- **Buttons**: primary = `--accent` fill, `--accent-ink` text; secondary = 1px `--line` outline on `--surface`; danger-secondary (veto) = 1px `--danger` outline. Square. Full-width on mobile forms.
- **Offline banner**: full-width strip under the header, `--warn-bg` fill, `--warn` 1px top/bottom rules, `--text`: "Sin conexión — glosario local del 2026-07-03". The date is mandatory (stale data is a safety issue). Thinner variant for online-but-stale.
- **Token receipt panel**: post-submit climax. `--surface` panel, 3px `--ok` left border, the code at 20px monospace full-width on `--surface-2`, a 48px "Copiar" primary button, and: "Guárdelo: es su único vínculo con este envío. Expira en 30 días."
- **Caution strip** (vulgar/regional, term detail): full-width, `--warn-bg` or `--danger-bg` fill with 3px matching left border, bold leading word, one plain sentence. Not a tooltip, not dismissible.
- **Moderation entry**: everything needed to decide without navigating: term, equivalent, definition, example, source label — `tucuso-original-draft` rows get a `--warn` chip "borrador asistido — revisar con cuidado". Approve = primary; Veto = danger-secondary revealing a required reason field inline. After vote the entry collapses (the one animation); counter "12 pendientes" decrements.
- **Header**: `--surface`, 1px `--line` bottom rule, serif wordmark "Tucuso-term" with the ⇄ mark in `--accent`; sans nav links in `--accent`, no underline until hover/focus.

## Screens to render (mobile, 380px frames)

1. **Home, pre-search**: hero search + 6 category shortcut chips + one trust line ("Cada término publicado fue validado por dos revisores bilingües").
2. **Home, results** for "aplasta": 3 dictionary entries (aplastamiento ⇄ crush injury; colapso estructural ⇄ structural collapse; one with zone chip).
3. **Home, offline variant**: same as 2 with the ochre banner.
4. **Term detail** ×2: damnificado ⇄ disaster victim (example sentence, chips, "publicado · 2 revisores · 2026-07-03 · v2", "Sugerir corrección" secondary); and a vulgar-register modismo showing the danger caution strip.
5. **Submit form + token receipt state** (two frames).
6. **Status check**: the three states (en revisión / publicado / rechazado con motivo).
7. **Moderation queue**: two pending entries (one "fuente oficial", one "borrador asistido"), one collapsed just-voted entry, counter.

Realistic Spanish microcopy throughout; English appears only as glossary content. No "Lorem".

## Hard constraints (violating any = failed output)

Single self-contained HTML file, inline CSS, minimal inline JS for demo toggles only. Zero external requests: no CDNs, no web fonts, no images (inline SVG only). Must render offline from the file. Semantic HTML, WCAG AA, visible focus. No gamification, avatars, social proof, or engagement patterns — the tool succeeds when the visit is short. Annotate key design decisions in small margin notes beside each frame.
