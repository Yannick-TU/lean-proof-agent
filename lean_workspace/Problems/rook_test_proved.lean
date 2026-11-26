import Mathlib

theorem rook_tail_bound (n k : ℕ) :
    ∏ j ∈ Finset.Icc 2 (k + 1),
        ((n - j / 2 : ℕ) : ℝ) / ∑ i ∈ Finset.Icc 1 j, ((n - i / 2 : ℕ) : ℝ)
      ≤ 1 / ((k + 1).factorial : ℝ) :=
  by
    have key : ∀ j ∈ Finset.Icc 2 (k + 1),
        ((n - j / 2 : ℕ) : ℝ) / ∑ i ∈ Finset.Icc 1 j, ((n - i / 2 : ℕ) : ℝ) ≤ 1 / (j : ℝ) := by
      intro j hj
      rw [Finset.mem_Icc] at hj
      have hjpos : (0:ℝ) < j := by
        have : 0 < j := by omega
        exact_mod_cast this
      have hS : (j:ℝ) * ((n - j / 2 : ℕ) : ℝ) ≤ ∑ i ∈ Finset.Icc 1 j, ((n - i / 2 : ℕ) : ℝ) := by
        have h := Finset.card_nsmul_le_sum (Finset.Icc 1 j) (fun i => ((n - i / 2 : ℕ) : ℝ))
          ((n - j / 2 : ℕ) : ℝ) (by
            intro i hi
            rw [Finset.mem_Icc] at hi
            have : n - j / 2 ≤ n - i / 2 := Nat.sub_le_sub_left (Nat.div_le_div_right hi.2) n
            exact_mod_cast this)
        simpa using h
      have hS0 : (0:ℝ) ≤ ∑ i ∈ Finset.Icc 1 j, ((n - i / 2 : ℕ) : ℝ) :=
        Finset.sum_nonneg (fun i _ => Nat.cast_nonneg _)
      rcases hS0.eq_or_lt with h | h
      · rw [← h, div_zero]; positivity
      · rw [div_le_iff₀ h]
        rw [one_div, inv_mul_eq_div, le_div_iff₀ hjpos]
        linarith
    have h1 : ∏ j ∈ Finset.Icc 2 (k + 1),
          ((n - j / 2 : ℕ) : ℝ) / ∑ i ∈ Finset.Icc 1 j, ((n - i / 2 : ℕ) : ℝ)
        ≤ ∏ j ∈ Finset.Icc 2 (k + 1), 1 / (j : ℝ) := by
      apply Finset.prod_le_prod₀
      · intro j _
        exact div_nonneg (Nat.cast_nonneg _) (Finset.sum_nonneg (fun i _ => Nat.cast_nonneg _))
      · exact key
    refine h1.trans (le_of_eq ?_)
    clear h1 key
    induction k with
    | zero => simp
    | succ m ih =>
      rw [Finset.prod_Icc_succ_top (by omega), ih, Nat.factorial_succ (m + 1)]
      push_cast
      field_simp

#print axioms rook_tail_bound
