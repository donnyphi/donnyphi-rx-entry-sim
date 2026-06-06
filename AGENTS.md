# AGENTS.md — Rx Entry Simulator design & product guidelines

This file is the source of truth for how the **Rx Entry Simulator** should look, read,
and behave. Read it before making any UI, copy, or layout change. The goal is simple:

> The app must feel like a **clean, serious pharmacy technician training platform** — not
> generic AI-generated software, not a startup landing page, not a kids' quiz app.

The design language already exists in `app.py` inside the `CUSTOM_CSS` string. This
document names the tokens and patterns that are already there so future changes stay
consistent instead of inventing a new look each time.

---

## 0. Architecture (so changes land in the right file)

The app is intentionally split. Respect these boundaries.

| File | Responsibility | Imports streamlit? |
|------|----------------|--------------------|
| `app.py` | All UI, CSS, render functions, session state | Yes (only this file) |
| `checker.py` | Pure field validation, returns uniform result dicts | No |
| `cases.py` | Fictional prescription case data | No |
| `tracker.py` | Session stats + review queue | No |

- **All CSS lives in one place:** the `CUSTOM_CSS` constant at the top of `app.py`.
  Do not add inline `style="..."` for anything reusable — add a class.
- **Validation logic never goes in `app.py`.** Explanations shown to the user *can* be
  built in `app.py` (it is the human-facing layer) but the correct/incorrect decision
  belongs in `checker.py`.
- The three sections (Prescription Entry, Drug Knowledge, Workflow Scenarios) are
  dispatched from `main()` via `st.session_state.active_section`. Keep that pattern.

---

## 1. Product identity

**Name / style direction**
- Product name in UI: **Rx Entry Simulator**, with the subtitle **"Pharmacy technician
  training tool."** Keep this exact framing — it sets a workstation tone, not a SaaS tone.
- Visual metaphor: a **pharmacy workstation / dispensing screen**. White cards on a light
  gray desktop, monospace for prescription shorthand and label fields, a printable
  training label as the reward. Think *practice terminal*, not *marketing site*.

**Target user**
- Pharmacy technician **students and beginners** preparing for certification and real
  prescription entry. Assume they know some abbreviations but are still learning SIG
  decoding, days-supply math, DAW codes, and DUR/workflow judgment.
- They are studying, often on a deadline (e.g. a cohort before a certification exam).
  Every screen should help them *practice and self-correct*, not impress them.

**Overall tone**
- Professional, clear, calm, training-focused.
- Realistic but beginner-friendly: use real pharmacy vocabulary, then explain it plainly.
- Never childish, never hypey, never "fun." No confetti, no mascots, no exclamation-heavy
  praise. A correct answer earns a quiet green check and a useful explanation.
- Always reinforce the safety framing: everything is **"Training only — not for
  dispensing,"** patients/prescribers/identifiers are **fictional**.

---

## 2. Visual design rules

### Color palette (use these exact tokens — they already exist in `CUSTOM_CSS`)

**Neutrals (the bulk of every screen)**
| Token | Hex | Use |
|-------|-----|-----|
| Desktop background | `#f6f7f9` | `.stApp` page background only |
| Card surface | `#ffffff` | every card / panel |
| Input surface | `#fafbfc` | text inputs, textareas |
| Border (default) | `#e5e7eb` | card and chip borders |
| Border (strong) | `#d1d5db` | inputs, container outlines, label paper |
| Hairline | `#f3f4f6` | internal dividers inside a card |
| Text primary | `#111827` | headings, drug names, values |
| Text body | `#374151` / `#4b5563` | paragraphs, explanations |
| Text muted | `#6b7280` | labels, captions, secondary meta |
| Text faint | `#9ca3af` | placeholders, "Not specified" |

**Green (the brand / "pharmacy" / success color)**
| Hex | Use |
|-----|-----|
| `#0f766e` | **Primary teal** — primary buttons, input focus ring, SIG mono text, active nav card, chip values |
| `#115e59` | Primary teal hover |
| `#047857` | **Deep green** — "See Example" button, success titles, "Correct" status text |
| `#065f46` | Deep green hover, success subtitle text |
| `#ecfdf5` / `#d1fae5` / `#a7f3d0` | Green tints — SIG pill bg, success card bg, correct-row bg/border |
| `#166534` | Green text on the "no warnings" empty state |

Green = brand, success, "this is correct," and the primary action. Do not use green for
warnings or to decorate neutral content.

