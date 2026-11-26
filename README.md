# EzLab

**Offline CS lab-report copilot for Pakistani universities.**

Fine-tuned **Qwen2.5-Coder-1.5B** → GGUF **Q4_K_M**, served with **llama.cpp** on Windows + macOS (~1–2 GB RAM). Paste a lab manual, get per-task **code + terminal output**, then export a university-branded **Word (.docx)** and **PDF** — with Wi‑Fi off.

[![Model](https://img.shields.io/badge/Hugging%20Face-ezlab--1.5b--q4__k__m-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/HassanM44/ezlab-1.5b-q4_k_m)
[![Demo](https://img.shields.io/badge/Demo-LinkedIn-0A66C2?logo=linkedin)](https://lnkd.in/p/d3uED8wC)
[![Showcase](https://img.shields.io/badge/Showcase-PR%20%232-111111?logo=github)](https://github.com/junaiddshaukat/finetune-anywhere/pull/2)
[![Runtime](https://img.shields.io/badge/Runtime-llama.cpp-4CAF50)](https://github.com/ggerganov/llama.cpp)
[![Offline](https://img.shields.io/badge/Offline-100%25-22305e)](#)

<p align="center">
  <a href="docs/demo/ezlab_demo.mp4"><strong>▶ Watch the demo reel</strong></a>
  ·
  <a href="https://lnkd.in/p/d3uED8wC"><strong>LinkedIn post</strong></a>
  ·
  <a href="https://huggingface.co/HassanM44/ezlab-1.5b-q4_k_m"><strong>Download GGUF</strong></a>
</p>

---

## The pitch (30 seconds)

University CS students spend hours formatting lab reports while campus labs block cloud AI (or risk leaking coursework). EzLab fine-tunes a **1.5B Qwen coder** on Pakistani CS lab tasks, quantizes it to **Q4_K_M**, and runs it **locally** via llama.cpp. The model emits structured task JSON; a Python pipeline validates, polishes, and renders **DOCX + PDF** with FAST / NUST / GIKI / COMSATS / Bahria (and more) cover pages.

> Not a cheat bot. It needs the real lab manual and grounds solutions in a schema — then formats what a student would submit.

---

## Why judges care

| Criterion | How EzLab hits it |
|-----------|-------------------|
| **Usefulness** | Daily pain: lab manuals → submission-ready DOCX/PDF with campus crests |
| **Technical work** | Custom **LoRA** (Unsloth) on Qwen2.5-Coder-1.5B → merge → **GGUF Q4_K_M** → llama.cpp |
| **Measured results** | Multi-subject prod suite (PF / OOP / DSA / OS / DB / Networks / ML / …) with DOCX+PDF export checks |
| **Runs locally** | ~**1–2 GB RAM**, Wi‑Fi off, macOS + Windows |
| **Write-up & demo** | Public HF model, LinkedIn demo, Kaggle notebook, reproducible repo |

---

## What it does

```text
Lab manual (+ student profile)
        │
        ▼
  llama.cpp  ·  models/labpulse-1.5b-q4_k_m.gguf
  (fine-tuned only — no cloud API)
        │
        ▼
  Strict JSON: { tasks → code, output }
        │
        ▼
  Validator · templates · safe Python exec
        │
   ┌────┴────┐
   ▼         ▼
 .docx     .pdf + cover preview.png
 (docxtpl)   (Typst)
```

### Product surface

| Column | What you see |
|--------|----------------|
| **Inputs** | Student profile, university, lab manual upload, one-click CS presets |
| **Audit** | Task JSON, telemetry (RAM / latency), grounding / polish status |
| **Deliverables** | Cover preview, download **.docx** + **.pdf** |

---

## Before → after (same held-out prompt)

Held-out style prompt: *PF Lab — write `factorial(n)`, print `factorial(5)`, return JSON with `code` and `output`.*

| | Base Qwen2.5-Coder-1.5B | **EzLab (fine-tuned)** |
|--|--|--|
| **JSON** | Incomplete / missing fields | Valid `code` + `output` |
| **Code** | Stub or non-runnable | Typed factorial + `main()` |
| **Stdout** | Empty | `factorial(5) = 120` |

Full before/after strings live in the [showcase `model.yaml`](https://github.com/junaiddshaukat/finetune-anywhere/blob/main/showcase/qwen-local-hackathon-2026/ezlab/model.yaml) (after merge) and in this repo’s hackathon draft.

---

## Quick start

### 1. Model

```bash
hf download HassanM44/ezlab-1.5b-q4_k_m labpulse-1.5b-q4_k_m.gguf --local-dir ./models
# → models/labpulse-1.5b-q4_k_m.gguf  (~940 MB)
```

### 2. Backend + UI

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# PDF engine
# macOS: brew install typst
# or place a typst binary at bin/typst

# Terminal A — API
uvicorn src.api:app --host 127.0.0.1 --port 8080

# Terminal B — UI
cd web && npm install && npm run dev
# → http://localhost:3000  (proxies /backend → :8080)
```

Or: `make demo` for the API, then start the Next.js app as above.

### 3. Smoke test

```bash
make prod-suite   # multi-subject DOCX/PDF/template suite
```

---

## Training pipeline

| Step | Where | What |
|------|--------|------|
| Dataset | `data/generate_dataset.py` | ~3700 CS lab chat pairs (train / valid / test) |
| Fine-tune | [`notebooks/train_lora_kaggle.ipynb`](notebooks/train_lora_kaggle.ipynb) | **Preferred** — Unsloth LoRA on Kaggle GPU |
| Alt | `notebooks/train_lora_colab.ipynb` | Colab (GPU limits) |
| Export | Kaggle notebook | Merge LoRA → GGUF **Q4_K_M** |
| Ship | [Hugging Face](https://huggingface.co/HassanM44/ezlab-1.5b-q4_k_m) | Public GGUF + model card |

**Base:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`  
**Method:** LoRA (r=32, Unsloth / PEFT)  
**Domains:** Programming Fundamentals, OOP, DSA, OS, Databases, Networks, Discrete, ML, and related CS labs common at FAST, NUST SEECS, COMSATS, etc.

---

## Stack

| Layer | Tech |
|-------|------|
| Inference | `llama-cpp-python` · `n_ctx=4096` · Q4_K_M |
| Schema | Pydantic (`src/schema.py`) |
| Pipeline | Manual parse → generate → validate → render (`src/pipeline.py`) |
| API | FastAPI (`src/api.py`) |
| UI | Next.js TypeScript (`web/`) |
| Word | `docxtpl` + university template |
| PDF | Typst (`templates/report_template.typ`) |
| Crests | `assets/logos/` + `assets/universities.json` (~20 Pakistani universities) |

---

## Repo map

```text
EzLab/
├── src/                  # inference, pipeline, validators, renderers, API
├── web/                  # Next.js demo UI
├── data/                 # generate_dataset.py + train/valid/test.jsonl
├── notebooks/            # Kaggle + Colab LoRA → GGUF
├── templates/            # DOCX + Typst
├── assets/               # universities.json + crest PNGs
├── models/               # labpulse-1.5b-q4_k_m.gguf (gitignored; download from HF)
├── docs/demo/            # ezlab_demo.mp4
├── hackathon/            # showcase draft (model.yaml + README)
└── scripts/              # prod_ready_suite.py, e2e render helpers
```

---

## Anti-cheating stance

EzLab is built as an **auditor / formatter**, not a fabulator:

- Requires a real **lab manual** (and student metadata).
- Emits **schema-shaped** task solutions; product path prefers curated templates + syntax / exec gates for demos.
- Keeps data **on-device** — no cloud LLM calls in the runtime path.

---

## Hackathon links

| Resource | Link |
|----------|------|
| Showcase PR | https://github.com/junaiddshaukat/finetune-anywhere/pull/2 |
| Hugging Face GGUF | https://huggingface.co/HassanM44/ezlab-1.5b-q4_k_m |
| Demo post | https://lnkd.in/p/d3uED8wC |
| Demo reel | [docs/demo/ezlab_demo.mp4](docs/demo/ezlab_demo.mp4) |
| Kaggle notebook | [notebooks/train_lora_kaggle.ipynb](notebooks/train_lora_kaggle.ipynb) |

---

## Credits

Built for **Qwen Local Hackathon 2026**.

- **Qwen** / **Qwen Pakistan** — base models & event
- **Junaid Shaukat** — finetune-anywhere & mentorship
- **Unsloth**, **llama.cpp**, **Typst**, **Hugging Face**

Team: [Hassan Mahmood](https://github.com/Hassanmahmood4)

---

## License

Model weights follow **Apache-2.0** (Qwen lineage). University crest PNGs in `assets/logos/` — replace with official artwork for public production if required.
