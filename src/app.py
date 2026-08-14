import sys
import uuid
from pathlib import Path

# Add project root directory to Python path dynamically
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import gradio as gr
from src.model_service import CyberModelService
from src.pdf_generator import PDFReportGenerator

# Initialize the core model service singleton
service = CyberModelService()


def get_new_session_id():
    """Generates a unique session identifier per browser session."""
    return str(uuid.uuid4())


def chat_respond(message, history, session_id):
    """Bridge function yielding streamed tokens for interactive chat formatted as dict messages."""
    if not message or not message.strip():
        yield history or [], ""
        return

    history = history or []

    # Normalize history to a list of dicts with 'role' and 'content' keys
    new_history = []
    for item in history:
        if isinstance(item, dict):
            new_history.append(item)
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            new_history.append({"role": "user", "content": str(item[0])})
            new_history.append({"role": "assistant", "content": str(item[1])})

    # Append current user message and empty placeholder for assistant response
    new_history.append({"role": "user", "content": message})
    new_history.append({"role": "assistant", "content": ""})

    for partial_response in service.generate_response_stream(message, history, session_id=session_id):
        new_history[-1]["content"] = partial_response
        yield new_history, ""


def clear_chat_history(session_id):
    """Clears history from SQLite for the active session and resets chat UI."""
    service.db.clear_session(session_id)
    return [], ""


def file_audit_respond(file_obj, session_id):
    """Bridge function handling file upload and streaming code audit results."""
    if file_obj is None:
        yield "❌ Please upload a valid source code file (.py, .c, .js, .php, etc.) before running the audit."
        return

    for partial_response in service.audit_code_file(file_obj.name, session_id=session_id):
        yield partial_response


def export_pdf_report(file_obj, audit_text):
    """Generates a PDF audit report file for user download."""
    if not file_obj or not audit_text or "Please upload a file" in audit_text:
        return None

    file_name = Path(file_obj.name).name
    pdf_path = PDFReportGenerator.build_sast_pdf(
        file_name=file_name,
        report_content=audit_text,
        output_path="sast_audit_report.pdf"
    )
    return pdf_path


# Build Tabbed User Interface
with gr.Blocks(title="🛡️ CyberAssistant LLM") as demo:
    session_id = gr.State(get_new_session_id)

    gr.Markdown(
        """
        # 🛡️ CyberAssistant LLM
        *Specialized AI Assistant for Cybersecurity, Vulnerability Analysis, and Secure Code Auditing.*
        """
    )

    with gr.Tabs():
        # Tab 1: Interactive Chat
        with gr.TabItem("💬 Interactive Security Chat"):
            chatbot = gr.Chatbot(height=500)
            msg = gr.Textbox(placeholder="Ask a cybersecurity question...", show_label=False)

            with gr.Row():
                submit_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("🗑️ Clear History")

            # Chat event handlers
            submit_btn.click(chat_respond, [msg, chatbot, session_id], [chatbot, msg])
            msg.submit(chat_respond, [msg, chatbot, session_id], [chatbot, msg])
            clear_btn.click(clear_chat_history, [session_id], [chatbot, msg])

        # Tab 2: SAST Code Auditor
        with gr.TabItem("🔍 SAST Code Auditor"):
            gr.Markdown(
                """
                ### Upload Source Code File for Automated Security Audit
                Upload any code file (`.py`, `.c`, `.cpp`, `.js`, `.php`, `.sql`, etc.) to run a Static Application Security Testing (SAST) scan and download an official PDF report.
                """
            )
            with gr.Row():
                with gr.Column(scale=1):
                    file_input = gr.File(
                        label="Upload Source Code File",
                        file_types=[".py", ".c", ".cpp", ".js", ".ts", ".php", ".java", ".go", ".sql", ".sh"]
                    )
                    audit_button = gr.Button("🔍 Run Security Audit", variant="primary")

                    gr.Markdown("---")
                    export_pdf_btn = gr.Button("📥 Export Audit Report (PDF)", variant="secondary", interactive=False)
                    pdf_download_output = gr.File(label="Download Generated PDF", interactive=False)

                with gr.Column(scale=2):
                    audit_output = gr.Markdown(label="Audit Report",
                                               value="*Upload a file and click 'Run Security Audit' to view results...*")

            # Disable PDF button during streaming, re-enable once finished
            audit_button.click(
                fn=lambda: gr.Button(interactive=False),
                outputs=[export_pdf_btn]
            ).then(
                fn=file_audit_respond,
                inputs=[file_input, session_id],
                outputs=[audit_output]
            ).then(
                fn=lambda: gr.Button(interactive=True),
                outputs=[export_pdf_btn]
            )

            # Export PDF button event
            export_pdf_btn.click(
                fn=export_pdf_report,
                inputs=[file_input, audit_output],
                outputs=[pdf_download_output]
            )

if __name__ == "__main__":
    demo.launch()