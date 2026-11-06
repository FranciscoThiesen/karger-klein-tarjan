import Mathlib

/-!
Checked with Lean 4.24.0 / mathlib v4.24.0; see verification-2026-11-05.

These are conditional arithmetic lemmas for ONE expected-cost induction step.
The variables ms, ml, ns, nl can be expected child sizes, once a separate
probabilistic proof supplies their bounds. This file does not define graphs,
sampling, a verifier, C++ semantics, or the whole recursive algorithm.
-/

namespace KKTRecurrence

/-- Close an affine budget after the probabilistic and inductive obligations
have supplied the four child-size bounds. No independence of the two children
is assumed here; that is not needed for addition of expectations. -/
theorem affine_step
    {c a b p m n ms ml ns nl : ℝ}
    (ha : 0 ≤ a) (hb : 0 ≤ b) (hm : 0 ≤ m) (hn : 0 ≤ n)
    (sample_edges : ms ≤ p * m)
    (light_edges : ml ≤ n / (4 * p))
    (sample_vertices : ns ≤ n / 4)
    (light_vertices : nl ≤ n / 4)
    (edge_budget : c + a * p ≤ a)
    (vertex_budget : c + a / (4 * p) + b / 2 ≤ b) :
    c * (m + n) + (a * ms + b * ns) + (a * ml + b * nl)
      ≤ a * m + b * n := by
  have hms := mul_le_mul_of_nonneg_left sample_edges ha
  have hml := mul_le_mul_of_nonneg_left light_edges ha
  have hns := mul_le_mul_of_nonneg_left sample_vertices hb
  have hnl := mul_le_mul_of_nonneg_left light_vertices hb
  have hem := mul_le_mul_of_nonneg_right edge_budget hm
  have hvn := mul_le_mul_of_nonneg_right vertex_budget hn
  calc
    c * (m + n) + (a * ms + b * ns) + (a * ml + b * nl)
        ≤ c * (m + n) + (a * (p * m) + b * (n / 4))
          + (a * (n / (4 * p)) + b * (n / 4)) := by linarith
    _ = (c + a * p) * m + (c + a / (4 * p) + b / 2) * n := by ring
    _ ≤ a * m + b * n := add_le_add hem hvn

/-- The familiar half-sampling constants, assuming a common local-cost c. -/
theorem half_sample_step
    {c m n ms ml ns nl : ℝ}
    (hc : 0 ≤ c) (hm : 0 ≤ m) (hn : 0 ≤ n)
    (sample_edges : ms ≤ m / 2) (light_edges : ml ≤ n / 2)
    (sample_vertices : ns ≤ n / 4) (light_vertices : nl ≤ n / 4) :
    c * (m + n) + (2 * c * ms + 4 * c * ns)
      + (2 * c * ml + 4 * c * nl) ≤ 2 * c * m + 4 * c * n := by
  apply affine_step (p := (1 / 2 : ℝ))
  · positivity
  · positivity
  · exact hm
  · exact hn
  · linarith
  · linarith
  · exact sample_vertices
  · exact light_vertices
  · linarith
  · linarith

/-- The selected implementation's idealized eighth-sampling constants.
The hypotheses still require a separate sampling-lemma proof. -/
theorem eighth_sample_step
    {c m n ms ml ns nl : ℝ}
    (hc : 0 ≤ c) (hm : 0 ≤ m) (hn : 0 ≤ n)
    (sample_edges : ms ≤ m / 8) (light_edges : ml ≤ 2 * n)
    (sample_vertices : ns ≤ n / 4) (light_vertices : nl ≤ n / 4) :
    c * (m + n) + ((8 / 7 : ℝ) * c * ms + (46 / 7 : ℝ) * c * ns)
      + ((8 / 7 : ℝ) * c * ml + (46 / 7 : ℝ) * c * nl)
      ≤ (8 / 7 : ℝ) * c * m + (46 / 7 : ℝ) * c * n := by
  apply affine_step (p := (1 / 8 : ℝ))
  · positivity
  · positivity
  · exact hm
  · exact hn
  · norm_num [div_eq_mul_inv] at *; linarith
  · norm_num [div_eq_mul_inv] at *; linarith
  · exact sample_vertices
  · exact light_vertices
  · norm_num [div_eq_mul_inv] at *; linarith
  · norm_num [div_eq_mul_inv] at *; linarith

end KKTRecurrence

#print axioms KKTRecurrence.affine_step
#print axioms KKTRecurrence.half_sample_step
#print axioms KKTRecurrence.eighth_sample_step
