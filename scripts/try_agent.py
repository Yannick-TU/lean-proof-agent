# Connect to anthropic and lean, use prove() for the proof process.

import logging

import anthropic
from dotenv import load_dotenv

from lean_proof_agent.agent import prove
from lean_proof_agent.lean_runner import LeanRunner

STATEMENT = (
    "theorem gauss_sum (n : ℕ) : 2 * (∑ i ∈ Finset.range (n + 1), i) = n * (n + 1)"
)


def main():
    load_dotenv()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    client = anthropic.Anthropic()
    checker = LeanRunner()

    result = prove(STATEMENT, client=client, checker=checker)

    status = "PROVED" if result.proved else "NOT PROVED"

    print(f"\n{status}")
    print(f"Attempts: {len(result.attempts)}")
    print(f"Duration: {result.duration_s:.0f} seconds")
    print(f"Tokens: {result.input_tokens} in / {result.output_tokens} out")

    if result.proof:
        print("\nProof:")
        print(result.proof)


if __name__ == "__main__":
    main()
