# lean-proof-agent

An LLM agent proving mathematical theorems in **Lean 4**. 
Claude proposes proofs through the Anthropic API, the Lean compiler checks them. A proof is only accepted if Lean verifies it without errors, without sorry, and without relying on non-standard axioms.

## Functioning
1. The statement is read from a Lean file in which the theorem has `sorry` as its proof.
2. Claude gets the extracted theorem statement and can submit proof attempts through the check_proof tool. The application combines each proof attempt with the original statement, so Claude cannot replace the theorem that is being verified.
3. Every attempt is checked with Lean and if Lean rejects it Claude gets the reasons and error messages back and tries again.
4. The run ends when a proof is verified or the attempts run out.

A proof counts as verified only if

- Lean reports no errors and no `sorry`, and
- `#print axioms` shows that the theorem relies only on the standard axioms of Lean namely (`propext`, `Classical.choice`, `Quot.sound`). This rejects for example `native_decide`, which trusts compiled code.

## Requirements

- Python ≥ 3.13, [Poetry](https://python-poetry.org/)
- Anthropic API key
- Lean 4 via [elan](https://github.com/leanprover/elan)

The Lean workspace specifies Lean 4.36.0 and uses Mathlib as its mathematical library.

## Installation

```bash
poetry install --with dev
cd lean_workspace && lake exe cache get && cd ..
```
lake exe cache get downloads the precompiled Mathlib which is several GB.

Create a .env file in the project root and enter your API Key:

```dotenv
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

1. Write a theorem in a Lean file (lean_workspace/Problems/), with sorry as proof e.g. Example.lean:

   ```lean
   import Mathlib

   theorem gauss_sum (n : ℕ) : 2 * (∑ i ∈ Finset.range (n + 1), i) = n * (n + 1) := by
     sorry
   ```

2. Run the agent from the project root:

   ```bash
   poetry run python -m lean_proof_agent lean_workspace/Problems/Example.lean
   ```

   Options are attempts and model: --attempts N (default: 5), --model model_id (e.g. claude-opus-5-5)

3. A verified proof is saved next to the input file as Example_proved.lean. See Example_proved.lean for the result of the example above.

## Tests

```bash
poetry run pytest -m "not lean"  # fast tests, Lean and Claude are faked
poetry run pytest              # also runs 2 tests with the real Lean compiler (~40 s)
```

## Limitations
The agent can prove exactly one theorem with sorry per file. The statement can only contain Mathlib terms. User-defined defs or previously proven lemmas in the file are not passed on to Claude. The checks catch the more common ways to cheat by `sorry`, `native_decide` and other extra axioms, or a second theorem with the same name. Other checks are **not** included.

## Security
**Not a Sandbox!**
Lean is run as a regular local process with your user permission.
Lean code can execute arbitrary programs during checking (e.g. via `#eval`) including the proofs Claude generates. Only use this tool with trusted theorem files.

## License

MIT, see [LICENSE](LICENSE).