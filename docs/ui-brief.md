# LabPulse UI Brief

Status: **confirmed.** No UI code until this is approved and a visual direction is chosen.
Product truth lives in `PRODUCT.md`; this brief covers only the `web/` surface.

---

## 1. Job and audience

- **Who:** a Pakistani CS / SE / IT student with a lab report due. They're either at home or in a hostel the night before, or in a campus lab with blocked internet.
- **State of mind:** tired, time-boxed, and wary of AI tools that might leak their work or make up numbers. They've done this every week of the semester.
- **Mode:** Operate. They came to get a job done. The screen must read as a working tool within a second, not a landing page.
- **Need:** raw `.csv` / `.log` plus the lab manual in, and a correct `.docx` and `.pdf` with their university's cover page out, in one sitting.

## 2. Outcome and proof

- **Primary action:** Generate, then Download `.pdf` / `.docx`.
- **Success:** files are downloaded, the student has read the anomaly result, and they trust every table number came from their own file.
- **Proof the UI shows (never claims):**
  - A persistent **"Offline · running on this laptop"** status backed by a real `/health` check. It's never decorative.
  - An **anomaly card** that shows the original value next to the normalized value (`1.85 s → 1850 ms`) in the row where it was found.
  - A **grounding result**: "16 of 16 table values found in your log". Any ungrounded value is listed by name.
- **Never shown:** accuracy percentages, benchmarks, testimonials, usage counts, or anything implying the crests are official.

## 3. Selected direction: Practical Journal

Chosen from the second Impeccable roll (seed:2658e9a748e02d06). Reference sketch: `.impeccable/mocks/decision/model-pick-r1.html`.

- **Thesis:** the review pane follows the order of a practical journal, which every Pakistani science student has kept since FSc: **Observations → Graph → Calculations → Result**. This replaces the generic dashboard of cards. The student already knows the reading order.
- **Visual authority:** the practical journal lends type, palette, density and one signature move. It never supplies layout or controls. Navigation, inputs, tabs and buttons stay standard web components.
- **Palette** (light theme, because the scene is a journal on a desk under a hostel lamp or bright lab lights). Each colour has one job:
  - **Ballpoint navy** `#22305E`: the shell (top bar), primary actions and navigation.
  - **Graph green** `#3E8E5E`: "traced to your data" (grounded values, the data series, the grounding count).
  - **Grid tint** `#CFE6D6`: only inside the plot area, never as a page background.
  - **Graphite** `#4A4A4A`: auditor annotations (pencil notes).
  - **Amber / red**: warning and error, and only those.
  - Working surfaces are white on a cool grey ground (`#F5F6F8`). There are no gradients, grain or paper textures.
- **Type:** one workhorse sans (Libre Franklin in the sketch, bundled locally, not loaded from a CDN).
  - Section heads are small uppercase tracked navy labels sitting on a navy rule, like journal headings.
  - Numbers always use tabular figures and carry their unit.
  - The raw log preview is set in monospace.
  - No handwriting fonts.
- **Signature move: the auditor's pencil notes.**
  - Findings are written in graphite italic directly beneath the row or value they concern, for example *"QuickSort at N = 1,000,000 was logged as 1.85 s; corrected to 1850 ms to match other rows."*
  - The affected row carries an amber tint.
  - The anomaly sits next to its data, not in a separate alert box.
  - The plot is drawn on a fine green millimetre grid, the only place graph paper appears.
- **Carried over from the round as product behaviour:**
  - Each state has a distinct mark, not just a colour: pending, out of date, ungrounded and error.
  - Generation stage bars are sized by real elapsed time.
  - An out-of-date preview is labelled, never silently swapped.
  - Editing one section visually recedes the others.
  - Hovering a table value highlights its source line in the log preview.
  - An ungrounded value gets a crossed mark distinct from the green trace mark.
- **Refused:**
  - Ruled or graph paper as page or table backgrounds.
  - Handwritten fonts.
  - Red-pen grading marks.
  - Notebook spiral or binding costume.
  - A dark neon "AI tool" look.
  - A generic grey card dashboard.

## 4. Scope and boundaries

- **Fidelity:** production-ready, a working Next.js app wired to the real FastAPI backend.
- **Breadth (v1): three routes.**
  1. `/`: **Workspace**, the full flow from inputs to audit, review/edit, and export.
  2. `/history`: **History**, a list of past reports to reopen, re-download, or delete.
  3. `/profile`: **Profile & setup**, the saved student profile plus system status (model found, Typst found, offline).
- **Out of scope for v1:**
  - Circuit photo input (the model is text-only and the scope is CS).
  - TA/instructor views and accounts or login.
  - Cloud anything.
  - Base-vs-fine-tuned toggle.
  - Telemetry as a headline feature.
- **Anti-goals (feels wrong even if polished):**
  - Chat-bot UI or a "write my lab" prompt box.
  - A marketing hero on the workspace.
  - Spinners with no stage information during a 30–90 s generation.
  - Silently "fixing" data.
  - Editable tables that let students change numbers.
  - Dashboard-style RAM/tokens charts competing with the report.

## 5. States and ranges

**Realistic content ranges**

| Thing | Min | Typical | Max |
|---|---|---|---|
| Raw log rows | 3 | 10–40 | ~500 |
| Tables in report | 1 | 1–2 | 4 |
| Anomaly flags | 0 | 1 | 5 |
| Generation time (CPU) | ~15 s | 30–60 s | ~120 s |
| History entries | 0 | 10–15 | ~50 per semester |

