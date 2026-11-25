"""The proof agent: Claude proposes proofs, Lean checks them, errors are fed back.

1. Claude gets the theorem and a tool `check_proof`.
2. Claude calls the tool with a proof attempt.
3. We check the attempt with the verifier (Lean) and send the result back to Claude.
4. Repeat until a proof is verified, Claude stops, or `max_attempts` is reached.
"""

from __future__ import annotations

import logging
import time

from dataclasses import dataclass
from typing import Any, cast

import anthropic
from anthropic.types import MessageParam, ToolParam

from lean_proof_agent.lean_runner import LeanRunner
from lean_proof_agent.verifier import Verdict, build_lean_code, verify

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_FEEDBACK_CHARS = 4000

SYSTEM_PROMPT = """
You are an expert in Lean 4 and Mathlib. Your task is to prove the theorem the user gives you.

Use the `check_proof` tool to test a proof with Lean. If the proof is rejected, read Lean's
messages carefully, fix the proof and check again. Proofs that use `sorry`, `admit` or
`native_decide` are always rejected.
"""
# Tool definition, allows Claude to verify proofs with Lean
CHECK_PROOF_TOOL : ToolParam = {
    "name": "check_proof",
    "description": (
        "Check a proof of the theorem with Lean 4 and Mathlib. "
        "Returns VERIFIED if the proof is complete and correct, "
        "otherwise the reasons for the rejection and Lean's messages."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "proof": {
                "type": "string",
                "description": (
                    "Only the proof: everything that comes after `:=` in the theorem, "
                    "usually starting with `by`. Do not repeat the theorem statement."
                ),
            }
        },
        "required": ["proof"],
    },
}


# Stores the result of a single proof attempt
@dataclass(frozen=True)
class Attempt:
    proof: str
    verified: bool
    problems: tuple[str, ...]


# the outcome of a single proof run
@dataclass(frozen=True)
class ProofResult:
    statement: str
    proved: bool
    proof: str | None  # the verified proof, if one was found
    attempts: tuple[Attempt, ...]
    input_tokens: int
    output_tokens: int
    duration_s: float


# Formats Lean feedback into text for Claude
def format_feedback(statement: str, proof: str, verdict: Verdict) -> str:
    if verdict.verified:
        return "VERIFIED: Lean accepted the proof."

    code, _ = build_lean_code(statement, proof)
    numbered_code = "\n".join(
        f"{number:>3} | {line}"
        for number, line in enumerate(code.splitlines(), start=1)
    )
    # read error messages
    messages = [m.format() for m in verdict.lean_result.messages] or ["(none)"]
    # combine lean message
    text = "\n".join(
        ["REJECTED:"]
        + [f"- {problem}" for problem in verdict.problems]
        + ["", "Checked code (Lean's line numbers refer to it):", numbered_code]
        + ["", "Lean messages:"]
        + messages
    )
    # cut if too long
    if len(text) > MAX_FEEDBACK_CHARS:
        text = text[:MAX_FEEDBACK_CHARS] + "\n... (truncated)"
    return text


# Claude proves a statement and checks every attempt with Lean.
def prove(
    statement: str,
    client: anthropic.Anthropic,
    checker: LeanRunner,
    model: str = DEFAULT_MODEL,
    max_attempts: int = 5,
    max_tokens: int = 4000,
) -> ProofResult:

    start = time.perf_counter()
    messages: list[MessageParam] = [{"role": "user", "content": f"Prove this theorem: \n\n{statement}"}]
    attempts: list[Attempt] = []
    input_tokens = output_tokens = 0
    proof_found: str | None = None

    while proof_found is None and len(attempts) < max_attempts:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            tools=[CHECK_PROOF_TOOL],
            messages=messages,
        )
        input_tokens += response.usage.input_tokens
        output_tokens += response.usage.output_tokens

        # The API is stateless, we store Claudes rsponse in conversation history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            logger.info(
                "Claude stopped without checking a proof (%s)", response.stop_reason
            )
            break
        tool_results = []

        # Checking Clauds answer
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_input = cast(dict[str, Any], block.input)
            proof = block.input.get("proof", "")
            verdict = verify(statement, proof, checker)
            attempts.append(Attempt(proof, verdict.verified, verdict.problems))
            logger.info(
                "Attempt %d: %s",
                len(attempts),
                "VERIFIED" if verdict.verified else "; ".join(verdict.problems),
            )

            if verdict.verified:
                proof_found = proof
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": format_feedback(statement, proof, verdict),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return ProofResult(
        statement=statement,
        proved=proof_found is not None,
        proof=proof_found,
        attempts=tuple(attempts),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_s=time.perf_counter() - start,
    )
