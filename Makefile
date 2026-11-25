.PHONY: setup logos data eval demo clean models-check render-test prod-suite

PYTHON ?= python3
PIP ?= pip3
# Prefer project venv when present
ifneq (,$(wildcard .venv/bin/python))
  PYTHON := .venv/bin/python
  PIP := .venv/bin/pip
endif

setup:
	$(PIP) install -r requirements.txt
	@command -v typst >/dev/null 2>&1 || test -x bin/typst || echo "Install Typst: https://github.com/typst/typst/releases (or place binary at bin/typst)"
	$(MAKE) logos

logos:
	$(PYTHON) assets/generate_placeholder_logos.py

data:
	$(PYTHON) data/generate_dataset.py

# Training is Colab-only — open notebooks/train_lora_colab.ipynb in Google Colab (T4 GPU)
models-check:
	@test -f models/labpulse-1.5b-q4_k_m.gguf || echo "Missing fine-tuned GGUF: models/labpulse-1.5b-q4_k_m.gguf (export from Colab)"

eval:
	$(MAKE) models-check
	$(PYTHON) eval.py

render-test:
	$(PYTHON) scripts/e2e_render.py

prod-suite:
	GGML_METAL=0 LABPULSE_N_GPU_LAYERS=0 $(PYTHON) scripts/prod_ready_suite.py

demo:
	@echo "Start UI:   cd web && npm run dev   # http://127.0.0.1:3000"
	uvicorn src.api:app --host 127.0.0.1 --port 8080

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf outputs/ .cache/ 2>/dev/null || true
