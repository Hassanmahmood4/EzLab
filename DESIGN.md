---
name: LabPulse
description: Offline lab report auditor that lays a student's own data out as a practical-journal page.
colors:
  navy: "#22305e"
  navy-deep: "#1a2548"
  navy-soft: "#2d3d74"
  navy-tint: "#e8ebf4"
  navy-mist: "#b9c3e4"
  ground: "#f5f6f8"
  sheet: "#ffffff"
  well: "#eceef2"
  rule: "#e1e4e8"
  rule-strong: "#cdd2da"
  ink: "#1e2333"
  body: "#2f3546"
  mute: "#646b7c"
  graphite: "#4a4a4a"
  trace: "#2f7d50"
  trace-strong: "#24643f"
  trace-tint: "#e6f2ea"
  grid: "#cfe6d6"
  grid-fine: "#e8f3ec"
  warn: "#a8620c"
  warn-tint: "#fff4e0"
  warn-rule: "#f0d3a1"
  error: "#b42318"
  error-tint: "#fdecea"
typography:
  headline:
    fontFamily: "Libre Franklin, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.025em"
    fontFeature: "\"tnum\" 1, \"lnum\" 1"
  title:
    fontFamily: "Libre Franklin, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 600
    lineHeight: 1.45
  body:
    fontFamily: "Libre Franklin, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.65
    fontFeature: "\"tnum\" 1, \"lnum\" 1"
  body-sm:
    fontFamily: "Libre Franklin, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Libre Franklin, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.4
  section-head:
    fontFamily: "Libre Franklin, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 700
    letterSpacing: "0.08em"
  caption:
    fontFamily: "Libre Franklin, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.35
  pencil:
    fontFamily: "Libre Franklin, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.625
  mono:
    fontFamily: "JetBrains Mono, ui-monospace, Menlo, Consolas, monospace"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.7
  mono-tag:
    fontFamily: "JetBrains Mono, ui-monospace, Menlo, Consolas, monospace"
    fontSize: "0.625rem"
    fontWeight: 500
rounded:
  sm: "4px"
  md: "6px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  section: "36px"
  top-bar: "56px"
  footer: "32px"
  inputs-pane: "320px"
  files-pane: "400px"
  journal-measure: "832px"
components:
  button-primary:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.sheet}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.navy-soft}"
    textColor: "{colors.sheet}"
  button-primary-active:
    backgroundColor: "{colors.navy-deep}"
    textColor: "{colors.sheet}"
  button-secondary:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.navy}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "40px"
  button-secondary-hover:
    backgroundColor: "{colors.navy-tint}"
    textColor: "{colors.navy}"
  button-quiet:
    textColor: "{colors.navy}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "32px"
  button-quiet-hover:
    backgroundColor: "{colors.navy-tint}"
    textColor: "{colors.navy}"
  button-danger:
    backgroundColor: "{colors.error}"
    textColor: "{colors.sheet}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "32px"
  input-field:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "40px"
  input-field-disabled:
    backgroundColor: "{colors.well}"
    textColor: "{colors.mute}"
  top-bar:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.sheet}"
    height: "{spacing.top-bar}"
  nav-item:
    textColor: "{colors.navy-mist}"
    rounded: "{rounded.sm}"
    padding: "6px 14px"
  nav-item-hover:
    backgroundColor: "{colors.navy-deep}"
    textColor: "{colors.sheet}"
  nav-item-active:
    backgroundColor: "{colors.navy-soft}"
    textColor: "{colors.sheet}"
  journal-head:
    textColor: "{colors.navy}"
    typography: "{typography.section-head}"
  observation-table:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.body}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  observation-row-flagged:
    backgroundColor: "{colors.warn-tint}"
  trace-tag:
    textColor: "{colors.trace}"
    typography: "{typography.mono-tag}"
  pencil-note:
    textColor: "{colors.graphite}"
    typography: "{typography.pencil}"
  audit-badge-warning:
    backgroundColor: "{colors.warn-tint}"
    textColor: "{colors.warn}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
  audit-badge-error:
    backgroundColor: "{colors.error-tint}"
    textColor: "{colors.error}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
  sample-chip:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.body}"
    rounded: "{rounded.full}"
    padding: "4px 10px"
  status-footer:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.mute}"
    typography: "{typography.caption}"
    height: "{spacing.footer}"
