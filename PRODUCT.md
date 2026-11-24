# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Next.js (TypeScript) frontend in `web/`, talking to a local FastAPI backend (`src/api.py`) on the same machine. Inference runs in-process via llama.cpp (`llama-cpp-python`) on a single fine-tuned GGUF (`models/labpulse-1.5b-q4_k_m.gguf`). Must run on Windows and macOS with no internet.

## Users

Pakistani university CS / SE / IT students writing weekly lab reports. Two equally important situations:

- Alone at home or in a hostel, finishing a report against a deadline.
- In a campus computer lab where internet is restricted, blocked, or unreliable.

Their job: upload the week's lab manual, fill in their name and university once, and download a submission-ready report with that university's cover page — without fighting Word layout.

Secondary audience (not designed for in v1): TAs and instructors who receive the reports.

## Product Purpose

LabPulse writes a complete lab report from the student's lab manual and personal details, then exports it as both an editable `.docx` and a print-ready `.pdf`. Success means a student goes from manual to downloaded files in one sitting, on this laptop, with nothing uploaded.

## Positioning

Everything runs locally: a fine-tuned 1.5B model on the student's own laptop, with no account, no cloud API, and no upload. Student data never leaves the machine, and the tool keeps working with Wi-Fi off. This is the first thing the product must communicate.

## Operating Context

- Laptops with 8–16 GB RAM, Windows 10/11 or macOS, often older hardware.
- Opened in a local browser tab pointing at the app on the student's own machine.
- Used weekly, repeatedly, across a semester. It is a daily tool, not a one-off demo.
- Inputs: student profile (name, registration no., section, instructor, date), university (noisy campus names like "FAST-NU Isb", "Bahria Uni", "IIUI"), and the lab manual (paste or `.pdf` / `.docx` / `.txt`). A raw `.csv` / `.log` is optional.
- Generation takes real seconds on CPU; waiting is part of the experience.

## Capabilities and Constraints

- Covers 16 CS lab subjects: Programming Fundamentals, OOP, Data Structures, Algorithms, Discrete Structures, Digital Logic (CS track), Databases, Operating Systems, Networks, Software Engineering, Web, AI/ML, Information Security, Theory of Automata, Compilers, HCI. No EE or mechanical labs.
- 20 Pakistani universities with canonical IDs and crests (`assets/universities.json`).
- Output is strict JSON (cover page, anomaly check, abstract, apparatus, methodology, equations, tables, plot, discussion, conclusion), rendered to `.docx` (docxtpl) and `.pdf` (Typst).
- Anomaly check returns `ok` / `warning` / `error` plus human-readable flags, such as a timing value logged in seconds among millisecond rows.
- Single model only; no base-vs-fine-tuned toggle in the product.
- Writes the full report from the lab manual and the student's details. A measurements file is optional, not required.
- Students can edit report prose and cover-page fields before export. Tables, equations, and the plot stay locked; changing those means regenerating.
- Past reports are kept in a local history on disk and can be reopened and re-downloaded. Nothing syncs anywhere.
- The student profile is saved locally so it is entered once per semester, not every week.

## Brand Commitments

- Name: LabPulse.
- The product writes the weekly lab from the official manual plus the student's own cover-page details. Copy is plain: "Generate report", never a chatbot.

## Evidence on Hand

- Synthetic dataset: 1,120 examples across 16 subjects (`data/`).
- A working end-to-end render: `outputs/e2e/report.docx` and `report.pdf`.
- University crests in `assets/logos/` are generated placeholders, not official artwork. Do not present them as official.
- No benchmark numbers yet. The README table is empty; do not show or invent accuracy figures in the UI.
- No user testimonials, usage stats, or institutional endorsements exist. Do not fabricate them.

## Product Principles

1. **Local by default, and visibly so.** Offline status and "nothing uploaded" should be evident, not buried in settings.
2. **Manual in, report out.** The student should not need a CSV before they can download `.docx` and `.pdf`.
3. **A weekly tool, not a show.** Calm, fast, repeatable flows beat demo theatrics. Telemetry and presets are secondary.
4. **Deliverables are the finish line.** The session ends with `.docx` and `.pdf` in hand; everything else serves that.
