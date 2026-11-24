## lean-proof-agent

An LLM agent proving mathematical theorems in **Lean 4**. 
Using Claude (Anthropic API), proposes proofs, Lean compiler checks them. A theorem only counts as proved once Lean has accepted the proof without `sorry` and using only
Lean's standard axioms.

## Setup

Requirements: Python ≥ 3.13, [Poetry](https://python-poetry.org/),
Lean 4 via [elan](https://github.com/leanprover/elan), an Anthropic API key.


## Usage

1. Write a theorem in a Lean file (`lean_workspace/Problems/`), with `sorry` as     proof.
2. Claude proposes a proof and checks it with the tool `check_proof`.
3. The verifier runs Lean on it. If the proof is rejected, Claude gets
   Lean's error messages and tries again.
4. This repeats until the proof is verified or the attempts are used up.

# Example
    ```lean
    import Mathlib

    theorem gauss_sum (n : ℕ) : 2 * (∑ i ∈ Finset.range (n + 1), i) = n * (n + 1) := by
    sorry
    ```
Run the agent from the project root (inside the Poetry environment,
or prefix the command with `poetry run`):
```bash
python -m lean_proof_agent lean_workspace/Problems/Example.lean
python -m lean_proof_agent lean_workspace/Problems/Example.lean --attempts 10 --model claude-opus-5-5
```
If a proof is found, it is saved as `Example_proved.lean` next to the input file.

## Tests

```bash
pytest -m "not lean"   # fast tests, Lean and Claude are faked
pytest                 # also runs 2 tests with the real Lean compiler (~40 s)
```