# EzLab

Offline CS lab-report copilot for Pakistani universities.

Fine-tuned **Qwen2.5-Coder-1.5B** → GGUF **Q4_K_M**, served with **llama.cpp** on Windows + macOS (~1–2 GB RAM). Parses a lab manual into tasks, writes code + output, exports **Word** and **PDF** with campus cover pages — **100% offline**.

**Model (public):** [HassanM44/ezlab-1.5b-q4_k_m](https://huggingface.co/HassanM44/ezlab-1.5b-q4_k_m)  
**Demo video:** [docs/demo/ezlab_demo.mp4](docs/demo/ezlab_demo.mp4)

## Quick start

```bash
# Python deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Download GGUF
hf download HassanM44/ezlab-1.5b-q4_k_m labpulse-1.5b-q4_k_m.gguf --local-dir ./models

# Typst (PDF)
# macOS: brew install typst   OR place binary at bin/typst

# API + UI
make demo
# → FastAPI http://127.0.0.1:8080
# → Next.js  http://localhost:3000
```

```bash
make prod-suite   # multi-subject smoke test (docx/pdf/templates)
```

## Training

| Notebook | Where |
|----------|--------|
| `notebooks/train_lora_kaggle.ipynb` | **Preferred** — Unsloth LoRA → GGUF on Kaggle |
| `notebooks/train_lora_colab.ipynb` | Colab (GPU limits) |

Dataset: `data/train.jsonl` (~3200), `valid.jsonl` / `test.jsonl` (~250 each). Regenerate with `python data/generate_dataset.py`.

## Stack

- **Inference:** `llama-cpp-python` loads `models/labpulse-1.5b-q4_k_m.gguf`
- **Backend:** FastAPI (`src/api.py`) — task pipeline, curated templates, Python exec polish
- **Frontend:** Next.js (`web/`)
- **Export:** `docxtpl` → `.docx`, Typst → `.pdf` + cover `preview.png`

## Hackathon showcase draft

Filled submission forms (copy into a fork of `junaiddshaukat/finetune-anywhere`):

- `hackathon/showcase-ezlab/model.yaml`
- `hackathon/showcase-ezlab/README.md`

## License

Apache-2.0 model weights (Qwen lineage). University crest PNGs in `assets/logos/` — replace with official artwork for public production if required.
