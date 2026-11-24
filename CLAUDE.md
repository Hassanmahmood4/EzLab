# CLAUDE.md — Offline Lab-to-Report & Anomaly Copilot (Pakistani University Edition)

## 1. Project Overview & Core Value Proposition

**Project Name:** LabPulse (or `lab-report-copilot`)  
**One-Line Summary:** A 100% offline, lowest-resource, cross-platform (Windows + macOS) LoRA-fine-tuned **`Qwen2.5-1.5B-Instruct`** system served via **llama.cpp (GGUF `Q4_K_M`)** that audits university students' raw lab logs/CSVs/circuit photos for unit errors and anomalies, generates grounded academic analysis, and compiles submission-ready **Word (`.docx`)** and **PDF (`.pdf`)** reports with official Pakistani university cover pages.

### The Problem & Academic-Integrity Positioning
- **Student & Faculty Pain Points:** University engineering and CS students spend hours formatting LaTeX/Word tables, writing equations, and debugging broken layouts, while TAs/professors grade inconsistent submissions—often inside restricted-internet university computer labs where cloud AI APIs are blocked or risk leaking student data.
- **Anti-Cheating Guardrail (Crucial Framing):** This tool **does not fabricate lab work from scratch**. It requires the student's actual experimental artifacts (raw `.csv` sensor/oscilloscope readings, terminal `.log` outputs, or breadboard/circuit photos), audits those raw logs for unit mismatches (e.g., `4.2 A` mixed into `mA` readings) and statistical outliers, and strictly grounds every table cell in the uploaded input data.

### Judge Elevator Pitch
> "University engineering and computer science students spend hours every week formatting lab reports in Word or PDF and manually cross-checking raw experimental logs, while professors and TAs have to grade inconsistent submissions—often inside restricted-internet labs where cloud AI tools are blocked or risk leaking student data. To solve this, we fine-tuned a custom LoRA on Qwen2.5-1.5B in Google Colab, merged and quantized it to GGUF Q4_K_M, and run it with llama.cpp so the same low-RAM offline stack works on Windows and macOS (~1–2 GB). The model converts raw lab artifacts—CSV readings, terminal outputs, or circuit photos—into a verified structured schema, audits unit mismatches and sensor anomalies, then exports both an editable Word document and a print-ready PDF in one click. On our held-out evaluation suite, the Lab LoRA substantially outperformed the base GGUF model in schema validity and numerical accuracy—and the Colab notebook, adapters, and eval script are in the repo for reproduction."

---

## 2. Hackathon Judging Rubric Alignment

Every architectural decision maps directly to the 5 official judging criteria:

1. **Usefulness:** Solves a daily workflow bottleneck for both university students (instant `.docx` + `.pdf` formatting, math/plots, cover page auto-fill) and TAs/instructors (automated anomaly/unit-mismatch audit and uniform report structure).
2. **Technical Work:** Combines **GGUF 4-bit quantization (`Q4_K_M`)** with a **custom LoRA fine-tune** (Hugging Face PEFT / Unsloth on Colab) trained on domain-specific Pakistani university lab tasks — inference via **llama.cpp** (`llama-cpp-python`) on Windows and macOS with minimal RAM.
3. **Measured Results:** Includes an automated `eval.py` benchmark (run on Colab or once locally) comparing *Base GGUF* vs. *Lab LoRA GGUF* for the write-up table — Strict JSON Validity %, Numerical Grounding Accuracy %, Unit Anomaly Recall %, University Alias F1, Dual `.docx`/`.pdf` Export Success %, Peak RAM (GB), and Tokens/sec. The **product app loads only the fine-tuned model**.
4. **Runs Locally:** Executes 100% offline on **Windows and macOS** via llama.cpp with Wi-Fi disabled. Target footprint ~**1–2 GB RAM** with `Qwen2.5-1.5B` Q4_K_M.
5. **Write-Up & Demo:** Reproducible repository with Colab notebook, LoRA adapters, fine-tuned GGUF, `data/test.jsonl`, `eval.py`, a `Makefile`, and a single-model demo UI (no Base/Lab toggle).

---

## 3. System Architecture & Data Flow

```text
[Lab Manual / Task Prompt] + [Raw .csv / Terminal .log / Circuit Photo] + [Student Profile]
                                           │
                                           ▼
                   llama.cpp (Windows + macOS) via llama-cpp-python
                   Fine-tuned only: models/labpulse-1.5b-q4_k_m.gguf
                   In-process GGUF load → strict JSON output
                                           │
                                           ▼
                    Python Grounding, Math & Anomaly Validator
                    • Validates Pydantic JSON schema
                    • Verifies every table number exists in raw CSV/log
                    • Executes matplotlib plot_code safely -> plot.png
                    • Resolves university_id -> Official Name & PNG Crest
                              ┌────────────┴────────────┐
                              ▼                         ▼
                   Word Renderer (.docx)      PDF Renderer (.pdf)
                   docxtpl (InlineImage +     Typst (`typst compile`)
                   university_template.docx)  (Fast single binary, <100ms)
```