---

# Design System: LabPulse

## Overview

**Creative North Star: "The Practical Journal"**

LabPulse reads like the practical journal a Pakistani student has kept since FSc: a ballpoint-navy cover and ruling, white working sheets laid on a cool grey desk, and a review that runs in journal order (Procedure, Observations, Graph, Calculations, Result). The auditor writes in graphite pencil beneath the exact row it concerns; green ink appears only where a value has been traced back to the student's own file. Nothing in the interface is decorative. Every colour, rule and mark either structures the page or tells the student where a number came from.

Density is that of a working tool used weekly, not a showpiece: three panes at desktop width, compact 13–15px text, tabular figures everywhere so columns of readings align. The surface is flat colour on light paper, with no texture, no gradients and no handwriting fonts; the journal metaphor lives in structure (ruled section heads, the Expt. No./Date box, pencil notes, the millimetre grid behind the plot), never in skeuomorphic imitation. Light theme only. Fully offline: both typefaces are bundled locally and no font, script or image is fetched from a CDN.

The system rejects the category's grey card dashboard and the alert-banner audit. Anomalies are not shouted from a banner; they are annotated in place, the way a lab instructor marks a journal.

**Key Characteristics:**
- Ballpoint navy carries the shell, primary actions and section ruling; everything else is ink on white.
- Green is a single-meaning colour: "traced to your data".
- Amber and red appear only for warning and error states, always paired with a distinct shape.
- Uppercase tracked navy section heads sit on a 1.5px navy rule.
- Tabular, lining figures with units throughout; raw logs shown in mono with line numbers.
- Flat sheets with hairline borders and a barely-there sheet shadow.

## Colors

A restrained ballpoint-and-paper palette: one navy voice, cool neutral paper, and three semantic inks that each mean exactly one thing.

### Primary
- **Ballpoint Navy** (navy): the top bar, primary buttons, focus outlines, caret, active tab underline, section-head text and its rule. The one colour with authority on the page.
- **Pressed Navy** (navy-deep): primary button active state and nav hover on the top bar.
- **Lifted Navy** (navy-soft): primary button hover and the active nav item on the top bar.
- **Navy Wash** (navy-tint): hover fill for secondary and quiet buttons, selection highlight, the "edited" wash on prose fields, OK status discs.
- **Faded Navy** (navy-mist): inactive nav labels on the navy bar (7.3:1 on navy).

### Secondary
- **Graph Green** (trace): trace tags, the "values traced" count in the Observations heading, and nothing else. Shipped darker than the direction contract's #3E8E5E because 10px trace tags on white need 4.5:1; this value measures 5.0:1 where the contract value measured 4.0:1.
- **Deep Green** (trace-strong): the lit line number in the raw-log preview when a table value is hovered.
- **Green Wash** (trace-tint): the hover fill on a traced table cell and the lit line in the log preview, linking the two.
- **Millimetre Grid** (grid) and **Fine Grid** (grid-fine): the 50px major and 10px minor lines of the graph sheet behind the plot, and the plot frame's border.

### Tertiary
- **Warning Amber** (warn), **Amber Wash** (warn-tint), **Amber Rule** (warn-rule): warning states only: the "Anomaly corrected" badge, flagged table rows, flagged log lines, the warn icon in pencil notes, setup notices, and the strikethrough decoration on a corrected value.
- **Error Red** (error), **Red Wash** (error-tint): error states only: "Needs checking" badge, ungrounded "not in log" tags, failed-generation titles, field validation, destructive buttons.

