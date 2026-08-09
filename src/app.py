import torch
import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

LORA_PATH = "marcobrasiliense/qwen-lora-sec"
BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if torch.cuda.is_available() else torch.float32

print(f"=== Carregando modelo no dispositivo: {device} ===")

tokenizer = AutoTokenizer.from_pretrained(
    BASE_MODEL_ID,
    trust_remote_code=True
)

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    dtype=dtype,
    device_map="auto" if torch.cuda.is_available() else None,
    trust_remote_code=True
)

model = PeftModel.from_pretrained(
    base_model,
    LORA_PATH,
    subfolder="modelo_final"
)
model.eval()


def extract_text(content):
    """Garante que qualquer formato vindo do Gradio seja convertido para string pura."""
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


def respond(message, history):
    messages = []

    # Processa e limpa o histórico
    for item in history:
        if isinstance(item, dict):
            role = item.get("role", "user")
            content = extract_text(item.get("content", ""))
            messages.append({"role": role, "content": content})
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            u, a = item
            if u:
                messages.append({"role": "user", "content": extract_text(u)})
            if a:
                messages.append({"role": "assistant", "content": extract_text(a)})

    # Adiciona a mensagem atual garantindo o tipo 'str'
    user_text = extract_text(message)
    messages.append({"role": "user", "content": user_text})

    # Renderiza o template de chat
    text_input = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    inputs = tokenizer(text_input, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id
        )

    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response


demo = gr.ChatInterface(
    fn=respond,
    title="Cybersecurity AI Assistant (Qwen-1.5B LoRA)",
    description="Interface de testes do modelo finetunado para respostas de cibersegurança e tecnologia.",
    examples=[
        "O que é uma vulnerabilidade de SQL Injection e como prevenir?",
        "Explique como funciona o método LoRA para fine-tuning de LLMs."
    ]
)

if __name__ == "__main__":
    demo.launch()