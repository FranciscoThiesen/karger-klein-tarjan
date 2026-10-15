# Scalar half versus eighth sampling

**Correctness gates passed; performance has not run.** This opt-in experiment
changes one private sampling predicate while keeping the public sampler and
the rest of KKT fixed. Its [original preparation status](PREPARATION_STATUS.md)
and [reviewed source package](validation/source-preparation/ROOT_EXECUTION_HANDOFF.md)
remain available. The matrix was declared before inspecting the separate
larger-hierarchy results.

Each visited edge still consumes one `mt19937` word. The reference accepts odd
words; the candidate accepts words whose low three bits are all one. Both keep
`reserve(m/2)`, compressed verifier queries, retained parallel edges, direct
Edge queries, and the unchanged public half-sampling API. Only `kkt.o` differs;
both final binaries physically share seven production objects and the harness
main. This is a sampling-rate experiment, not packed-bit sampling.

The [fixed-p analysis](../../../docs/kkt-report/FIXED_SAMPLING_PROBABILITY.md)
explains why a constant rate below one half retains the expected linear-work
argument under its stated assumptions. Smaller samples can weaken filtering,
so neither a speedup nor a memory reduction follows from the change alone.

Validation completed in an isolated worktree rooted at
`fbdf4a8571104302ea21464026e86a2257e2add0`:

| Gate | Result | Retained receipt |
|---|---|---|
| Controller, builder and collector mocks | 4 + 7 + 14 groups passed | [controller](validation/controller-mocks-attempt01.json), [builder](validation/build-mocks-attempt01.json), [collector](validation/collector-mocks-attempt01.json) |
| Native AppleClang 15 correctness | Passed | [receipt](validation/native-controller-attempt01.json) |
| Native Clang 22 ASan/UBSan and leak checks | Passed | [receipt](validation/sanitizer-controller-attempt01.json) |
| Uninstrumented shared-object build | Passed; no benchmark execution | [receipt](validation/timing-controller-attempt01.json) |
| Actual final-object correctness and sampling-policy proof | Passed | [receipt](validation/final-controller-attempt01.json) |

Each correctness profile runs twenty positive suites and four wrong-policy
negatives. The full-KKT suite preserves 1,344 exact input/MSF pairs. The fresh
half implementation replays all 65 parent counters; 543 paired fixtures have
different recursive work under eighth sampling. Direct predicate, private
sampling, public API, verifier and independent MSF checks remain separate.
The final-object gate combines certificates using the actual objects, two
byte-identical KKT recompilations, and a separate same-flags private/public
sampling oracle. It does not claim to observe private RNG calls inside the
already linked timing executable. Every owned validation group exited and
was verified empty. No gate failed on execution; the source-review deadline
finding and repair are retained in the preparation review.

The [independent completed-artifact review](validation/INDEPENDENT_READINESS_REVIEW.md)
also passed: it rechecked the full original parent proof, 331 directly pinned
artifacts, all native command outcomes and the actual final binary profiles.

The [protocol](PROTOCOL.md) and [manifest](manifest.csv) fix six cases, two graph
seeds and two sampler seeds: **48 children, 2,016 outputs, 4,608 paired clock
ratios, 3,024 summary medians and 30 endpoint classifications**. All five
comparators remain. Same numerical sampler seeds do not imply identical
recursive forests across rates. Historical timings will not be pooled or used
to normalize gains. The [prospective freeze](freeze.json), SHA-256
`2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f`,
passed [preflight](validation/preflight-attempt01.json) at revision
`0fec3ee75d5065c776a55656a13e1062e13426c3`. The evidence merge did not change
any native source. Serial performance release remains pending until all
separate diagnostics, builds and plots have stopped.