### Neutral
- **Cool Desk** (ground): the app background under the sheets; log-preview header strip.
- **Sheet White** (sheet): every working surface: panes, tables, cards, inputs, footer.
- **Well** (well): the deliverables pane background, skeleton bars, disabled inputs, the progress-track channel.
- **Hairline** (rule) and **Firm Hairline** (rule-strong): dividers and container borders; rule-strong for input borders, dashed empty states and the thin scrollbar thumb.
- **Ink** (ink): headings, table headers, the corrected value, primary text.
- **Body** (body): running text and table cells.
- **Mute** (mute): hints, captions, metadata, secondary labels (5.3:1 on white).
- **Graphite** (graphite): the auditor's pencil voice: italic notes and the struck-through original value on warnings.

### Named Rules
**The One Meaning Rule.** Green means "traced to your data" and nothing else. Success, OK, saved and connected states use navy (or neutral graphite), never green.

**The Ink Only For Trouble Rule.** Amber appears only on a warning, red only on an error. A struck-through corrected value is graphite with an amber strike on a warning, and turns red only on an error.

**The Shape Plus Colour Rule.** No state is carried by colour alone. Check, cross, triangle, dashed clock and lock marks each have their own silhouette, and every trace tag has screen-reader text.

## Typography

**Display Font:** none; the system has no display tier.
**Body Font:** Libre Franklin (variable 100–900, roman + italic, bundled), with ui-sans-serif, system-ui, Segoe UI fallback
**Label/Mono Font:** JetBrains Mono (400, 500, bundled), with ui-monospace, Menlo, Consolas fallback

**Character:** Libre Franklin is a sturdy, slightly bookish grotesque that reads like printed lab-manual headings and stays legible at 13px; JetBrains Mono is reserved for the student's raw data and machine identifiers, so the two voices never blur.

### Hierarchy
- **Headline** (700, 1.375rem, tight tracking): the one page title per view: the report's "Lab 05 · Experiment title", History, Profile.
- **Title** (600, 0.9375rem): card titles, the active stage name, empty-state headings, the student's name.
- **Body** (400, 0.9375rem, 1.65): editable report prose in the journal; capped by the 52rem journal measure.
- **Body small** (400, 0.875rem): table cells, page intros, buttons at medium size.
- **Label** (600, 0.8125rem): form labels, table captions ("Table 1. …"), sub-heads inside a section.
- **Section head** (700, 0.78rem, 0.08em tracking, uppercase, navy): the journal's ruled section heads and History column headers. The input pane's group headings (Student, Lab, Raw data) use the same treatment at 0.6875rem in mute.
- **Caption** (400, 0.75rem): hints, metadata lines, the status footer.
- **Pencil** (italic 400, 0.8125rem, 1.625, graphite): auditor notes only.
- **Mono** (400, 0.75rem, 1.7): raw-log lines, record IDs, timings, command snippets.
- **Mono tag** (500, 0.625rem): trace tags ("L14") after a table value.

### Named Rules
**The Tabular Everywhere Rule.** `tnum` and `lnum` are set on the body, so every figure aligns in columns. Numeric table columns are right-aligned; the first column is left-aligned only when it is non-numeric.

**The Mono Is Data Rule.** Mono is for things that came out of a machine (log lines, IDs, line numbers, seconds). Never use it for labels, headings or decoration.

**The Italic Is The Auditor Rule.** Italic is reserved for the pencil voice. Nothing else in the UI is italic.

## Layout

The workspace is a three-pane desk at xl (≥1280px): Inputs fixed at 320px on the left on a white sheet, the journal review fluid in the centre on the cool desk, and Files fixed at 400px on the right on the well. The centre is always the widest pane. Below 1280px the panes collapse to a single column with an Inputs / Review / Files tab strip under the top bar (navy 2px inset underline on the selected tab); the view follows the work to Review when a generation starts.

