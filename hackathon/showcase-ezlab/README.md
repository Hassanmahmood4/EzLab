# EzLab — Offline CS Lab Report Copilot

## What it does

EzLab helps Pakistani CS students turn a lab manual into a submission-ready **Word (.docx)** and **PDF** report on a laptop with **Wi‑Fi off**. The fine-tuned Qwen model writes per-task **code** and **terminal output**; a local Python pipeline validates, runs Python solutions when safe, and renders university cover pages (crests for FAST, NUST, GIKI, COMSATS, etc.).

## Why we built it

Students waste hours formatting lab reports. Campus labs often block cloud AI, and uploading raw student work to SaaS APIs is risky. A small **LoRA on Qwen2.5-Coder-1.5B**, served as **GGUF Q4_K_M** via **llama.cpp**, fits ~1–2 GB RAM and stays fully offline.

## Dataset

- **Source:** Synthetic chat JSONL (`data/generate_dataset.py`) covering CS labs common in Pakistani universities (PF, OOP, DSA, OS, DB, Networks, Discrete, ML, …).
- **Size:** 3200 train / 250 valid / 250 test (~3700 total).
- **License / repo:** https://github.com/Hassanmahmood4/Labpulse/tree/main/data  
- Examples inject noisy campus aliases and unit anomalies; assistants must emit schema-valid task JSON grounded in the prompt.

## Training

- **Base:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`
- **Tool:** Unsloth / PEFT LoRA (r=32, multi-epoch, packing, assistant-only loss) — see `notebooks/train_lora_kaggle.ipynb`
- **Platform:** Kaggle GPU (Colab hit limits)
- **Export:** merge LoRA → GGUF **Q4_K_M**
- **Artifact:** https://huggingface.co/HassanM44/ezlab-1.5b-q4_k_m (`labpulse-1.5b-q4_k_m.gguf`, ~940 MB)

## Run it locally

```bash
# Download
hf download HassanM44/ezlab-1.5b-q4_k_m labpulse-1.5b-q4_k_m.gguf --local-dir ./models

# App (from Labpulse repo)
pip install -r requirements.txt
# place GGUF at models/labpulse-1.5b-q4_k_m.gguf
uvicorn src.api:app --host 127.0.0.1 --port 8080
# UI: cd web && npm run dev → http://localhost:3000
```

- **Runtime:** llama.cpp via `llama-cpp-python` (`n_ctx=4096`, temperature 0.1 for JSON)
- **Hardware tested:** MacBook CPU (~1–2 GB RAM for Q4 1.5B)
- **System behaviour:** task/code/output JSON; curated templates + language gate for presentation-ready OS/ML demos

## Before and after

Same held-out style prompt (factorial lab task → JSON `code`/`output`):

| | Behaviour |
|--|-----------|
| **Base** | Often incomplete JSON, empty `output`, or non-runnable stubs |
| **Fine-tuned (EzLab)** | Schema-shaped JSON with a full runnable Python factorial and `factorial(5) = 120` |

Limitation: tiny 1.5B still drifts on rare tasks; the product path prefers curated templates + syntax/exec gates so demos stay submission-ready.

## What we learned

- Quantized 1.5B + Unsloth on Kaggle is enough for structured lab JSON when the dataset is narrow.
- Export/session wipe on Kaggle is the real pain — FileLink/zip beats UI download.
- For judges, **template-first + real PDF/DOCX** beats raw model prose; PDF iframe previews are unreliable — use a PNG cover preview.

## Team

- Hassan Mahmood — https://github.com/Hassanmahmood4  
- Model: https://huggingface.co/HassanM44/ezlab-1.5b-q4_k_m  
- Credits: Qwen, Unsloth, llama.cpp, Typst, Hugging Face
