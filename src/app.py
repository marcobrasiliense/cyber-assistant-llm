import sys
from pathlib import Path

# Add project root directory to Python path dynamically
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import gradio as gr
from src.model_service import CyberModelService

# Initialize the core model service singleton
service = CyberModelService()


def chat_respond(message, history):
    """Bridge function yielding streamed tokens for interactive chat."""
    for partial_response in service.generate_response_stream(message, history):
        yield partial_response


def file_audit_respond(file_obj):
    """Bridge function handling file upload and streaming code audit results."""
    if file_obj is None:
        yield "❌ Please upload a valid source code file (.py, .c, .js, .php, etc.) before running the audit."
        return

    for partial_response in service.audit_code_file(file_obj.name):
        yield partial_response


# Build Tabbed User Interface
with gr.Blocks(title="🛡️ CyberAssistant LLM") as demo:
    gr.Markdown(
        """
        # 🛡️ CyberAssistant LLM
        *Specialized AI Assistant for Cybersecurity, Vulnerability Analysis, and Secure Code Auditing.*
        """
    )

    with gr.Tabs():
        # Tab 1: Interactive Chat
        with gr.TabItem("💬 Interactive Security Chat"):
            gr.ChatInterface(
                fn=chat_respond,
                examples=[
                    "How do I prevent SQL Injection vulnerabilities in Python applications?",
                    "Explain Broken Object Level Authorization (BOLA / IDOR) and how to mitigate it in FastAPI.",
                    "What is the difference between static analysis and dynamic analysis when examining Linux binaries?",
                    "Why is Argon2id preferred over standard MD5 or SHA256 for password hashing?"
                ]
            )

        # Tab 2: SAST Code Auditor
        with gr.TabItem("🔍 SAST Code Auditor"):
            gr.Markdown(
                """
                ### Upload Source Code File for Automated Security Audit
                Upload any code file (`.py`, `.c`, `.cpp`, `.js`, `.php`, `.sql`, etc.) to run a Static Application Security Testing (SAST) scan.
                """
            )
            with gr.Row():
                with gr.Column(scale=1):
                    file_input = gr.File(
                        label="Upload Source Code File",
                        file_types=[".py", ".c", ".cpp", ".js", ".ts", ".php", ".java", ".go", ".sql", ".sh"]
                    )
                    audit_button = gr.Button("🔍 Run Security Audit", variant="primary")

                with gr.Column(scale=2):
                    audit_output = gr.Markdown(label="Audit Report",
                                               value="*Upload a file and click 'Run Security Audit' to view results...*")

            audit_button.click(
                fn=file_audit_respond,
                inputs=[file_input],
                outputs=[audit_output]
            )

if __name__ == "__main__":
    demo.launch()