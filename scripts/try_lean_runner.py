"""Try the LeanRunner on three small examples."""

from lean_proof_agent.lean_runner import LeanRunner

EXAMPLES = {
    "correct": "example : (2 : ℕ) + 2 = 4 := by norm_num",
    "incomplete": "theorem t (a b : ℕ) : a + b = b + a := by\n  sorry",
    "wrong": "example : (2 : ℕ) + 2 = 5 := by norm_num",
}

runner = LeanRunner()
for name, code in EXAMPLES.items():
    result = runner.check(code)
    print(f"=== {name}: success={result.is_success} ({result.duration_s:.1f} s) ===")
    for message in result.messages:
        print(message.format())