**Amber (caution / verify / partial)**
- Backgrounds `#fffbeb` / `#fef3c7`, borders `#fde68a` / `#f59e0b` / `#fbbf24`,
  text `#92400e` / `#78350f` / `#b45309`.
- Use for: things that need a human check but are not errors — DUR safety callouts, the
  "training only / corrected fields" label banner, the label-locked gate, a **medium**
  feedback score, the "missed fields" chip.

**Red (incorrect / error only)**
- Backgrounds `#fef2f2` / `#fee2e2`, borders `#fecaca`, text `#b91c1c`.
- Use **only** for: an incorrect field row, a **low** feedback score, and low accuracy in
  the header chip. Never use red for emphasis or decoration. Red means "you got this
  wrong" or "this is failing."

**Blue & purple (the established DUR alert taxonomy — do not reinvent)**
The DUR/Safety Review panel already encodes alert categories by color via `safety-callout`
tone classes. Keep this mapping:
| Tone class | Color | Meaning |
|-----------|-------|---------|
| `safety` | amber (`#fffbeb` / `#92400e`) | allergy, interaction, high-alert drug |
| `insurance` | blue (`#f0f9ff` / `#0369a1`) | refill-too-soon, prior auth, plan issues |
| `drug` | green (`#f0fdf4` / `#047857`) | drug verification, LASA, DAW |
| `training` | purple (`#f5f3ff` / `#6d28d9`) | teaching note |

Blue and purple are **reserved** for this taxonomy (and the info disclaimer banner, which
is blue). Don't introduce them elsewhere.

### Typography
- Sans stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
  Arial, sans-serif`. Never add web-font imports or display/script fonts.
- Mono stack: `"SF Mono", Menlo, Consolas, "Courier New", monospace` — used for SIG
  shorthand, Rx numbers, answer boxes, and code-like values. Mono signals "this is data
  off a prescription." Use it deliberately, not for body text.
- Section labels are the recurring device: uppercase, `0.7rem`, weight `700`,
  letter-spacing `0.08em`, color `#6b7280` (class `.section-label`). Every card opens with
  one. Reuse it; don't invent new heading styles.

### Card styling
- White surface, `1px solid #e5e7eb` (or `#d1d5db`), `border-radius: 8px`,
  padding `16px 22px`, `margin-bottom: 12px`. Use the `.section-card` class for HTML-only
  cards, or `st.container(border=True)` **plus** a `<div class="card-border-anchor">` first
  child for Streamlit-native cards (the anchor forces a visible border across Streamlit
  versions — see the comment in `CUSTOM_CSS`).
- One concern per card. Open with a `.section-label`. Keep corners at 8px and shadows
  minimal (`0 1px 2px` at most for the label paper). No heavy drop shadows or glow.

### Button styling
- Radius `6px`, weight `500`, `0.88rem`, padding `7px 20px`, `min-height: 38px`.
- **Primary** (`type="primary"`): teal `#0f766e` fill, white text, hover `#115e59`. Exactly
  **one** primary action per view — the next step the user should take (Check Entry before
  submit; Next Case after a perfect entry; Submit answer in a scenario).
- **Secondary** (`type="secondary"`): white fill, `#d1d5db` border, `#374151` text. For
  everything else (Try Again, Decode SIG, Prev/Next Drug, Start New Session).
- **See Example** is the one deep-green (`#047857`) button, styled via the
  `.see-example-anchor` `:has()` hook. Keep it green and distinct from the teal primary.
- Disabled buttons dim to `opacity: 0.45`. Don't hide actions that are temporarily
  unavailable — disable them so the layout stays stable.

### Form / input styling
- `st.text_input` / `st.text_area` with radius `6px`, border `#d1d5db`, surface `#fafbfc`,
  `0.9rem`; focus ring teal `#0f766e`. Labels `0.8rem`, weight `500`, `#374151`.
- Always set a concrete, instructive `placeholder` (e.g. `"e.g. 500 mg"`,
  `"Include verb, quantity, dosage form, route, frequency, and duration when applicable."`).
