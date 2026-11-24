# LabPulse

Offline lab-to-report & anomaly copilot for Pakistani university STEM/CS labs.

**Windows + macOS**, lowest local footprint: **llama.cpp** + fine-tuned **`labpulse-1.5b-q4_k_m.gguf`** (~1–2 GB RAM). Train LoRA on **Google Colab**, run one GGUF locally — no Ollama, no MLX, **no Base/Lab toggle**.

Audits raw CSV/logs for unit errors, then exports **Word (`.docx`)** and **PDF (`.pdf`)** with campus cover pages — 100% offline. Training data is **CS-focused** (PF, OOP, DSA, OS, DB, Networks, SE, etc.) — not EE/mechanical labs.

## Why this stack

| Option | Local cost | Notes |
|--------|------------|--------|
| **llama.cpp** (chosen) | Lowest | Direct GGUF, CPU/Metal/CUDA, no extra server |
| Ollama | Higher | Convenient wrapper around llama.cpp + daemon |
| MLX | Mac-only | Not for Windows |

**App model:** fine-tuned `Qwen2.5-1.5B` only. Base-vs-lab numbers live in the benchmark table (from Colab / `eval.py`), not in the UI.

## Quick start

```bash
make setup
# Place Colab-exported GGUF at models/labpulse-1.5b-q4_k_m.gguf
make models-check
make data
make eval                 # optional write-up metrics
make demo                 # FastAPI :8080 + Next.js :3000
```

Training (heavy): `notebooks/train_lora_colab.ipynb` on Colab GPU.

## Requirements

- Windows 10/11 or macOS
- Python 3.11+
- ~2 GB free RAM for the 1.5B Q4 model (8 GB machine is fine)
- Typst CLI for PDF export ([releases](https://github.com/typst/typst/releases))

## Benchmark

| Model | JSON Validity % | Grounding Acc % | Anomaly Recall % | Alias F1 | Dual Export % | Peak RAM (GB) | tok/s |
|-------|-----------------|-----------------|------------------|----------|---------------|---------------|-------|
| Base 1.5B Q4 (eval only) | — | — | — | — | — | — | — |
| labpulse 1.5B Q4 (**app**) | — | — | — | — | — | — | — |

*Filled after `make eval` / Colab.*

## License

Hackathon / research prototype. University crest PNGs in `assets/logos/` are placeholders — replace with official artwork before public demos where required.
