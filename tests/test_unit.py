"""Fast tests: Lean and Claude are replaced by fakes (no Lean, no API costs)."""

from types import SimpleNamespace

import pytest

from lean_proof_agent.agent import prove
from lean_proof_agent.lean_runner import LeanMessage, LeanResult, parse_messages
from lean_proof_agent.verifier import verify

STATEMENT = "theorem t (a b : ℕ) : a + b = b + a"
PROOF = "by omega"
AXIOMS_LINE = 4  # statement, proof, empty line, #print axioms


def lean_result(*messages: LeanMessage, returncode: int = 0) -> LeanResult:
    return LeanResult(messages, returncode=returncode, stderr="", duration_s=0.0)


def axioms(names: str) -> LeanMessage:
    text = f"'t' depends on axioms: [{names}]"
    return LeanMessage("information", text, line=AXIOMS_LINE, column=0)


# Typical answers from Lean
ACCEPTED = lean_result(axioms("propext"))
SORRY = lean_result(
    LeanMessage("warning", "declaration uses `sorry`", 1, 8, "hasSorry")
)
ERROR = lean_result(LeanMessage("error", "unsolved goals", 2, 5), returncode=1)
NATIVE_DECIDE = lean_result(axioms("t._native.native_decide.ax_1_1"))


# Plays LeanRunner, returns prepared results one after another.
class FakeLean:
    def __init__(self, *results: LeanResult):
        self.results = list(results)
        self.code = None

    def check(self, code: str) -> LeanResult:
        self.code = code
        return self.results.pop(0)


# Plays Anthropic client, each answer asks to check one proof.
class FakeClaude:
    def __init__(self, *proofs: str):
        self.proofs = list(proofs)
        self.messages = self  # so that client.messages.create(...) works

    def create(self, **request):
        block = SimpleNamespace(
            type="tool_use", id="call", input={"proof": self.proofs.pop(0)}
        )
        usage = SimpleNamespace(input_tokens=100, output_tokens=20)
        return SimpleNamespace(content=[block], stop_reason="tool_use", usage=usage)


# --- lean_runner -------


def test_parse_lean_json_output():
    line = (
        '{"severity":"warning","data":"declaration uses `sorry`",'
        '"pos":{"line":3,"column":8},"kind":"hasSorry"}'
    )
    (message,) = parse_messages(line, line_offset=2)
    assert (message.line, message.column, message.is_sorry) == (1, 8, True)


def test_sorry_is_not_success_although_lean_exits_with_0():
    assert SORRY.returncode == 0
    assert not SORRY.is_success


def test_crash_without_messages_is_not_success():
    assert not lean_result(returncode=1).is_success


# --- verifier -------


def test_honest_proof_is_verified_and_statement_is_ours():
    lean = FakeLean(ACCEPTED)
    assert verify(STATEMENT, PROOF, lean).verified
    assert lean.code.startswith(STATEMENT)


@pytest.mark.parametrize(
    "result", [SORRY, ERROR, NATIVE_DECIDE], ids=["sorry", "error", "native_decide"]
)
def test_cheating_or_wrong_proofs_are_rejected(result):
    assert not verify(STATEMENT, PROOF, FakeLean(result)).verified


# --- agent -------


def test_agent_retries_after_rejection_and_succeeds():
    result = prove(STATEMENT, FakeClaude("by simp", PROOF), FakeLean(ERROR, ACCEPTED))
    assert result.proved
    assert result.proof == PROOF
    assert len(result.attempts) == 2


def test_agent_stops_after_max_attempts():
    claude = FakeClaude("by simp", "by simp", "by simp")
    result = prove(STATEMENT, claude, FakeLean(ERROR, ERROR), max_attempts=2)
    assert not result.proved
    assert len(result.attempts) == 2