### Why Structured JSON Instead of Raw LaTeX Generation?
- Unadapted small models frequently leave `\begin{tabular}` unclosed or break LaTeX escaping (`%`, `&`, `_`), and cannot natively output both `.docx` and `.pdf`.
- By fine-tuning Qwen2.5 to emit a **single deterministic JSON object**, local Python renderers (`docxtpl` and `typst`) deterministically format cover pages, crests, tables, equations, and plots into **both `.docx` and `.pdf`** with zero layout corruption.

---

## 4. Target Hardware & Tech Stack

- **Target Machines:** **Windows 10/11** and **macOS** (8 GB RAM usable; 16 GB comfortable). Same llama.cpp path on both.
- **Why llama.cpp (least resources):**
  - Loads **GGUF** directly — no Docker, no Ollama daemon, no MLX/CUDA framework tax.
  - CPU works everywhere; Metal (macOS) / Vulkan or CUDA (Windows) optional accelerators.
  - Default model **Qwen2.5-1.5B-Instruct Q4_K_M** ≈ **~1.1 GB** on disk / **~1–2 GB** RAM at runtime.
- **Where heavy work runs:**
  - **Google Colab (GPU):** PEFT / Unsloth LoRA train → merge → **GGUF Q4_K_M** export.
  - **Local laptop (light):** `llama-cpp-python` inference + validators + `.docx`/`.pdf` + Next.js — no training on the laptop.
- **Model & Inference Engine (cross-platform):**
  - Runtime: **llama.cpp** via **`llama-cpp-python`** (in-process; used by `src/inference.py`).
  - **App model (only):** `models/labpulse-1.5b-q4_k_m.gguf` — merged LoRA from Colab. No Base/Lab toggle in the UI.
  - **Eval-only base** (optional, for README benchmark): stock `Qwen2.5-1.5B` Q4_K_M compared in `eval.py` / Colab, not shipped in the product path.
  - Optional upgrade if machine allows: fine-tune `Qwen2.5-3B-Instruct` instead (~2 GB).
  - Settings: `n_ctx=4096`, `n_gpu_layers=-1` when GPU/Metal available else `0`, `temperature=0.1` for JSON.
- **Document & Plotting Stack:**
  - Word Export: `docxtpl` + `python-docx`.
  - PDF Export: `typst` CLI (macOS: `brew install typst`; Windows: scoop/choco or official zip).
  - Plots: `matplotlib` (headless `Agg`, 300 DPI `plot.png`).
- **Demo UI:** FastAPI (`src/api.py`) + Next.js (`web/`) — `:3000` → `:8080`.

---

## 5. Repository Structure

Build and maintain this exact folder layout:

```text
lab-report-copilot/
├── CLAUDE.md                       # Master architectural specification (this file)
├── README.md                       # Reproducible write-up + before/after benchmark table
├── Makefile                        # One-command targets: setup, data, train, eval, demo
├── requirements.txt                # llama-cpp-python, docxtpl, pydantic, matplotlib, fastapi
├── notebooks/
│   └── train_lora_colab.ipynb      # Colab: PEFT/Unsloth train → merge → GGUF
├── web/                            # Next.js (TypeScript) 3-column demo frontend
├── assets/
│   ├── universities.json           # Canonical registry of Pakistani universities
│   └── logos/                      # Transparent 300x300 PNG crests (nust.png, fast_nuces.png, etc.)
├── templates/
│   ├── master_cover.docx           # Styled Word template with Jinja2 tags & {{ university_logo }}
│   └── report_template.typ         # Typst template reading resolved_report.json
├── data/
│   ├── generate_dataset.py         # Generates 400 synthetic Pakistani STEM/CS lab pairs
│   ├── train.jsonl                 # 340 training examples (chat messages format)
│   ├── valid.jsonl                 # 30 validation examples
│   └── test.jsonl                  # 30-60 held-out test examples for eval.py
├── adapters/
│   ├── adapter_model.safetensors   # PEFT LoRA weights from Colab (~25-50 MB)
│   └── adapter_config.json
├── models/                         # Local GGUF weights (gitignored)
│   └── labpulse-1.5b-q4_k_m.gguf   # Fine-tuned model only (app runtime)
├── src/
│   ├── schema.py                   # Pydantic models for strict output validation
│   ├── inference.py                # llama.cpp loader for labpulse GGUF + telemetry
│   ├── validator.py                # Checks numerical grounding against raw CSV/logs + runs plot_code
│   ├── renderer_docx.py            # Renders .docx via docxtpl + InlineImage
│   ├── renderer_pdf.py             # Renders .pdf via Typst CLI
│   └── api.py                      # FastAPI local backend for the TypeScript demo UI
└── eval.py                         # Optional base-vs-lab benchmark for README (not used by UI)
```

