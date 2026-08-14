import torch
from pathlib import Path
from threading import Thread
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from peft import PeftModel
from src.config import Config
from src.database import DatabaseManager


class CyberModelService:
    """Service class responsible for loading LLM pipeline, database persistence, and streaming."""

    def __init__(self):
        self.config = Config
        self.device = self.config.DEVICE
        self.db = DatabaseManager(self.config.DB_PATH)
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Loads base model and LoRA adapter into memory."""
        print(f"=== [ModelService] Initializing execution on device: {self.device} ===")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.BASE_MODEL_ID,
            trust_remote_code=True
        )

        base_model = AutoModelForCausalLM.from_pretrained(
            self.config.BASE_MODEL_ID,
            torch_dtype=self.config.DTYPE,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )

        self.model = PeftModel.from_pretrained(
            base_model,
            self.config.LORA_PATH,
            subfolder=self.config.LORA_SUBFOLDER
        )
        self.model.eval()
        print("=== [ModelService] Model successfully loaded and set to evaluation mode ===")

    @staticmethod
    def _extract_clean_text(content) -> str:
        """Sanitizes incoming Gradio history payloads into plain strings."""
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            return content.get("text", str(content))
        elif isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                else:
                    parts.append(str(part))
            return "".join(parts)
        return str(content)

    def _prepare_messages(self, session_id: str, current_message: str) -> list:
        """Loads last N messages from SQLite database to restrict token context length."""
        recent_history = self.db.get_recent_history(
            session_id=session_id,
            limit=self.config.MAX_HISTORY_LIMIT
        )

        messages = [{"role": "system", "content": self.config.SYSTEM_PROMPT}]
        messages.extend(recent_history)
        messages.append({"role": "user", "content": current_message})

        return messages

    def generate_response(self, message: str, session_id: str = "default_session") -> str:
        """Synchronous generation with SQLite persistence (used for benchmarks/eval.py)."""
        clean_user_message = self._extract_clean_text(message)
        messages = self._prepare_messages(session_id, clean_user_message)

        text_input = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = self.tokenizer(text_input, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config.MAX_NEW_TOKENS,
                temperature=self.config.TEMPERATURE,
                top_p=self.config.TOP_P,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id
            )

        response = self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:],
            skip_special_tokens=True
        )

        self.db.add_message(session_id, "user", clean_user_message)
        self.db.add_message(session_id, "assistant", response)

        return response

    def generate_response_stream(self, message: str, history: list, session_id: str = "default_session"):
        """Real-time streaming generation with automatic SQLite persistence."""
        clean_user_message = self._extract_clean_text(message)
        messages = self._prepare_messages(session_id, clean_user_message)

        text_input = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = self.tokenizer(text_input, return_tensors="pt").to(self.model.device)

        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        generation_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=self.config.MAX_NEW_TOKENS,
            temperature=self.config.TEMPERATURE,
            top_p=self.config.TOP_P,
            do_sample=True,
            pad_token_id=self.tokenizer.pad_token_id
        )

        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        full_response = ""
        for new_text in streamer:
            full_response += new_text
            yield full_response

        self.db.add_message(session_id, "user", clean_user_message)
        self.db.add_message(session_id, "assistant", full_response)

    def audit_code_file(self, file_path: str, session_id: str = "default_session"):
        """Reads a source code file, formats a security audit prompt, and streams analysis."""
        if not file_path:
            yield "❌ Error: No file uploaded. Please select a source code file."
            return

        path = Path(file_path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                code_content = f.read()
        except UnicodeDecodeError:
            yield f"❌ Error: Unable to read `{path.name}`. The file appears to be a binary or non-text file. Please upload plain text source code files (.py, .c, .js, .sql, etc.)."
            return
        except Exception as e:
            yield f"❌ Error reading file `{path.name}`: {str(e)}"
            return

        # Truncate source code if excessively long to prevent token explosion
        max_chars = 4000
        if len(code_content) > max_chars:
            code_content = code_content[:max_chars] + "\n... [TRUNCATED DUE TO LENGTH LIMIT]"

        audit_prompt = (
            f"Perform a comprehensive Static Application Security Testing (SAST) audit on the following file ({path.name}):\n\n"
            f"```\n{code_content}\n```\n\n"
            "Please structure your response into the following clear sections:\n"
            "1. **Identified Security Vulnerabilities** (Name, Severity, OWASP/CWE alignment).\n"
            "2. **Detailed Flaw Explanation** (Why the flaw is dangerous).\n"
            "3. **Refactored & Secure Code** (Provide concise, focused code snippets fixing ONLY the identified vulnerabilities. Do NOT rewrite unchanged full classes or add repetitive assertions)."
        )

        for partial_response in self.generate_response_stream(audit_prompt, history=[], session_id=session_id):
            yield partial_response