import os
import torch

class Config:
    """Central configuration management for the CyberAssistant LLM project"""

    #Model Identifiers
    BASE_MODEL_ID: str = os.getenv("BASE_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct")
    LORA_PATH: str = os.getenv("LORA_PATH", "marcobrasiliense/qwen-lora-sec")
    LORA_SUBFOLDER: str = os.getenv("LORA_SUBFOLDER", "modelo_final")

    #System Persona
    SYSTEM_PROMPT: str = (
        "You are CyberAssistant, an expert AI assistant specializing in cybersecurity, "
        "defensive security, and secure software development. Your mission is to help "
        "cybersecurity professionals, developers, and researchers analyze vulnerabilities, "
        "mitigate threats (OWASP Top 10, MITRE ATT&CK), review code for security flaws, "
        "and apply security best practices. Provide technically accurate, clear, concise, "
        "and well-structured responses."
    )

    #Generation Hyperparameters
    MAX_NEW_TOKENS: int = int(os.getenv("MAX_NEW_TOKENS", "1024"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))
    TOP_P: float = float(os.getenv("TOP_P", "0.9"))

    #Hardware Optimization
    DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"
    DTYPE: torch.dtype = torch.float16 if torch.cuda.is_available() else torch.float32