---

## 6. Strict Output JSON Schema (`src/schema.py`)

Every model generation MUST conform to this exact JSON structure:

```json
{
  "cover_page": {
    "university_id": "fast_nuces",
    "university_raw": "FAST-NU Isb",
    "department": "Department of Computer Science",
    "course_code": "CS-218",
    "course_title": "Data Structures and Algorithms Lab",
    "lab_number": "Lab 05",
    "experiment_title": "Empirical Runtime Comparison of MergeSort and QuickSort",
    "student_name": "Hassan Ali",
    "registration_no": "21I-1234",
    "section": "BCS-4A",
    "instructor": "Dr. Ayesha Khan",
    "submission_date": "2026-11-23"
  },
  "anomaly_check": {
    "status": "warning",
    "flags": [
      "N=1000000 QuickSort runtime recorded as 1.85 s while sibling rows use ms (1000x unit mismatch detected and normalized to 1850 ms)."
    ]
  },
  "report_body": {
    "abstract": "Concise 3-4 sentence academic summary of objective, setup, and key quantitative result.",
    "apparatus": [
      "GCC 13 / Clang toolchain",
      "Python 3.11 timing harness",
      "CSV runtime log (input size N vs wall-clock time)"
    ],
    "methodology": "Past-tense, step-by-step experimental procedure derived from the lab manual.",
    "equations_latex": [
      "T_{\\text{avg}}(N) = \\frac{1}{k}\\sum_{i=1}^{k} t_i(N)",
      "\\text{Speedup} = \\frac{T_{\\text{MergeSort}}}{T_{\\text{QuickSort}}}"
    ],
    "tables": [
      {
        "caption": "Average Runtime (ms) vs Input Size N",
        "headers": ["N", "MergeSort (ms)", "QuickSort (ms)", "Speedup"],
        "rows": [
          ["1000", "0.42", "0.31", "1.35"],
          ["100000", "58.2", "41.7", "1.40"],
          ["1000000", "712.0", "1850.0", "0.39"]
        ]
      }
    ],
    "plot_code": "import matplotlib.pyplot as plt\nn = [1000, 100000, 1000000]\nmerge = [0.42, 58.2, 712.0]\nquick = [0.31, 41.7, 1850.0]\nplt.figure(figsize=(6, 4))\nplt.plot(n, merge, 'o-', label='MergeSort')\nplt.plot(n, quick, 's--', label='QuickSort')\nplt.xscale('log')\nplt.yscale('log')\nplt.xlabel('Input Size N')\nplt.ylabel('Runtime (ms)')\nplt.title('Sorting Runtime vs N')\nplt.legend()\nplt.grid(True, which='both', ls=':')\nplt.tight_layout()\nplt.savefig('plot.png', dpi=300)",
    "discussion": "Technical analysis of asymptotic trends, constant factors, anomaly impact, and implementation bottlenecks.",
    "conclusion": "Concise synthesis confirming whether experimental results validated theoretical expectations."
  }
}
```

---

## 7. Pakistani University Asset Registry (`assets/universities.json`)

The LoRA adapter must normalize messy campus shorthand (e.g., `"SEECS NUST"`, `"FAST-NU Isb"`, `"Pak Austria"`, `"Bahria Uni"`, `"IIUI"`, `"PUCIT"`) into canonical `university_id` slugs in `assets/universities.json` (**20 universities**):

`nust`, `fast_nuces`, `comsats`, `uet_lahore`, `giki`, `pieas`, `lums`, `ned`, `air_university`, `itu`, `qau`, `pu`, **`pak_austria`**, **`bahria`**, **`iiui`**, **`numl`**, **`szabist`**, **`iba`**, **`riphah`**, **`uet_taxila`**.

Example aliases: `"PAF-IAST"` / `"Pak Austria"` → `pak_austria`; `"BUIC"` / `"Bahria Uni"` → `bahria`; `"Islamic Uni Isb"` / `"IIUI"` → `iiui`; `"NUML"` → `numl`; `"SZABIST"` → `szabist`; `"IBA Khi"` → `iba`; `"Riphah"` → `riphah`; `"UET Taxila"` → `uet_taxila`.

