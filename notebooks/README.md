# EzLab training notebooks

Train a **new** LoRA so the model emits per-task solutions:

```json
{"code": "...", "output": "..."}
```

(not the old full-report / tables schema).

---

## Kaggle (recommended if Colab quota is empty)

### Files on your Mac
| File | Purpose |
|------|---------|
| `notebooks/train_lora_kaggle.ipynb` | Unsloth-only train → merge → GGUF (no HF login / llama.cpp) |
| `data/kaggle_dataset.zip` | Fresh high-diversity set (~3200 train): Task/Exercise labels, C OS, ML+savefig |

**Always regenerate before a final run:**

```bash
cd Labpulse
.venv/bin/python data/generate_dataset.py
```

### Steps (final run)
1. Open [Kaggle](https://www.kaggle.com) → **New Notebook**
2. **GPU** + **Internet On**
3. Import **updated** `train_lora_kaggle.ipynb`
4. **Add Data** → upload the **new** `data/kaggle_dataset.zip` (remove any old dataset first)
5. **Run All** — leave session on (~45–90 min)
6. Download `labpulse-1.5b-q4_k_m.gguf` **immediately**, then **Save Version**
7. On Mac:
   ```bash
   mv ~/Downloads/labpulse-1.5b-q4_k_m.gguf Labpulse/models/labpulse-1.5b-q4_k_m.gguf
   ```
8. Restart API **without** `LABPULSE_STUB=1`

### Quality knobs (in notebook config cell)
- Default **Qwen2.5-Coder-1.5B**, LoRA `r=32`, **3 epochs**
- Packing + NEFTune + **train on assistant replies only**
- Set `USE_3B = True` for Coder-3B only if VRAM allows (may OOM on small T4)

---

## Colab (when quota returns)

1. Upload `notebooks/train_lora_colab.ipynb`
2. Runtime → GPU → T4
3. Upload `data/colab_dataset.zip` when prompted  
   *(same new schema as the Kaggle zip)*
4. Download GGUF → `Labpulse/models/`

> If the Colab notebook still mentions the old report schema in a validation cell, prefer the **Kaggle** notebook — it validates `code` / `output` keys only.

---

## After install

```bash
cd Labpulse
GGML_METAL=0 LABPULSE_N_GPU_LAYERS=0 .venv/bin/uvicorn src.api:app --host 127.0.0.1 --port 8080
```

Then generate ML Lab 06 / OS process lab again and check for real code + graphs, not placeholders.