**States the design must cover**

- **First run:** no saved profile. The workspace asks for profile details inline (not in a modal), then saves them and collapses them to a one-line summary.
- **Setup problems** (blocking, with exact fixes):
  - Model file missing: show the expected path `models/labpulse-1.5b-q4_k_m.gguf`.
  - Backend not running: show the command to start it.
  - Typst missing: `.docx` still works, and the PDF is shown as unavailable along with the reason.
- **Empty workspace:** a clear drop zone for data plus a quiet "Try a sample" row with three presets: *PF Loop Runtime w/ Unit Bug*, *OOP Unit-Test Coverage*, *OS Scheduling Lab*.
- **Input errors:**
  - Unsupported file type, empty file, or file too large.
  - No parsable numbers.
  - Lab manual missing.
  - Each error is shown inline at the field it belongs to.
- **Data loaded:** a preview of the first rows of the file, so the student can confirm they picked the right one.
- **Generating:**
  - Named stages: Reading data → Auditing → Writing report → Validating → Rendering files.
  - Elapsed time and a Cancel button.
  - Inputs locked but visible.
- **Model output invalid:** the app retries once automatically. If that also fails, show a plain explanation with Retry, and keep the inputs.
- **Audit results:**
  - `ok`: a calm confirmation.
  - `warning`: flags listed with before → after values.
  - `error`: data the model couldn't reconcile, with the student told what to check in their file.
- **Grounding partial:** ungrounded values are highlighted in the table preview, and export still works with a visible caution.
- **Editing:** prose sections and cover fields are editable. Once something changes, the preview is marked out of date until **Update files** re-renders it.
- **Success:**
  - PDF preview, plus `.pdf` and `.docx` download buttons that are the most prominent things on screen.
  - The report is saved to History automatically.
- **History:**
  - Empty: a single line pointing back to the workspace.
  - Populated: rows sortable by date, with course, lab number, and anomaly status.
  - Reopening an entry loads it back into the editable review.
  - Deleting asks for confirmation.

## 6. Interaction and layout (intent, not CSS)

- **Shell:**
  - A slim top bar with LabPulse, navigation (Workspace / History / Profile), and the persistent offline status.
  - No sidebar app chrome beyond that.
  - A footer status strip carries secondary telemetry: RAM, tok/s, last generation time.
- **Workspace at ≥1280 px:** three panes, matching the student's reading order.
  1. **Inputs** (narrow): profile summary, university (auto-detected from the profile, with override), lab manual, and data file. Generate sits at the bottom.
  2. **Review** (widest), in journal order:
     - **Observations:** the table or tables, with pencil-note anomalies under their rows.
     - **Graph.**
     - **Calculations:** the equations.
     - **Result:** abstract, discussion and conclusion.
     - Methodology and apparatus sit in a collapsible "Procedure" section above Observations.
     - Prose is editable in place. Tables, equations and the plot carry a small "from your data" mark and are locked.
  3. **Deliverables:** live PDF preview with the two download buttons pinned above it.
- **Workspace at 1024–1279 px** (common 1366×768 lab monitors): inputs collapse to a summary after generation. Review and Deliverables share the space as two panes.
- **Under 1024 px:** a single column with tabs: Inputs · Review · Files. It's not a primary target, but it must not break.
- **Before first generation:** Review and Deliverables show purposeful empty states, not blank boxes. The inputs pane is the focus.
- **Keyboard:**
  - Full tab order through the form.
  - `Ctrl/Cmd+Enter` generates, and `Ctrl/Cmd+S` runs Update files while editing.
  - Visible focus rings.
- **Motion:** minimal and functional. Stage progress advances, the audit card arrives, and the preview cross-fades when it's re-rendered. Respects `prefers-reduced-motion`.
- **Feedback:**
  - Every async action shows its state where the action happened.
  - Toasts only for background events (saved to History, file downloaded).

## 7. Constraints and open decisions

- **Platform:**
  - Next.js (TypeScript, strict) on `:3000`, calling FastAPI on `127.0.0.1:8080`.
  - Must work fully offline on Windows and macOS.
  - No CDN fonts, no external scripts, no telemetry calls. Everything is bundled.
- **Backend endpoints this UI implies** (to build in `src/api.py`):
  - `GET /health`
  - `GET /universities`
  - `GET` and `PUT /profile`
  - `POST /generate`, streaming stage progress over SSE
  - `POST /render`, which re-renders an edited report
  - `GET /reports`, `GET /reports/{id}`, `DELETE /reports/{id}`
  - `GET /reports/{id}/files/{pdf|docx}`
- **Storage:** profile and history live on disk under `outputs/`. It's all local and deletable from the UI.
- **Accessibility:**
  - WCAG AA contrast.
  - Status is never conveyed by colour alone. Anomaly states carry an icon and a text label too.
  - Labelled inputs and announced stage changes.
- **Language:** English UI. Names and university strings must handle Urdu-origin spellings and long official names without truncation on the cover summary.
- **Lab manual input:** students can paste text or upload `.txt`, `.md`, `.pdf` or `.docx`. Files are parsed locally (`pypdf`, `python-docx`), and the extracted text is shown in an editable box so the student can trim it. Scanned PDFs with no text layer show an inline error asking for pasted text (no OCR in v1).
- **Theme:** light only in v1, as set by the Practical Journal direction. A dark mode can come later as a deliberate addition.
