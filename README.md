## lean-proof-agent

An LLM agent proving mathematical theorems in **Lean 4**. 
Using Claude (Anthropic API), proposes proofs, Lean compiler checks them. A theorem only counts as proved once Lean's kernel has accepted the proof.

## Setup

Requirements: Python ≥ 3.13, [Poetry](https://python-poetry.org/),
Lean 4 via [elan](https://github.com/leanprover/elan), an Anthropic API key.

```bash
git clone https://github.com/<your-user>/lean-proof-agent.git
cd lean-proof-agent

# Python dependencies
poetry install

## Project structure

src/lean_proof_agent/   Python package 
lean_workspace/         Lean 4 project with Mathlib, used to check proofs