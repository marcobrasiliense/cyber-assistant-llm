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
        "category": "Web Security",
        "prompt": "How do I secure a Python Flask application against SQL Injection?",
        "expected_topics": ["parameterized queries", "ORMs", "input sanitization"]
    },
    {
        "category": "Reverse Engineering",
        "prompt": "What are the key steps when performing static analysis on an unknown ELF binary in Linux?",
        "expected_topics": ["strings", "objdump/GDB/Ghidra", "header inspection", "permissions"]
    },
    {
        "category": "Cryptography",
        "prompt": "Why should password hashes use salt, and what hashing algorithm is recommended today?",
        "expected_topics": ["argon2", "bcrypt", "rainbow tables", "unique salt per user"]
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