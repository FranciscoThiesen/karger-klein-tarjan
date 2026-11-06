import KKTRecurrence

/-!
A finite, well-founded expected-cost recursion, with explicit KKT premises.
This is an abstract cost model, not a graph implementation or a C++ refinement.
Outcomes may correlate the two children. Only the conditional mean-size bounds
are used; the KKT sampling lemma and implementation work bounds remain premises.
-/

namespace KKTExpectedWork

structure Model (State : Type) where
  vertices : State → ℕ
  edges : State → ℝ
  outcomes : State → Finset (State × State)
  weight : State → (State × State) → ℝ
  weight_nonneg : ∀ g o, o ∈ outcomes g → 0 ≤ weight g o
  normalized : ∀ g, (outcomes g).Nonempty → ∑ o ∈ outcomes g, weight g o = 1
  localWork : State → ℝ
  localWork_nonneg : ∀ g, 0 ≤ localWork g
  smaller : ∀ g o, o ∈ outcomes g →
    vertices o.1 < vertices g ∧ vertices o.2 < vertices g

noncomputable def expectedWork {State : Type} (M : Model State) (g : State) : ℝ :=
  M.localWork g + ∑ o ∈ (M.outcomes g).attach,
    M.weight g o.val * (expectedWork M o.val.1 + expectedWork M o.val.2)
termination_by M.vertices g
decreasing_by
  · exact (M.smaller g o.val o.property).1
  · exact (M.smaller g o.val o.property).2

theorem expectedWork_eq {State : Type} (M : Model State) (g : State) :
    expectedWork M g = M.localWork g + ∑ o ∈ M.outcomes g,
      M.weight g o * (expectedWork M o.1 + expectedWork M o.2) := by
  rw [expectedWork]
  congr 1
  exact Finset.sum_attach (M.outcomes g)
    (fun o => M.weight g o * (expectedWork M o.1 + expectedWork M o.2))

/-- Full induction over the finite recursive computation, not just one step.
The local-work and expected child-size bounds are explicit assumptions.
An empty public call's fixed overhead must be charged separately. -/
theorem affine_expected_work_bound {State : Type} (M : Model State)
    {c a b p : ℝ}
    (ha : 0 ≤ a) (hb : 0 ≤ b)
    (edges_nonneg : ∀ g, 0 ≤ M.edges g)
    (local_bound : ∀ g, M.localWork g ≤ c * (M.edges g + M.vertices g))
    (sample_edges : ∀ g, (∑ o ∈ M.outcomes g, M.weight g o * M.edges o.1)
      ≤ p * M.edges g)
    (light_edges : ∀ g, (∑ o ∈ M.outcomes g, M.weight g o * M.edges o.2)
      ≤ (M.vertices g : ℝ) / (4 * p))
    (sample_vertices : ∀ g, (∑ o ∈ M.outcomes g, M.weight g o * M.vertices o.1)
      ≤ (M.vertices g : ℝ) / 4)
    (light_vertices : ∀ g, (∑ o ∈ M.outcomes g, M.weight g o * M.vertices o.2)
      ≤ (M.vertices g : ℝ) / 4)
    (edge_budget : c + a * p ≤ a)
    (vertex_budget : c + a / (4 * p) + b / 2 ≤ b) :
    ∀ g, expectedWork M g ≤ a * M.edges g + b * M.vertices g := by
  have bound : ∀ n : ℕ, ∀ g, M.vertices g = n →
      expectedWork M g ≤ a * M.edges g + b * M.vertices g := by
    intro n
    induction n using Nat.strong_induction_on with
    | h n ih =>
      intro g hg
      have child_bound : ∀ o ∈ M.outcomes g,
          M.weight g o * (expectedWork M o.1 + expectedWork M o.2) ≤
          M.weight g o * ((a * M.edges o.1 + b * M.vertices o.1) +
            (a * M.edges o.2 + b * M.vertices o.2)) := by
        intro o ho
        apply mul_le_mul_of_nonneg_left _ (M.weight_nonneg g o ho)
        exact add_le_add
          (ih _ (hg ▸ (M.smaller g o ho).1) o.1 rfl)
          (ih _ (hg ▸ (M.smaller g o ho).2) o.2 rfl)
      have distribute :
          (∑ o ∈ M.outcomes g, M.weight g o *
            ((a * M.edges o.1 + b * M.vertices o.1) +
             (a * M.edges o.2 + b * M.vertices o.2))) =
          (a * (∑ o ∈ M.outcomes g, M.weight g o * M.edges o.1) +
           b * (∑ o ∈ M.outcomes g, M.weight g o * M.vertices o.1)) +
          (a * (∑ o ∈ M.outcomes g, M.weight g o * M.edges o.2) +
           b * (∑ o ∈ M.outcomes g, M.weight g o * M.vertices o.2)) := by
        simp only [Finset.mul_sum, ← Finset.sum_add_distrib]
        apply Finset.sum_congr rfl
        intro o ho
        ring
      calc
        expectedWork M g = M.localWork g + ∑ o ∈ M.outcomes g,
            M.weight g o * (expectedWork M o.1 + expectedWork M o.2) :=
          expectedWork_eq M g
        _ ≤ c * (M.edges g + M.vertices g) +
            ∑ o ∈ M.outcomes g, M.weight g o *
              ((a * M.edges o.1 + b * M.vertices o.1) +
               (a * M.edges o.2 + b * M.vertices o.2)) :=
          add_le_add (local_bound g) (Finset.sum_le_sum child_bound)
        _ = _ := congrArg (fun x => c * (M.edges g + M.vertices g) + x) distribute
        _ ≤ a * M.edges g + b * M.vertices g := by
          simpa only [add_assoc] using
            KKTRecurrence.affine_step ha hb (edges_nonneg g) (Nat.cast_nonneg _)
            (sample_edges g) (light_edges g) (sample_vertices g) (light_vertices g)
            edge_budget vertex_budget
  intro g
  exact bound (M.vertices g) g rfl

