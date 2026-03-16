# Local Models

This folder is for repo-local model assets used by StrattonAI.

- `models/ollama/`
  Ollama-managed local chat models. The current user `OLLAMA_MODELS` setting points here.
- `models/huggingface/`
  Hugging Face model snapshots such as embedding and reranker models.

Current local models:

- `models/ollama/llama3.1:latest`
- `models/ollama/qwen2.5:14b-instruct`
- `models/huggingface/bge-m3`
- `models/huggingface/bge-reranker-v2-m3`

Large model files in this directory are intentionally ignored by Git.