*Full official names + logo paths live in `assets/universities.json`. Placeholder crests are generated by `assets/generate_placeholder_logos.py`.*

---

## 8. Synthetic Dataset & Colab LoRA → llama.cpp (Windows + macOS)

### Dataset Generation (`data/generate_dataset.py`)
Generate **~1000–1200 CS-focused university lab examples** (~850 train, ~75 valid, ~75–100 test). **No EE / mechanical engineering domains.** Target ~60–75 samples across **16 CS/SE/IT lab subjects** common in Pakistani universities (FAST, NUST SEECS, COMSATS, PUCIT, etc.):

1. **Programming Fundamentals** — I/O, loops, arrays; runtime / test-case pass-fail logs (inject `ms` vs `s` timer bugs).
2. **Object-Oriented Programming (OOP)** — classes, inheritance, polymorphism labs; unit-test / coverage CSV outputs.
3. **Data Structures** — stacks, queues, linked lists, trees; operation-count and memory logs.
4. **Algorithms / Analysis** — sorting & searching benchmarks (`MergeSort` vs `QuickSort`) across $N=10^3 \dots 10^6$ (inject timer unit anomalies).
5. **Discrete Structures / Logic** — truth tables, predicate examples; correctness / counterexample logs.
6. **Digital Logic Design (CS track)** — combinational circuits, K-maps; simulation truth-table outputs (CS-oriented, not EE labs).
7. **Database Systems** — SQL queries, joins, indexing; query-time / row-count result logs.
8. **Operating Systems** — process scheduling (`FCFS`, `SJF`, `Round Robin`); turnaround/waiting-time CSVs.
9. **Computer Networks** — sockets, latency, throughput, packet loss traces.
10. **Software Engineering** — requirements/test cases; defect-count and test-pass-rate logs.
11. **Web Technologies** — HTTP status, page-load timings, API response logs.
12. **Artificial Intelligence / ML Intro** — accuracy, loss, confusion-matrix metrics from small experiments.
13. **Information Security** — hash/encrypt timing or password-strength experiment logs.
14. **Theory of Automata** — DFA/NFA acceptance traces; string accept/reject tables.
15. **Compiler Construction** — lexer/parser test suites; token-count and error logs.
16. **Human–Computer Interaction / HCI** — usability task times, SUS-style score sheets (numeric CSV).

Each example still injects realistic anomalies (wrong time units, outlier runtimes, mismatched counters) and noisy campus aliases (`FAST-NU Isb`, `SEECS NUST`, `CUI Wah`, etc.) while requiring the model to ground every table cell in the raw log.

Each example in `train.jsonl` uses standard chat format (HF / Unsloth / llama.cpp):
```json
{
  "messages": [
    {"role": "system", "content": "You are an offline university lab report auditor and generator. Audit raw experimental data for unit mismatches or outliers, extract cover page metadata, and output strictly valid JSON matching the required schema. Do not fabricate data."},
    {"role": "user", "content": "STUDENT PROFILE: ...\nLAB MANUAL: ...\nRAW DATA LOG:\n..."},
    {"role": "assistant", "content": "{...valid ground-truth JSON...}"}
  ]
}
```

### Colab Training → GGUF → llama.cpp (`notebooks/train_lora_colab.ipynb`)
Train on Colab GPU so laptops stay light:

1. Load **`Qwen/Qwen2.5-1.5B-Instruct`** with Unsloth / PEFT (smallest viable instruct model).
2. LoRA: `r=16`, `lora_alpha=32`, `lora_dropout=0.05`, target attention projections.
3. Train on `data/train.jsonl` (~1–3 epochs), validate on `valid.jsonl`.
4. Merge LoRA → convert with `llama.cpp` `convert_hf_to_gguf.py` + `llama-quantize` → **`Q4_K_M`**.
5. Download **`labpulse-1.5b-q4_k_m.gguf`** into local `models/` — this is the **only** model the app loads.
6. Optionally keep a stock base GGUF on Colab (or locally) solely for `eval.py` before/after numbers in the README.

### Least-resource knobs (`src/inference.py`)
```python
Llama(
    model_path=...,
    n_ctx=4096,
    n_threads=max(2, os.cpu_count() // 2),
    n_gpu_layers=-1,   # Metal/CUDA if present; else set 0 for CPU-only
    logits_all=False,
    embedding=False,
    verbose=False,
)
```

---

## 9. Evaluation Harness (`eval.py`) & Benchmark Table

