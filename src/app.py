import sys
from pathlib import Path

#Add project root directory to Python path dinamically
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import gradio as gr
from src.model_service import CyberModelService

#Initialize the core model service singleton
service = CyberModelService()

def respond(message, history):
    """Bride function between Gradio UI and CyberModelService"""
    return service.generate_response(message, history)

#Configure User Interface
demo = gr.ChatInterface(
    fn=respond,
    title="CyberAssistant LLM (Qwen-1.5B LoRA)",
    description="Specialized AI Assistant for Cybersecurity, Vulnerability Analysis, and Secure Coding.",
    examples=[
        "How do I prevent SQL Injection vulnerabilities in Python applications?",
        "Explain Broken Access Control (OWASP A01:2021) and how to mitigate it.",
        "What is the difference between symmetric and asymmetric encryption?",
        "How does a Reflected Cross-Site Scripting (XSS) attack work?"
    ]
)

if __name__ == "__main__":
    demo.launch()