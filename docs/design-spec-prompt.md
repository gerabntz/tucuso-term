# Design-system prompt — Tucuso-term (paste whole into Claude design)

You are producing high-fidelity UI for **Tucuso-term**, an offline-capable EN⇄ES emergency glossary used by volunteer interpreters in the Venezuela earthquake response, on cheap Android phones, often during blackouts. Mood: **field equipment** — headlamp, radio, triage tag. Calm, legible, sturdy. Not "startup dark mode."

The design system below is **decided, not suggested**. Apply it exactly; your creative freedom is in composition, hierarchy, and microcopy polish — not in tokens.

## Design tokens

### Color (dark is the only theme to design)

| Token | Value | Use — and nothing else |
|---|---|---|
| `--bg` | `#111418` | page background (warm charcoal; never pure black) |
| `--surface` | `#1a1f26` | cards, header, form fields |
| `--surface-2` | `#222933` | pressed/hover states, chip fills |
| `--line` | `#262d36` | hairline separators (use instead of shadows, always) |
| `--text` | `#e8eaed` | primary text (≈14:1 on bg) |
| `--muted` | `#98a2ad` | metadata, labels (≥4.5:1 — never smaller than 14px) |
| `--accent` | `#4cc2ff` | interactive only: links, buttons, focus, active states |
| `--accent-ink` | `#06202e` | text on accent-filled buttons |
| `--ok` | `#57c785` | validated/published semantics only |
| `--warn` | `#e6b450` | caution: regional-use, coloquial register, offline/stale banner |
| `--danger` | `#e5695b` | veto, vulgar register, destructive only |

Rules: semantic colors are **always paired with a word** (badge text, label) — never color alone. Accent never used for decoration, headings, or emphasis. No gradients, no glassmorphism, no shadows.

### Typography

System stack only: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`. No web fonts, no icon fonts.

| Role | Size / weight / line-height |
|---|---|
| Base body | 17px / 400 / 1.55 |
| Metadata, chips | 13.5px / 400 / 1.4 (floor: 13.5px, never smaller) |
| Card term pair | 22px / 650 / 1.3 |
| Term-detail headline | 30px / 700 / 1.2 |
| Detail equivalent (the "answer") | 26px / 650 / 1.25, `--ok`-badged |
| Section h2 | 20px / 650 |
| Buttons | 17px / 600 |

Spanish compounds are long ("Concientización/sensibilización pública") — every text element must wrap gracefully at 360px width; test headlines against that string.

### Space, shape, motion

- 4px spacing grid; card padding 16px; page gutter 16px; max content width 44rem centered.
- Radius 8px everywhere (chips 999px).
- Touch targets ≥48×48px; adjacent targets ≥8px apart.
- Focus: 2px `--accent` ring, 2px offset, on everything focusable.
- Motion: essentially none. One 120ms opacity/transform ease on card collapse after a moderation vote. No page transitions, no skeletons, no spinners — pages are tiny and server-rendered; absence of loading UI is a feature.

## Components (build these exactly)

- **Search field (hero)**: full-width, 56px tall, `--surface`, 8px radius, placeholder "aplastamiento… / crush injury…", search glyph as inline SVG. Autofocused on Home.
- **Result card**: term (22px) + `ES|EN` mini-badge, then on the next line the equivalent with a leading `⇄` in `--ok` at the same 22px — **the equivalent is the answer; it never looks like metadata**. Below: chip row (category · register · zone) at 13.5px, hairline separator to next card.
- **Chips**: pill, 13.5px. Category = `--surface-2` fill. Register: formal/neutral = quiet `--line` outline; coloquial = `--warn` outline + word; vulgar = `--danger` fill + `--text` word "vulgar". Zone = `--warn` outline with "uso regional".
- **Validation badge**: `--ok` outline pill: "✓ validado · 2 revisores". Seed rows: `--ok` outline "fuente oficial". Pending (mod queue only): `--warn` "en revisión".
- **Buttons**: primary = `--accent` fill, `--accent-ink` text; secondary = outline `--line`, text `--text`; danger-secondary (veto) = outline `--danger`. Full-width on mobile forms.
- **Offline banner**: full-width strip under the header, `--warn` background, `#111` text: "Sin conexión — glosario local del 2026-07-03". The date is mandatory (stale data is a safety issue). Thinner variant, same content, for online-but-stale.
- **Token receipt panel**: post-submit climax. `--surface` panel, `--ok` left border 4px, the code at 20px monospace full-width, a 48px "Copiar" primary button, and the line "Guárdelo: es su único vínculo con este envío. Expira en 30 días."
- **Caution strip** (term detail, vulgar/regional): full-width inset, `--warn` or `--danger` left border 4px + bold word, one plain sentence. Not a tooltip, not dismissible.
- **Moderation card**: everything needed to decide without navigating: term, equivalent, definition, example, source label — `tucuso-original-draft` rows get a `--warn` chip "borrador asistido — revisar con cuidado". Approve = primary; Veto = danger-secondary that reveals a required reason field inline. After vote: card collapses (the one animation), counter "12 pendientes" decrements.

## Screens to render (mobile, 380px frames)

1. **Home, pre-search**: hero search + 6 category shortcut chips + one trust line ("Cada término publicado fue validado por dos revisores bilingües").
2. **Home, results** for "aplasta": 3 result cards (aplastamiento ⇄ crush injury; colapso estructural ⇄ structural collapse; one with zone chip).
3. **Home, offline variant**: same as 2 with the amber banner.
4. **Term detail**: damnificado ⇄ disaster victim, example sentence, chips, validation line "publicado · 2 revisores · 2026-07-03 · v2", "Sugerir corrección" secondary button. Add a second detail frame for a vulgar-register modismo showing the danger caution strip.
5. **Submit form + token receipt state** (two frames).
6. **Status check**: the three result states (en revisión / publicado / rechazado con motivo).
7. **Moderation queue**: two pending cards (one seed "fuente oficial", one "borrador asistido"), one collapsed just-voted card, counter.

Realistic Spanish microcopy throughout; English appears only as glossary content. No placeholders like "Lorem".

## Hard constraints (violating any = failed output)

Single self-contained HTML file, inline CSS, minimal inline JS for demo toggles only. Zero external requests: no CDNs, no web fonts, no images (inline SVG only). Must render offline from the file. Semantic HTML, WCAG AA, visible focus. No gamification, avatars, social proof, or engagement patterns — the tool succeeds when the visit is short. Annotate key design decisions in small margin notes beside each frame.
