# lean-proof-agent

An LLM agent proving mathematical theorems in **Lean 4**. 
Using Claude, with Anthropic API, it proposes proofs, the Lean compiler checks them. A proof is only accepted if Lean verifies it without errors, without sorry, and without relying on non-standard axioms.

## Requirements

- Python ≥ 3.13, [Poetry](https://python-poetry.org/)
- Anthropic API key
- Lean 4 via [elan](https://github.com/leanprover/elan)

The Lean workspace specifies Lean 4.36.0 and uses Mathlib as its mathematical library.

## Installation

```bash
poetry install --with dev
cd lean_workspace && lake exe cache get && lake build && cd ..
```

Create a .env file in the project root:

```dotenv
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

1. Write a theorem in a Lean file (lean_workspace/Problems/), with sorry as     proof e.g. Example.lean:

   ```lean
   import Mathlib

   theorem gauss_sum (n : ℕ) :
       2 * (∑ i ∈ Finset.range (n + 1), i) = n * (n + 1) := by
     sorry
   ```

2. Run the agent from the project root:

   ```bash
   poetry run python -m lean_proof_agent lean_workspace/Problems/Example.lean
   ```

   Options are attempts and model: --attempts N (default: 5), --model model_id (e.g. claude-opus-5-5)


3. Claude proposes a proof and checks it with the check_proof tool. If Lean rejects it, Claude gets the error messages and tries again until the proof is verified or the attempts run out.

4. A verified proof is saved next to the input file as Example_proved.lean, including the output of #print axioms.

## Tests

```bash
pytest -m "not lean"   # fast tests, Lean and Claude are faked
pytest                 # also runs 2 tests with the real Lean compiler (~40 s)
```

## Limitations
The agent can proof exactly one theorem with := by sorry per file. The statement can only contain Mathlib terms. User-defined defs or previously proven lemmas in the file are not passed on to Claude.

## Security
**Not a Sandbox!**
Lean is run as a regular local process with your user permission.
Lean code can execute arbitrary programs during checking (e.g. via `#eval`),
only use this tool with trusted theorem files.
