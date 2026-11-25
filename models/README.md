---
license: apache-2.0
base_model: Qwen/Qwen2.5-Coder-1.5B-Instruct
tags:
  - gguf
  - qwen2.5
  - lora
  - llama.cpp
  - offline
  - education
pipeline_tag: text-generation
---

# EzLab 1.5B (GGUF Q4_K_M)

Fine-tuned **Qwen2.5-Coder-1.5B-Instruct** LoRA for **EzLab** — an offline CS lab-report copilot for Pakistani university students.

## What’s in this repo

| File | Description |
|------|-------------|
| `labpulse-1.5b-q4_k_m.gguf` | Merged LoRA → GGUF **Q4_K_M** (~940 MB) |

## Intended use

- Local inference with **llama.cpp** / `llama-cpp-python`
- Lab-manual task → student code + terminal output JSON
- Runs on laptop CPU/Metal with ~1–2 GB RAM; works with Wi‑Fi off

## Quick start (llama.cpp)

```bash
huggingface-cli download HassanM44/ezlab-1.5b-q4_k_m labpulse-1.5b-q4_k_m.gguf --local-dir ./models
```

```python
from llama_cpp import Llama
llm = Llama(model_path="models/labpulse-1.5b-q4_k_m.gguf", n_ctx=4096, n_gpu_layers=-1)
```

## Training

- Base: `Qwen/Qwen2.5-Coder-1.5B-Instruct`
- LoRA (Unsloth / PEFT) on synthetic Pakistani CS lab chat data
- Trained on Kaggle GPU; quantized to GGUF Q4_K_M

## License

Apache 2.0 (inherits from Qwen2.5). Not for fabricating lab work without student artifacts.