/-- Inserting n distinct keys into one chained bucket inspects this many
previous entries, if each insertion scans the complete existing bucket. -/
theorem collision_chain_traversals (n : ℕ) :
    2 * (∑ k ∈ Finset.range n, k) = n * (n - 1) := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Finset.sum_range_succ]
    cases n with
    | zero => simp
    | succ n => simp only [Nat.add_sub_cancel] at *; nlinarith

/-- The abstract all-colliding bucket walk has no uniform linear bound in n.
This theorem is about the unbounded natural-number cost model; an actual
fixed-width ID representation imposes a finite valid-input limit. -/
theorem collision_work_not_uniform_linear (K : ℕ) :
    ∃ n : ℕ, K * n < ∑ k ∈ Finset.range n, k := by
  refine ⟨2 * K + 2, ?_⟩
  have h := collision_chain_traversals (2 * K + 2)
  have subtract : 2 * K + 2 - 1 = 2 * K + 1 := by omega
  rw [subtract] at h
  nlinarith

/-- A fixed upper bound on cost per charged operation transfers a linear
operation bound to a linear cost bound. Variable observed cost per operation
alone does not contradict the operation bound or prove N log N asymptotics. -/
theorem bounded_operation_cost {N K L work time : ℝ}
    (hL : 0 ≤ L) (work_bound : work ≤ K * N)
    (time_bound : time ≤ L * work) : time ≤ (L * K) * N := by
  calc
    time ≤ L * work := time_bound
    _ ≤ L * (K * N) := mul_le_mul_of_nonneg_left work_bound hL
    _ = (L * K) * N := by ring

/-- Individual operations need not have identical cost. A uniform bound is
enough, including a finite hierarchy of cache-hit and memory-access costs. -/
theorem sum_cost_le_uniform {Op : Type} (ops : Finset Op) (cost : Op → ℝ)
    (C : ℝ) (per_operation : ∀ op ∈ ops, cost op ≤ C) :
    (∑ op ∈ ops, cost op) ≤ C * ops.card := by
  calc
    (∑ op ∈ ops, cost op) ≤ ∑ _op ∈ ops, C := Finset.sum_le_sum per_operation
    _ = C * ops.card := by simp [mul_comm]

/-- A deterministic 32-bit seed cannot cover every 33-bit sampling pattern.
Connecting bit patterns to a Bernoulli distribution is a separate obligation.
This does not imply that a particular PRNG is slow or incorrect. -/
theorem no_full_33_bit_support_from_32_bit_seed :
    ¬ ∃ f : Fin (2 ^ 32) → Fin (2 ^ 33), Function.Surjective f := by
  rintro ⟨f, hf⟩
  have h := Fintype.card_le_of_surjective f hf
  norm_num at h

end KKTExpectedWork

#print axioms KKTExpectedWork.expectedWork_eq
#print axioms KKTExpectedWork.affine_expected_work_bound
#print axioms KKTExpectedWork.collision_chain_traversals
#print axioms KKTExpectedWork.collision_work_not_uniform_linear
#print axioms KKTExpectedWork.bounded_operation_cost
#print axioms KKTExpectedWork.sum_cost_le_uniform
#print axioms KKTExpectedWork.no_full_33_bit_support_from_32_bit_seed
