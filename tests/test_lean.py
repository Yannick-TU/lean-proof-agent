"""End-to-end tests with the real Lean compiler (slow, about 20 s each).

Skip them with pytest -m "not lean"
"""

import shutil

import pytest

from lean_proof_agent.lean_runner import LeanRunner
from lean_proof_agent.verifier import verify

pytestmark = [
    pytest.mark.lean,
    pytest.mark.skipif(shutil.which("lake") is None, reason="lake is not installed"),
]


def test_real_lean_accepts_honest_proof():
    statement = "theorem two_mul_le_sq_add_sq (a b : ℝ) : 2 * a * b ≤ a ^ 2 + b ^ 2"
    verdict = verify(statement, "by nlinarith [sq_nonneg (a - b)]", LeanRunner())
    assert verdict.verified, verdict.problems


def test_real_lean_rejects_native_decide():
    statement = "theorem two_add_two : (2 : ℕ) + 2 = 4"
    verdict = verify(statement, "by native_decide", LeanRunner())
    assert not verdict.verified