- Group fields under small uppercase `.form-group-label` headers ("Drug Entry", "Fill
  Details", "Patient Directions (SIG)"). Keep the seven-field entry order stable.
- Example mode renders **fake** read-only inputs (`.fake-input` / `.fake-textarea`) that
  match the real widgets pixel-for-pixel. If you add a field, add it to both the real and
  the example render paths.

### Feedback / report styling
- The graded report (`render_feedback_report`) is a `.section-card` titled **"Feedback
  Report"** containing a score summary then one row per field.
- Score summary (`.report-summary`) carries a tone: `.high` green (6–7/7), `.medium` amber
  (4–5/7), `.low` red (0–3/7). It shows the score (`X/7 fields correct`) and a short
  performance line.
- Field rows (`.feedback-item`) are `.correct` (green tint) or `.incorrect` (red tint),
  each with a status pill (`.field-status`), a `You entered / Expected` line using
  `.answer-box` mono chips, and a `.feedback-explanation` "why" note. Show all seven fields,
  correct and incorrect — it is a report card, not just an error list.
- Keep explanations to 1–3 sentences. SIG explanations should decode the shorthand to
  plain English and, when useful, break it token by token. Days-supply explanations should
  state `quantity ÷ doses per day`.

---

## 3. Layout rules

**Spacing**
- Page container max-width `1400px`, padding `~1.25rem` top / `1.5rem` sides
  (`.block-container`). Don't widen past 1400px — full-bleed reads like a marketing page.
- Horizontal column gap `14px` (`[data-testid="stHorizontalBlock"]`). Cards stack with
  `12px` vertical rhythm. Use the hairline `#f3f4f6` for dividers *inside* a card, never a
  second heavy border.
- Prefer one idea per row. Let cards breathe; don't pack four panels across.

**Section width**
- Single-column flow for the main work surface (prescription → safety → patient/prescriber
  → entry form → feedback → label). Two-up columns only for naturally paired data (Patient
  + Prescriber). The label paper is capped narrow (`max-width: 560–620px`, centered) so it
  reads like a real label.

**Dashboard structure (top to bottom, in order)**
1. **Header / hero** (`.app-header`): product title + subtitle on the left, stat chips
   (Completed, Accuracy, Missed fields) on the right.
2. **Top nav** (`render_top_nav`): three large cards — Prescription Entry, Drug Knowledge,
   Workflow Scenarios — active one teal, others white.
3. **Active section body.**
4. Section-specific footer (only Prescription Entry shows "Start New Session").

**Module cards (the three nav cards)**
- Large click target (`min-height: 88px`), bold title line + one plain-language
  description line. Active = solid teal `#0f766e` with white title; inactive = white with
  `#1f2937` title and a subtle teal hover hint. Keep them to a single short sentence each.

**Prescription case presentation**
- Lead with the source document card (`render_prescription_card`): a `Prescription · <id>`
  label, date written, the drug line in bold, the SIG in a mono green pill (`.rx-sig`), and
  a tag row for Disp / Refills / DAW. Hide the Disp value as "Not specified" (muted) when
  the case wants the student to calculate quantity.
- Follow the realistic pharmacy order: **Rx → DUR/Safety Review → optional SIG decoder →
  Patient/Prescriber → Entry form → Feedback → Label preview.** This mirrors a real fill
  workflow; do not reorder without a reason.
- Every case is fictional and labeled as training-only. Keep the disclaimer captions.

---

## 4. Copywriting rules

**Voice:** a knowledgeable preceptor at the counter — concise, correct, encouraging
without flattery.

- **Avoid generic SaaS / AI buzzwords:** no "Empower," "Unlock," "Seamless," "Supercharge,"
  "Revolutionize," "Elevate," "Effortless," "Next-generation," "AI-powered,"
  "Streamline your workflow," "Take your skills to the next level."
- **Use specific pharmacy-training language:** SIG, shorthand, days supply, quantity to
  dispense, DAW code, refills authorized, DUR, LASA, prior authorization, refill-too-soon,
  brand medically necessary, prescriber clarification, NKDA.
- **Instructions are short and practical.** Example, keep this exact register:
  *"Read the prescription, enter the required fields, then check your entry."* Tell the
  user the next physical action, not the benefit.
- **Explanations are beginner-friendly but realistic.** Define the term, then show the math
  or rule. Good: *"Days supply = total quantity ÷ doses per day. 60 tablets at 2 per day =
  30 days."* Avoid hand-wavy praise; a "why" note must teach something.
- **Praise is measured.** "Great job — ready for a harder case." is the ceiling. No
  "Amazing!!!", no streak hype.
- **Always keep the safety framing** in copy where a label or fill appears: "Training only
  · not for dispensing," "fictional patient/prescriber."
- Sentence case for body and buttons ("Check entry" style is fine as "Check Entry" to match
  existing labels — keep current button label casing consistent, don't shout in ALL CAPS
  except the established `.section-label` device and the label paper).

---

## 5. Component patterns to reuse

Reuse these existing patterns instead of building new ones. Class names are the contract.

| Pattern | Where / class | Notes |
|---------|---------------|-------|
| **Dashboard hero** | `.app-header` + `.app-title-block` + `.stat-chips` | Title, subtitle, pill chips. One per page, at the very top. |
| **Progress summary chips** | `.chip` / `.chip-value` (+ `.missed`, `.accuracy-low`) | Completed / Accuracy / Missed fields. Green value normally; amber for missed; red for low accuracy. |
| **Module cards** | `render_top_nav` + `.nav-marker.nav-active/.nav-inactive` | Three section selectors. Title + one-line description. |
| **Prescription case card** | `render_prescription_card`, `.rx-*` classes | Source document. Mono SIG pill, Disp/Refills/DAW tags. |
| **Safety / DUR alert box** | `render_safety_warnings`, `.safety-callout.<tone>` | Title + uppercase badge + body, color-coded by tone (safety/insurance/drug/training). Empty state = green "no warnings." |
| **SIG decoder** | `render_sig_help`, `.sig-decoder` / `.sig-pair` | Token = meaning rows, toggled by a secondary button. |
| **Entry form** | `render_entry_form`, `.form-group-label`, fake-input mirror | Seven fields in three labeled groups; real + example render paths. |
| **Feedback report rows** | `render_feedback_report`, `.report-summary`, `.feedback-item` | Score + per-field rows with status pill, answer boxes, why-note. |
| **Label preview** | `render_label_preview`, `.label-paper` | Printable training label; corrected fields marked `*`; locked behind a gate when ≥4 fields wrong. |
| **Data card** | `_party_card_html`, `.section-card` + `.data-row` | Label/value rows (Patient, Prescriber). |
| **Call-to-action buttons** | `st.button(type="primary"|"secondary")` | One primary per view; See Example is the deep-green exception. |
| **Disclaimer banner** | `.info-disclaimer` (blue) | "Training reference only · not clinical guidance." |

When you need something new, first ask whether one of these can be extended. If you must
add a component, give it a real class in `CUSTOM_CSS` and follow the token table above.

---

## 6. Things to avoid

- **Generic AI / landing-page phrases.** No hero taglines like "The smart way to learn
  pharmacy," no "Trusted by thousands," no feature-grid marketing sections, no testimonials.
- **Gradients.** Surfaces are flat. The palette is solid fills only; no gradient buttons,
  headers, or backgrounds.
- **Random emojis.** The only emoji in the app are the deliberate DUR badge glyphs
  (⚠️ / 💊 / 🧾 / 🧠) inside `safety-callout` badges. Do not sprinkle emoji into headings,
  buttons, copy, or success messages.
- **Startup-ish copy / over-praise.** No "Awesome!", no streak/gamification hype, no
  growth-marketing voice. Measured, instructional tone only.
- **Cluttered layouts.** No more than one primary action per view; don't pack multiple
  panels per row; keep the single-column work surface. Respect the 1400px cap and 12px
  card rhythm.
- **Changing the simulator flow without reason.** Keep all tabs, the seven entry fields and
  their order, and the Check Entry → Try Again → Next Case / See Example behavior. The fill
  order (Rx → DUR → patient → entry → feedback → label) mirrors real practice — don't
  reorder for novelty.
- **New colors or fonts.** Stay inside the token tables. Don't add a brand accent, a second
  font, or dark mode (the app intentionally pins `color-scheme: light` to defeat browser
  auto-dark inversion — see the `CUSTOM_CSS` comment; don't undo that).
- **Inline styles for reusable things, or scattering CSS.** All shared styling goes in the
  single `CUSTOM_CSS` block as named classes.

---

## Quick checklist before shipping a UI change

- [ ] Colors come from the token tables (§2); green=brand/correct, amber=verify, red=wrong.
- [ ] New surface uses the card pattern (white, `#e5e7eb`/`#d1d5db` border, 8px, opens with
      a `.section-label`).
- [ ] Exactly one primary button; copy tells the user the next action.
- [ ] Copy uses pharmacy vocabulary, no SaaS buzzwords, no random emoji, no gradients.
- [ ] Simulator flow, field count/order, and the three sections are unchanged (unless the
      task explicitly calls for it).
- [ ] CSS lives in `CUSTOM_CSS`; validation stays in `checker.py`; case data in `cases.py`.
- [ ] Training-only / fictional disclaimers preserved anywhere a label or fill is shown.
