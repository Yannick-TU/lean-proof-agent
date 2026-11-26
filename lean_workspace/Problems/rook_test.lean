import Mathlib

theorem rook_tail_bound (n k : ℕ) :
    ∏ j ∈ Finset.Icc 2 (k + 1),
        ((n - j / 2 : ℕ) : ℝ) / ∑ i ∈ Finset.Icc 1 j, ((n - i / 2 : ℕ) : ℝ)
      ≤ 1 / ((k + 1).factorial : ℝ) := by
  sorry
