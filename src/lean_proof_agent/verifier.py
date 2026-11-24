"""Decide whether a proof from Claude really proves the given statement.

A proof is accepted only if
1. Lean reports no errors and no `sorry`, and
2. it uses only Lean's three standard axioms (this rejects e.g. `native_decide`).

Claude cannot change the statement: it only supplies the proof, the statement is inserted by us.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass

from lean_proof_agent.lean_runner import LeanResult, LeanRunner

# The three axioms of Lean's standard foundations. Anything else is rejected.
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


# Result of verifiying one proof
@dataclass(frozen=True)
class Verdict:
    problems: tuple[str, ...]  # why the proof was rejected (empty if verified)
    lean_result: LeanResult

    @property
    def verified(self) -> bool:
        return not self.problems


# Put our statement and Claude's proof together and add an axiom check
# -> the theorem without proof + everything after `:=`, e.g. 'by simp'
# Returns Lean Code and Line number of `#print axioms`
def build_lean_code(statement: str, proof: str) -> tuple[str, int]:

    match = re.match(r"\s*(?:theorem|lemma)\s+([^\s(:]+)", statement)
    if match is None:
        raise ValueError(f"Statement must start with 'theorem <name>': {statement!r}")
    name = match.group(1)

    body = textwrap.indent(textwrap.dedent(proof).strip(), "  ")
    code = f"{statement.strip()} :=\n{body}\n\n#print axioms {name}"
    return code, code.count("\n") + 1


# Read axioms for the output of `#print axioms`
def used_axioms(result: LeanResult, axioms_line: int) -> set[str] | None:

    for message in result.messages:
        if message.line == axioms_line and message.severity == "information":
            # e.g. "'foo' depends on axioms: [propext, Classical.choice, Quot.sound]"
            match = re.search(r"\[(.*)\]", message.text, re.DOTALL)
            if match is None:  # "'foo' does not depend on any axioms"
                return set()
            return {axiom.strip() for axiom in match.group(1).split(",")}
    return None


# Check whether proof of statement is genuine with Lean.
def verify(statement: str, proof: str, checker: LeanRunner) -> Verdict:

    code, axioms_line = build_lean_code(statement, proof)
    result = checker.check(code)

    problems = []
    if result.timed_out:
        problems.append("Lean timed out")
    elif result.errors:
        problems.append(f"Lean reported {len(result.errors)} error")
    elif result.uses_sorry:
        problems.append("proof uses sorry")
    elif result.returncode != 0:
        problems.append(f"Lean failed with exit code {result.returncode}")
    else:
        # Lean accepted the proof, check which axioms it relies on.
        axioms = used_axioms(result, axioms_line)
        if axioms is None:
            problems.append("could not read the axioms used")
        elif not axioms <= STANDARD_AXIOMS:
            extra = sorted(axioms - STANDARD_AXIOMS)
            problems.append(f"non-standard axioms: {', '.join(extra)}")

    return Verdict(problems=tuple(problems), lean_result=result)
