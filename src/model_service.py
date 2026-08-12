import torch
from threading import Thread
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from peft import PeftModel
from src.config import Config


class CyberModelService:
    """Service class responsible for loading the LLM pipeline and handling inferences."""

    def __init__(self):
        self.config = Config
        self.device = self.config.DEVICE
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

    def _prepare_messages(self, message, history):
        """Internal helper function to format chat history into Qwen chat template structure."""
        messages = [{"role": "system", "content": self.config.SYSTEM_PROMPT}]

        for item in history:
            if isinstance(item, dict):
                role = item.get("role", "user")
                content = self._extract_clean_text(item.get("content", ""))
                messages.append({"role": role, "content": content})
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                u, a = item
                if u:
                    messages.append({"role": "user", "content": self._extract_clean_text(u)})
                if a:
                    messages.append({"role": "assistant", "content": self._extract_clean_text(a)})

        user_text = self._extract_clean_text(message)
        messages.append({"role": "user", "content": user_text})
        return messages

    def generate_response(self, message, history) -> str:
        """Synchronous generation (used for automated benchmarks like eval.py)."""
        messages = self._prepare_messages(message, history)
        text_input = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = self.tokenizer(text_input, return_tensors="pt").to(self.device)

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
        return response

    def generate_response_stream(self, message, history):
        """Real-time streaming generation (used for web UI in app.py)."""
        messages = self._prepare_messages(message, history)
        text_input = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = self.tokenizer(text_input, return_tensors="pt").to(self.device)

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

        partial_response = ""
        for new_text in streamer:
            partial_response += new_text
            yield partial_response