A 56px sticky navy top bar sits above everything; a 32px status footer (model, RAM, tok/s) appears only at lg and above and is deliberately secondary. The journal column is capped at 52rem and centred, with 36px between sections. Panes pad at 20px; form fields stack at 12px; table cells pad 16px horizontally by 8px vertically. The Generate button is pinned to the bottom of the Inputs pane in its own ruled footer. History and Profile use a centred 72rem container; Profile splits into a form plus a 22rem aside at lg.

**The Journal Order Rule.** The review always runs Procedure, Observations, Graph, Calculations, Result. Observations opens expanded; cover page and procedure are collapsible and start closed.

## Elevation & Depth

Depth is tonal first: white sheets on a cool grey desk, separated by hairline borders. Two shadows exist and both are nearly invisible; they read as paper resting on a desk, not as floating UI.

### Shadow Vocabulary
- **Sheet** (`box-shadow: 0 1px 2px rgb(30 35 51 / 0.06), 0 1px 1px rgb(30 35 51 / 0.04)`): tables, cards, forms, the stage track, the plot image on its graph sheet.
- **Page** (`box-shadow: 0 1px 3px rgb(30 35 51 / 0.12), 0 8px 24px -12px rgb(30 35 51 / 0.18)`): the PDF preview and the empty cover-page placeholder only, the one object that stands for a real printed page.

### Named Rules
**The Paper On A Desk Rule.** Surfaces are flat sheets. Use the sheet shadow for working surfaces and the page shadow only for the document preview; nothing hovers, lifts or glows.

**The Recede Rule.** While one prose field is being edited, every other journal section fades to 45% opacity (200ms, ease-out-quart), so focus is carried by contrast, not by elevation.

## Shapes

Gently rounded, ruled forms. Containers, buttons and inputs share a 6px radius (md); trace tags and nav items use 4px (sm); badges, sample chips, the connection pill and status discs are full pills. Borders do the structural work: 1px hairlines on sheets, 1.5px for emphasis (the navy section rule, the ink rule under table headers, the secondary button outline). Empty and unavailable states use a dashed firm hairline. The Expt. No./Date box is a square-cornered ruled grid in navy, echoing the printed box at the head of a journal page.

**The Millimetre Grid Rule.** The green millimetre graph sheet (50px major, 10px minor) appears only behind the plot, where it is a measurement surface. It is never a page background, card texture or decoration.

## Components

### Buttons
Confident and plain: solid navy for the one action that matters, outlined navy for its sibling.
- **Shape:** gently rounded (6px); 40px tall at medium, 32px at small; semibold label.
- **Primary:** navy fill, white label. Used for Generate report, Download .pdf, Update files, Save profile.
- **Hover / Focus:** hover lifts to navy-soft, press deepens to navy-deep with a 0.98 scale; 150ms colour transition. Focus is a 2px navy outline at 2px offset. Disabled drops to 40% navy and a not-allowed cursor. Loading shows an inline spinner and sets aria-busy.
- **Secondary:** white with a 1.5px navy outline and navy label; hover fills navy-tint. Paired with primary (Download .docx beside Download .pdf).
- **Quiet:** text-only navy; hover fills navy-tint. For Cancel, Discard edits, Keep, row actions.
- **Danger:** red fill, white label; appears only inside an explicit confirm step.

### Chips
- **Style:** sample-lab presets are white pills with a firm hairline and body text; hover turns border and label navy.
- **State:** action chips only; there are no selectable filter chips.

### Cards / Containers
- **Corner Style:** 6px.
- **Background:** sheet white on the desk or the well.
- **Shadow Strategy:** sheet shadow (see Elevation & Depth).
- **Border:** 1px hairline; failure cards switch to a 30% red border with a red title; setup notices use amber wash with an amber rule.
- **Internal Padding:** 20px for cards, 14px for compact notices.

