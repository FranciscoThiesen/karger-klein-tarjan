# Density-based sampling: a separate, unexecuted proposal

Source/theory preparation, 2026-10-15. This does not change the frozen eighth
experiment. No implementation, tests or performance measurements are included.
The following is our derivation, not a claim that the original paper proposes
or experimentally validates this policy.

The [KKT paper, Lemma 1](https://people.csail.mit.edu/karger/Papers/mst.pdf)
bounds the expected number of light edges by q/p under independent sampling.
Use the same loop-free multigraph, unique-weight, isolation-removal and linear
primitive assumptions as FIXED_SAMPLING_PROBABILITY.md. After two contractions,
let q be remaining vertices and r the number of retained edge records. Then
q <= n/4 and r <= m. Empty quotients return before choosing a probability.

Condition on this entire quotient and its history, then choose p using only
(q,r), before drawing fresh sample bits. If X is sample size and Y light-edge
count, E[X+Y | quotient] <= W(p) = pr + q/p. This is a bound on child input
volume; it is neither a runtime model nor the actual survivor count.

## A policy with the same uniform potential bound as half sampling

Choose a probability minimizing W over {1/2, 1/4, 1/8, ...}. The minimum exists
for q>0 because q/p tends to infinity. Since half sampling is a candidate,

    E[X+Y | quotient] <= W(p) <= r/2 + 2q <= m/2 + n/2.

Each child has at most q vertices. For nonrecursive work <= c(m+n), induction
using T(n,m) <= A m + B n gives

    E[T(n,m)] <= (c + A/2)m + (c + A/2 + B/2)n.

Thus A >= 2c and B >= 2c + A suffice, exactly the sufficient coefficients
of the half-sampling potential argument. Base/empty costs give O(m+n+1).
Unlike an arbitrary size-dependent probability, this particular adaptive
policy preserves a uniform expected-linear bound because its conditional
child-volume bound never exceeds the half-sampling bound.

This proof uses a fresh independent sample conditional on each input. The
finite seeded mt19937 program does not literally provide that conditional
independence. Retained parallel records count toward r; disconnected samples
and their isolates do not invalidate the sampling inequality. The coefficient
c covers the policy's extra local work and need not equal a measured reference
coefficient. This proves no wall-time improvement, high-probability bound, or
simple-graph worst-case cap for the retained-parallel implementation.

## Exact dyadic choice without logarithms or floating point

The change from p to p/2 improves W precisely when

    W(p/2) < W(p)  iff  r p^2 > 2q.

Starting at p=1/2, halve while the condition holds. Once it stops, further
halving cannot help, since the left side decreases by four each time. Prefer
the larger probability on ties. Equivalently, select k starting at 1, and
advance while r > 2q * 4^k; p = 2^-k.

An overflow-safe integer formulation keeps t = ceil(r/4^(k-1)):

    k = 1; t = r
    while ceil_div(t, 8) > q:
        t = ceil_div(t, 4)
        k += 1

Use quotient plus a nonzero-remainder flag for ceil_div, avoiding t+b-1
overflow. The condition is exactly t > 8q without computing 8q. Iterated
ceiling division preserves the stated t invariant. This selects the exact
dyadic minimizer, not merely rounding the continuous optimum downward.
Choosing p below sqrt(q/r) without the comparison can make W worse than
half sampling near a dyadic boundary; that is a different policy.

The policy computation takes O(log r) steps, subsumed in the local O(m+n)
bound. Under the current signed-32-bit edge-count domain and positive q,
k <= 15: at k=15, 2q*4^15 >= 2^31 > r. A mask (1u<<k)-1 therefore fits a
32-bit engine word. An eventual implementation must validate the actual
supported edge-count domain before relying on this argument. For a formal
unbounded word-RAM model, the random word needs enough bits for the input
size; fixed 32-bit code is not an unbounded-size implementation.

For the ordered hierarchy's root r/q=249, this rule chooses p=1/16: the
1/8-to-1/16 boundary is r/q=128, and the next is 512. This is a source-derived
policy prediction, not an observed optimum. Child quotients may choose
different probabilities, and recursive forests/RNG states will differ from
fixed-rate runs.

## Experimental boundary if pursued later

First finish the fixed half/eighth study. A later isolated change could select
only the private mask from the already available post-contraction q/r; keep
one word per edge, half-size reserve, order/IDs, public half sampler, verifier,
lifetimes and every baseline unchanged. It must use a fresh same-source half
control if shared refactoring changes the reference translation unit.

Required gates include independent integer/rational minimization on a broad
finite (q,r) grid, threshold/tie/maximum-domain cases, actual private dispatch
and wrong-policy rejection, exact public sampler behavior, and native plus
sanitizer full-MSF differential tests. This finite oracle would check the code;
the derivation above supplies the unbounded mathematical argument.

Record the chosen masks and per-call q/r in separate untimed diagnostics if
needed, without changing timing instrumentation. Keep all declared losses and
unchanged-solver controls. A bound on child edge volume omits forest shape,
query cost, memory traffic, allocation, and fixed parent work, so the best W
does not have to give the best measured time.
