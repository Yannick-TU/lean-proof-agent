"""Command line entry point:  python -m lean_proof_agent <file.lean>

The Lean file must contain exactly one theorem or lemma with `sorry` as proof.
Only the statement is used: the theorem is checked with the fixed HEADER, so it
must not depend on imports, `open`, `variable` or definitions from the input file.
If Claude finds a proof that Lean verifies, it is saved next to the input file.
"""

import argparse
import logging
import re
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from lean_proof_agent.agent import DEFAULT_MODEL, prove
from lean_proof_agent.lean_runner import HEADER, LeanRunner
from lean_proof_agent.verifier import build_lean_code

STATEMENT_PATTERN = re.compile(
    r"^((?:theorem|lemma)\s(?:(?!:=).)*?)\s*:=\s*(?:by\s+)?sorry\b",
    re.MULTILINE | re.DOTALL,
)


# Find 'theorem foo ... := by sorry' in a Lean file, return 'theorem foo ...'
def read_statement(path: Path) -> str:

    text = path.read_text(encoding="utf-8")
    statements = STATEMENT_PATTERN.findall(text)
    if not statements:
        raise ValueError(f"No theorem ending with ':= by sorry' found in {path}")
    if len(statements) > 1:
        raise ValueError(
            f"Found {len(statements)} theorems with sorry in {path}, expected exactly one"
        )
    return statements[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Let Claude prove a Lean theorem.")
    parser.add_argument("file", type=Path, help="Lean file with a theorem and sorry")
    parser.add_argument("--attempts", type=int, default=5, help="max proof attempts")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Claude model")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # hide HTTP request logs
    load_dotenv()

    statement = read_statement(args.file)
    print(f"Proving: {statement}\n")
    result = prove(
        statement,
        client=anthropic.Anthropic(),
        checker=LeanRunner(),
        model=args.model,
        max_attempts=args.attempts,
    )

    status = "PROVED" if result.proved else "NOT PROVED"
    print(
        f"\n{status} after {len(result.attempts)} attempt(s), {result.duration_s:.0f} s"
    )
    print(f"Tokens: {result.input_tokens} in / {result.output_tokens} out")
    if result.proof is None:
        return 1

    code, _ = build_lean_code(statement, result.proof)
    output = args.file.with_name(args.file.stem + "_proved.lean")
    output.write_text(HEADER + code + "\n", encoding="utf-8")
    print(f"\nProof:\n{result.proof}\n\nSaved to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
