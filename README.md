# 🛡️ CyberAssistant LLM

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/)
[![Gradio](https://img.shields.io/badge/Gradio-FF7C00?style=for-the-badge&logo=gradio&logoColor=white)](https://gradio.app/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

**CyberAssistant LLM** is a domain-specialized AI assistant designed for cybersecurity analysis, secure code review, and vulnerability mitigation. Powered by a fine-tuned **Qwen2.5-1.5B-Instruct** base model via Parameter-Efficient Fine-Tuning (**PEFT / LoRA**), the application delivers high-precision technical answers without commercial "over-refusal" bottlenecks.

---

## ✨ Key Features

* **Domain-Adapted Intelligence**: Fine-tuned on cybersecurity datasets (`marcobrasiliense/qwen-lora-sec`) for specialized guidance in OWASP Top 10, MITRE ATT&CK, secure C/Python coding, and reverse engineering.
* **Modular Enterprise Architecture**: Built using decoupled layers (`Config`, `DatabaseManager`, `ModelService`, and `UI`) following 12-Factor App and SOLID software principles.
* **Token-Efficient Context Management**: Integrates an embedded SQLite database (`cyber_assistant.db`) featuring a **Sliding Window** mechanism to restrict context history length, drastically lowering VRAM usage and preventing Out-Of-Memory (OOM) errors.
* **Real-Time Token Streaming**: Implements non-blocking multi-threaded inference with `TextIteratorStreamer` for near-instantaneous Time-To-First-Token (TTFT).
* **Automated Benchmarking & DB Inspection**: Includes `src/eval.py` for automated quality evaluation and `src/inspect_db.py` to audit persisted chat records.

---

## 🏗️ Project Architecture

```text
cyber-assistant-llm/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Centralized hyperparameter, DB, and system configuration
│   ├── database.py          # SQLite persistence manager & sliding window logic
│   ├── model_service.py     # Core LLM pipeline management, DB integration, and streaming
│   ├── inspect_db.py        # Terminal utility script to inspect stored chat logs
│   └── app.py               # Gradio web user interface
├── src/eval.py              # Automated benchmark evaluation script
├── eval_results.json        # Persisted benchmark output reports
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

* Linux / WSL2
* Python 3.11+
* Conda / Miniconda
* NVIDIA GPU with CUDA support (Recommended for optimal performance)

### 1. Environment Setup

Clone the repository and set up the Conda environment:

```bash
git clone [https://github.com/marcobrasiliense/cyber-assistant-llm.git](https://github.com/marcobrasiliense/cyber-assistant-llm.git)
cd cyber-assistant-llm

# Create and activate Conda environment
conda create -n cyber-assistant python=3.11 -y
conda activate cyber-assistant

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 Running the Application

### 1. Interactive Web Interface (Gradio)

Launch the user interface with real-time streaming and SQLite persistence:

```bash
python -m src.app
```

Once initialized, open your browser and navigate to:
```text
[http://127.0.0.1:7860](http://127.0.0.1:7860)
```

### 2. Inspecting Persisted Database Messages

Audit the conversation history stored in `cyber_assistant.db` directly from your terminal:

```bash
python src/inspect_db.py
```

### 3. Automated Evaluation Benchmark

Run the benchmark test suite to evaluate model accuracy and generate an updated `eval_results.json` report:

```bash
python src/eval.py
```

---

## ⚙️ Configuration & Customization

All application settings are managed centrally in `src/config.py` and can be overridden via environment variables:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `BASE_MODEL_ID` | `Qwen/Qwen2.5-1.5B-Instruct` | Base LLM identifier from Hugging Face |
| `LORA_PATH` | `marcobrasiliense/qwen-lora-sec` | Fine-tuned LoRA adapter repository |
| `DB_PATH` | `cyber_assistant.db` | Local SQLite database file location |
| `MAX_NEW_TOKENS` | `1024` | Maximum tokens per generated response |
| `MAX_HISTORY_LIMIT`| `8` | Maximum recent message turns sent to LLM (Sliding Window) |
| `TEMPERATURE` | `0.3` | Controls randomness (lower = more deterministic) |
| `TOP_P` | `0.9` | Nucleus sampling probability threshold |

---

## 📊 Evaluation & Benchmarking

The project incorporates regression testing to monitor model fidelity across key cybersecurity domains:

1. **Web & API Security**: BOLA/IDOR prevention and SQL Injection mitigation.
2. **Secure Software Development**: Buffer overflow detection and secure refactoring (e.g., C `gets()` replacement with `fgets()`).
3. **Reverse Engineering**: Static vs. dynamic analysis workflows for ELF binaries.
4. **Cryptography**: Password hashing mechanisms (Argon2id, bcrypt) and salting strategies.

Check `eval_results.json` for full historical evaluation outputs.

---

## 👤 Author

**Marco Antônio Brasiliense**  
* Computer Science Student & AI Developer  
* GitHub: [@marcobrasiliense](https://github.com/marcobrasiliense)