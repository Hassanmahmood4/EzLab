# LabPulse Colab training

## `train_lora_colab.ipynb`

Runs on **Google Colab (T4 GPU)**:

1. Install Unsloth / PEFT  
2. Load `data/train.jsonl` + `valid.jsonl`  
3. LoRA fine-tune `Qwen/Qwen2.5-1.5B-Instruct`  
4. Merge adapters → HF weights  
5. Convert → **`labpulse-1.5b-q4_k_m.gguf`** (Q4_K_M)  
6. Download the GGUF to your laptop  

### Local placement after download

```text
Labpulse/models/labpulse-1.5b-q4_k_m.gguf
```

That single file is what the app loads (no Lab OFF/ON toggle).

### How to open

1. Go to [colab.research.google.com](https://colab.research.google.com)  
2. File → Upload notebook → select `notebooks/train_lora_colab.ipynb`  
3. Runtime → Change runtime type → **T4 GPU**  
4. Upload `train.jsonl` / `valid.jsonl` (Option A) or clone/Drive (B/C)  
5. Run all cells  

Training usually takes on the order of **30–90 minutes** on a free T4 for ~850 examples × 2 epochs.