### Inputs / Fields
- **Style:** white, 1px firm-hairline border, 6px radius, 40px tall, 12px horizontal padding; semibold 13px label above, 12px mute hint below, "Optional" set right-aligned in the label row.
- **Focus:** border turns navy with a 2px 15%-navy ring; hover darkens the border slightly.
- **Error / Disabled:** red border with a red message announced via role="alert"; disabled fills the well with mute text.
- **Prose fields:** the journal's editable text reads as plain report prose until hover (hairline border appears) or focus (navy border and ring). An edited field keeps a navy-tint wash with a 35% navy border, and the section head reads "Edited · not in files yet".

### Navigation
- **Style:** a 56px navy bar with the LabPulse wordmark (bold, 17px) and a stroked logo mark, then Workspace / History / Profile as 14px medium links.
- **States:** inactive links in navy-mist; hover fills navy-deep with white text; the current page fills navy-soft with white text and carries aria-current.
- **Local status:** right-aligned pill with a hairline white border reading "Offline · running on this laptop", linking to the System section of Profile. Hidden below md.
- **Mobile:** nav stays inline with reduced padding; the workspace below switches to tabs.

### Journal Section Head (signature)
Small tracked uppercase navy text on a 1.5px navy rule, with an optional right-aligned aside (trace count, "Editable", "From your data" with a lock mark). Collapsible sections add a rotating chevron. This is the page's only heading device inside the review.

### Observation Table with Pencil Notes (signature)
A sheet-white figure with a "Table N." caption, an ink rule under the headers and hairline row dividers. Each traced value carries a trace tag: a green check plus mono line number ("L14") when found, the same in amber when the unit was normalised, a bordered mute "calc" tag when derived, and a red "not in log" tag with a cross when ungrounded. Hovering a traced cell washes it green and lights the matching line in the raw-log preview. A flagged row takes the amber wash (red wash on error), and the auditor's pencil note sits in its own row directly beneath it: amber triangle, the struck original value, an arrow, the corrected value in semibold ink, then the explanation in graphite italic.

### Raw Log Preview
A ruled sheet with a cool-desk header (file name, line count, size) and a numbered mono list capped at 224px tall. Flagged lines carry the amber wash; the hovered line carries the green wash and a deep-green line number, scrolled into view.

### Stage Track
The generation record: a sheet card with the current stage and live seconds in mono, an 8px track where each stage's navy segment is as wide as the time it actually took, and the four stage names beneath with completed durations.

### Audit Badge
A small pill with mark plus words: "No anomalies" (graphite on a hairline outline), "Anomaly corrected" (amber on amber wash), "Needs checking" (red on red wash).

## Do's and Don'ts

### Do:
- **Do** keep navy (#22305e) as the only colour for primary actions, focus and section ruling.
- **Do** use Graph Green (#2f7d50) solely for "traced to your data": trace tags, the traced-values count, and the cell/log-line link.
- **Do** place the auditor's note directly beneath the row it concerns, in graphite italic, with the struck original value and the corrected value in ink.
- **Do** pair every state colour with its own mark (check, cross, triangle, dashed clock, lock) and screen-reader text.
- **Do** set figures tabular and lining, right-align numeric columns, and show units in headers.
- **Do** show the student's raw data in JetBrains Mono with line numbers.
- **Do** bundle every font and asset locally; the app must render identically with Wi-Fi off.
- **Do** label university crests as placeholders wherever their provenance is stated.

### Don't:
- **Don't** use green for success, saved, connected or OK states; use navy or graphite.
- **Don't** use amber or red outside warning and error states, and don't make a warning's struck value red.
- **Don't** announce anomalies in a top-of-page alert banner; annotate them in place.
- **Don't** build the review as a grey card dashboard of metric tiles.
- **Don't** use the millimetre grid anywhere except behind the plot.
- **Don't** add texture, gradients, handwriting fonts or paper skeuomorphism; the journal lives in structure.
- **Don't** use the page shadow on anything but the document preview, or add shadows that lift on hover.
- **Don't** load fonts, scripts or images from a CDN.
- **Don't** add a dark theme without a separate system pass; the system is light-only.
