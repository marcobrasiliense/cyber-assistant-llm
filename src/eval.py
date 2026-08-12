import sys
import json
from pathlib import Path

# Add project root directory to Python path dynamically
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.model_service import CyberModelService

# Test dataset containing technical cybersecurity scenarios
EVAL_BENCHMARK = [
    {
        "category": "Web & API Security",
        "prompt": "How do I prevent Broken Object Level Authorization (BOLA / IDOR) in a Python FastAPI backend?",
        "expected_topics": ["ownership verification", "middleware/dependencies", "UUIDs over sequential IDs"]
    },
    {
        "category": "Secure Coding",
        "prompt": "Analyze this C code for vulnerabilities and rewrite it securely:\n\n```c\n#include <stdio.h>\n#include <string.h>\n\nvoid login() {\n    char password[16];\n    printf(\"Enter password: \");\n    gets(password);\n}\n```",
        "expected_topics": ["gets() buffer overflow", "fgets() substitution", "stack protection"]
    },
    {
        "category": "Reverse Engineering & Malware Analysis",
        "prompt": "What are the core differences between static analysis and dynamic analysis when examining a suspicious Linux binary?",
        "expected_topics": ["disassembly vs sandboxing", "strace/gdb", "strings/readelf", "safety precautions"]
    },
    {
        "category": "Cryptography & Authentication",
        "prompt": "Why is Argon2id preferred over standard MD5 or SHA256 for password storage, and how does salt fit in?",
        "expected_topics": ["memory-hard algorithm", "GPU/ASIC resistance", "unique salt", "CPU time cost"]
    }
]


def save_results(results_list: list, file_path: Path):
    """Utility function to persist results immediately to disk."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(results_list, f, indent=4, ensure_ascii=False)


def run_evaluation():
    """Runs automated benchmark evaluation on predefined cybersecurity queries."""
    print("=== Starting CyberAssistant Benchmark Evaluation ===\n")
    report_path = ROOT_DIR / "eval_results.json"

    try:
        service = CyberModelService()
    except Exception as e:
        print(f"❌ Error initializing CyberModelService: {e}")
        return

    results = []

    for idx, test_case in enumerate(EVAL_BENCHMARK, 1):
        print(f"[{idx}/{len(EVAL_BENCHMARK)}] Evaluating Category: {test_case['category']}...")
        print(f"Prompt: {test_case['prompt']}")

        try:
            response = service.generate_response(
                message=test_case["prompt"],
                history=[]
            )

            print("\n--- Model Response ---")
            print(response)
            print("-" * 40 + "\n")

            results.append({
                "category": test_case["category"],
                "prompt": test_case["prompt"],
                "expected_topics": test_case["expected_topics"],
                "generated_response": response
            })

            # Save incrementally after each successful response
            save_results(results, report_path)
            print(f"✔️ Progress saved to {report_path.name}")

        except Exception as e:
            print(f"❌ Error during evaluation of prompt {idx}: {e}")
            break

    print(f"\n=== Evaluation Finished! Full report available at: {report_path} ===")


if __name__ == "__main__":
    run_evaluation()