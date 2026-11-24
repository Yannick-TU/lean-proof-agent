# check three small Lean snippets.

import subprocess
import tempfile
import time
from pathlib import Path

# scripts/lean_interact.py -> project root -> lean_workspace
LEAN_PROJECT_DIR = Path(__file__).resolve().parents[1] / "lean_workspace"

EXAMPLES = {
    "correct": "example : (2 : ℕ) + 2 = 4 := by norm_num",
    "incomplete": "theorem t (a b : ℕ) : a + b = b + a := by\n  sorry",
    "wrong": "example : (2 : ℕ) + 2 = 5 := by norm_num",
}


def check_lean(code: str) -> subprocess.CompletedProcess[str]:
    """Write `code` to a temporary .lean file and let Lean check it."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        lean_file = Path(tmp_dir) / "Check.lean"
        lean_file.write_text("import Mathlib\n\n" + code + "\n", encoding="utf-8")
        return subprocess.run(
            ["lake", "env", "lean", str(lean_file)],
            cwd=LEAN_PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )


def main() -> None:
    for name, code in EXAMPLES.items():
        start = time.perf_counter()
        result = check_lean(code)
        elapsed = time.perf_counter() - start

        print(f"=== {name} ({elapsed:.1f} s) ===")
        print(f"Exit code: {result.returncode}")
        print(result.stdout.strip() or "(no messages)")
        if result.stderr.strip():
            print("stderr:", result.stderr.strip())
        print()


if __name__ == "__main__":
    main()
