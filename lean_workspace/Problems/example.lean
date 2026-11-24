import Mathlib

-- Run from the project root:
--   python -m lean_proof_agent lean_workspace/Problems/Example.lean

theorem gauss_sum (n : ℕ) : 2 * (∑ i ∈ Finset.range (n + 1), i) = n * (n + 1) := by
  sorry