`eval.py` (write-up only; not exposed in the UI) runs over `data/test.jsonl` and can compare:
1. **Base** — stock `Qwen2.5-1.5B` Q4_K_M (eval artifact)
2. **Lab** — `models/labpulse-1.5b-q4_k_m.gguf` (the model the app actually uses)

### Automated Metrics Computed by `eval.py`:
- **Strict JSON Schema Validity %:** Output parses via `json.loads()` and passes `LabReportSchema.model_validate()` on the first pass with zero repair regexes.
- **Numerical Grounding Accuracy %:** Extracts all numeric values from `report_body.tables` and verifies they match (or are valid arithmetic derivations of) numbers in the raw input `.csv`/log.
- **Unit Anomaly Recall %:** Percentage of injected unit mismatches (`A` vs `mA`, `s` vs `ms`) explicitly caught in `anomaly_check.flags`.
- **University Alias Extraction F1:** Exact match accuracy on normalized `university_id` from noisy campus headers (`SEECS NUST` $\rightarrow$ `nust`).
- **Dual `.docx` + `.pdf` Export Rate %:** Percentage of test cases where `plot_code` executes cleanly, `renderer_docx.py` produces a valid `.docx`, and `typst compile` exits with code `0`.
- **Hardware Telemetry:** Process RSS / peak RAM (GB) via `psutil` and generation throughput (`tokens/sec`) from llama.cpp timings.

---

## 10. Live Demo UI & 3-Minute Pitch Flow

### 3-Column Local Web UI (`web/` Next.js + `src/api.py` FastAPI)
Built last, after inference/eval work. Stack: Next.js (TypeScript) frontend calling a local FastAPI API.

1. **Left Column (Inputs & Controls):**
   - **Student Profile Inputs:** Name, Reg No., Section, University dropdown (with auto-detect option)
   - **Lab Manual Text / File Upload** + **Raw `.csv` / `.log` Upload** (with 3 one-click preset demo buttons: *PF Loop Runtime w/ Unit Bug*, *OOP Unit-Test Coverage*, *OS Scheduling Lab*)
2. **Center Column (Audit & Telemetry):**
   - **Anomaly & Grounding Card:** Highlights caught unit mismatches (`1.85 s -> 1850 ms`) and grounding verification badge
   - **Live Hardware Telemetry:** Peak RAM (GB), Speed (tok/s), Latency (s), Offline Status badge
   - **Collapsible Raw JSON Inspector**
3. **Right Column (Live Deliverables):**
   - **Embedded PDF Preview** (renders generated PDF cover page + body + matplotlib plot)
   - **Download `.docx` Button** & **Download `.pdf` Button**

### Live Stage Demo Script (3 Minutes)
1. **0:00–0:25:** Turn **Wi-Fi OFF** and show low RAM (~1–2 GB for the 1.5B Q4 model).
2. **0:25–1:30:** Click the *PF Loop Runtime w/ Unit Bug* or *DSA Sorting* preset → Generate — show caught `1.85 s -> 1850 ms`, FAST/NUST cover page, plot, and open `.pdf` / `.docx`.
3. **1:30–2:15:** Run a second preset (*OOP Unit-Test Coverage* or *OS Scheduling*) to show CS domain coverage.
4. **2:15–3:00:** Point to the README benchmark table (base vs fine-tuned from `eval.py` / Colab) for measured results.

---

## 11. Step-by-Step Build Execution Order

When building this project, execute in this sequence:
1. Scaffold directory structure, `requirements.txt`, `assets/universities.json`, and placeholder PNG crests.
2. Implement `src/schema.py` (Pydantic schemas) and `data/generate_dataset.py` to generate `train.jsonl`, `valid.jsonl`, and `test.jsonl`.
3. Implement `src/validator.py`, `src/renderer_docx.py` (generating `templates/master_cover.docx` programmatically if not present), and `src/renderer_pdf.py` (`templates/report_template.typ`). Test end-to-end rendering on a ground-truth sample from `test.jsonl`.
4. Train on **Google Colab** (`notebooks/train_lora_colab.ipynb`): PEFT/Unsloth LoRA → merge → GGUF Q4_K_M → download into `models/` for llama.cpp on Windows or macOS.
5. Implement `src/inference.py` (llama.cpp loads fine-tuned `labpulse` GGUF only) and `eval.py` (optional base-vs-lab for README), then populate the benchmark table.
6. Build Next.js (TypeScript) frontend (`web/`) + FastAPI backend (`src/api.py`) for the 3-column demo UI and verify full offline operation with Wi-Fi disabled on **both Windows and macOS**.