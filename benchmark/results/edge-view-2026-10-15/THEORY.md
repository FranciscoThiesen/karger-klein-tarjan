# Retaining parallel quotient edges: what the expected bound supports

The original [Karger–Klein–Tarjan paper](https://people.csail.mit.edu/karger/Papers/mst.pdf),
§3, removes all but the cheapest edge between each pair of contracted vertices.
Our retained-parallel implementation therefore differs from its stated algorithm.

**Our inference:** retaining those crossing edges preserves the expected
linear-work recurrence. Lemma 1 (§2) processes individual edges in weight order,
testing connectivity before each independent sampling decision. Parallel edges
do not invalidate that argument: the expected number of F-light edges is at
most the number of vertices divided by the sampling probability. The deduction
below extends that reasoning; it is not an explicit retained-parallel theorem
stated in the paper.

Let a call have `n` vertices and `m` edge records. After two contractions, let
`q ≤ n/4` and `r ≤ m`. With independent half-sampling, sample size `X` has
`E[X] = r/2 ≤ m/2`; the number `Y` of F-light records satisfies `E[Y] ≤ 2q`.
Assuming local work at most `c(m+n)`,

```
E[T(n,m)] ≤ c(m+n) + E[T(q,X) + T(q,Y)].
```

Induction bounding the expected cost of every fixed input by `Am + Bn`
(conditioning on each recursive input, with fresh sampling randomness) closes because

```
E[T(n,m)] ≤ (c + A/2)m + (c + A/2 + B/2)n,
```

with `A ≥ 2c` and `B ≥ A + 2c` (adjusting constants for base cases).
This gives expected `O(m+n)`. Here `m` counts parallel records individually.

The paper's Theorem 1 also gives an `O(n²)` worst-case cap using the absence
of parallel edges in every subproblem. That argument does **not** transfer;
the retained variant must not inherit that cap merely by citation.

## Conditions and implementation limits

- Inputs must be undirected, loop-free, and have distinct weights under the
  current implementation contract. General ties need consistent ordering across
  contraction and verification; that extension has not been implemented.
- The selected contraction edges must be safe MSF edges. Dropping resulting
  loops and isolated quotient vertices preserves the vertex reduction.
- The recursive sample must return a valid MSF. The current verifier processes
  parallel queries separately by position; its forest input must remain acyclic.
  Cross-component queries stay light. No simple-query-graph assumption is needed.
- The recurrence assumes fresh independent sampling bits, including conditional
  on earlier recursion. The executable instead uses a deterministic, finitely
  seeded `mt19937` stream. Its seed space is not the ideal independent-coin model.
- Contraction, sampling, filtering, and verification must take linear local
  work. The verifier's implementation-level argument, integer/index/mask bounds,
  and word-operation assumptions remain relevant; finite tests and complexity
  fits do not prove them. The public `unordered_set` result wrapper additionally
  relies on expected hashing cost.

This supports the algorithmic rationale for the experiment. It does not prove
linear wall time, practical dominance, a crossover, or suitability for production.
