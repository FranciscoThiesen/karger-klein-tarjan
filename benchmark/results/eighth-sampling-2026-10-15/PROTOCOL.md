# Prospective scalar half versus eighth sampling experiment

Prepared source-only on 2026-10-15 during the separate larger-hierarchy capture.
No partial larger timing was consulted. No import, test, build, installation,
preflight or native execution is claimed. Root owns all later releases; a
decision not to run preserves this declaration as unexecuted. Any different
matrix or rate requires a new prospective declaration.

The question is whether accepting one eighth instead of one half of private
sampling candidates reduces total KKT cost with compressed verifier queries
fixed. These known contrasting families test an implementation change, not
generalization to previously unseen graph shapes. Every loss and all five
comparators remain in the campaign.

## Fresh controlled pair

Use a future isolated checkout based on the complete compressed-query parent
proof at
`/Users/random_person/Desktop/kkt-compressed-queries/benchmark/results/compressed-query-2026-10-15/freeze.json`,
SHA-256 `bd65da13058d3e9cfa58919a0fe5e02b8a46b1d0b8fe7f05801692d5a0866df9`.
The parent binary is an artifact ancestor, not the timed baseline. Produce
fresh same-source `half` and `eighth` binaries.

The only changed existing native source is `kkt/kkt.cpp`; add the declared
pure-predicate header and two direct/private-integration test sources. Both
variants contain that predicate refactor. Only the eighth KKT compile enables
`KKT_EXPERIMENT_EIGHTH_SAMPLING`. Its private predicate accepts a word exactly
when all three low bits are one, instead of requiring only the low bit.
Both policies keep one RNG draw per edge, stable edge order and metadata,
`H.reserve(m/2)`, all work counters and the public legacy odd-word API.
No packed words, bit scanning, rate-by-family threshold, reserve adjustment,
contraction change or other optimization belongs in this comparison.

Compile seven non-KKT objects once, including one compressed verifier, and
link those same physical object paths and hashes into both variants. Share
the six-solver harness main object too. The exact twelve-command timing recipe
contains seven shared compiles, two KKT compiles, one main compile and two links.
The shared verifier compile alone adds `KKT_EXPERIMENT_COMPRESSED_QUERIES`;
the eighth KKT compile alone adds `KKT_EXPERIMENT_EIGHTH_SAMPLING`. Neither link
adds those two opt-ins. Retained-edge/direct-Edge flags remain in the common
base argv. Preserve C++17/O3, native arm64 AppleClang, assertions, compiler/SDK
identity, the 512 MiB stack and every certificate/timing boundary.

Bind the exact source overlay, recipes, compiler commands, logs, native
profiles, different KKT objects and binaries, equal seven shared objects and
equal main object. `source_overlay_sha256` identifies prepared source bytes;
it does not itself claim those bytes have passed tests.
Require exact typed policy metadata in both the build record and executable
descriptor: `sampling_policy` is the variant, `private_acceptance_mask` is
integer 1 or 7, and `sampling_words_per_visited_edge` is integer 1. These fields
describe the recipe; the actual source, object and private-oracle gates supply
the selection evidence. Preserve the original
compressed parent source/helper/object/build proof. The collector temporarily
rebinds only immutable parent helper path spelling while running the full
original checker and restores that binding even on failure. Raw commands and
rows use explicit local seeds; no parent seed globals are changed.

Native, sanitizer and final-object correctness gates must pass before timing.
They must retain predicate truth tables, actual private dispatch and opposite-
policy rejection, public stream/state preservation, exact independently
certified MSF IDs, direct tuple/Edge and compressed-query oracles, disconnected
and multigraph fixtures, signed extremes and input orders. Fresh half must
logically replay the parent half records, including all 65 counters, on the
same correctness fixtures. Across half/eighth require the same input and MSF,
equal dimensions immediately after the first two contractions, and a positive
private-work difference; cumulative recursion counters may differ. Replaying
half records as eighth must fail. Both policies run the native and sanitizer
MSF, direct-mark and focused sampling checks with the compressed verifier fixed;
no uncompressed timing or correctness variant is introduced. Check the actual
uninstrumented final object sets with the certificate harness. Recompile each
KKT object with its exact timing flags and require byte identity, then run the
separate same-flags private/public integration oracle and wrong-policy negative.
That oracle is not described as executing inside an already linked timing
binary. The exact completed gate receipts must be
reviewed before freeze; no test is assumed passed by this source declaration.

## Fixed inputs and schedule

The exact six-row [manifest](manifest.csv) is mandatory:

| Family | n | m/n | Intrusion |
|---|---|---:|---:|
| `leaf_hierarchy4` | 65,536; 1,048,576 | 32 | 0 |
| `leaf_shuffled4` | 65,536; 1,048,576 | 32 | 0 |
| `gnm_random` | 4,096; 1,048,576 | 16 | 0 |

Graph seeds are **15000011, 15000031**; sampling seeds are **2609, 2617**.
The source-only proposal search found no earlier declared use in its inspected
configuration files. Recheck declarations before freeze if other studies
intervene; this is not a global audit of external invocations. No measured
output may determine seed substitution or which cases are retained.

Loop over graph, sampler, case, then adjacent variants. Base case order is
hierarchy small, shuffled small, hierarchy large, shuffled large, G(n,m) small,
G(n,m) large. Graph two reverses the full case list. Run half first when the
zero-based graph-index plus sampler-index is even, eighth first otherwise.
Every variant runs first twice per case. Each child runs KKT, deduplicating
compacting Borůvka, retained-edge Borůvka, Kruskal, Prim and original Borůvka.
One checked warmup and six timed repetitions put each solver in every timed
position once.

There are **48 children / 2,016 certified outputs: 1,728 timed and 288 warmups**.
Six repeats reuse one graph and initial sampling state. Four graph/sampler
realizations share two graphs; they are not 24 independent graphs or forests.
Counterbalancing does not remove graph/sampler/order/thermal-history confounding.
Keep wall and process CPU clocks separately and retain every observation.

Require identical graph fingerprints across variants and sampling seeds. The
attachment twins share topology, IDs, labels, physical edge order and cheap
leaves; only core ranks change. Require equal topology and different weighted
fingerprints at all four size/graph twin pairs. This is a core-rank control,
not globally random weights. The attachment family is engineered, and G(n,m)
uses the existing connected simple graph construction without weakening it.

Equal numerical sampling seeds do not make the private recursive streams or
forests identical. With the same entry engine state and edge sequence, the
eighth-accepted positions form a subset of half-accepted positions, and both
consume the same number of words for that one sampling call. Once recursive
inputs diverge, this is not a global nesting or equal-state claim. Bernoulli
inclusion and the fixed-p sampling lemma use an ideal independent-word model;
finite `mt19937` streams do not prove that model for every seed.

## Capture and failure policy

Require a committed prospective freeze and a separate quiet performance
release; `capture` also requires `--released`. No build, test, plot or diagnostic
capture may compete with timing. Preserve the 40 GiB sampled owned-group RSS
ceiling, roughly two-second polling, bounded provider calls, three unavailable
observations stop, immediate provider-poison stop and bounded termination.
Verify a final empty owned group after wrapper exit before advancing; unknown
exit forbids another child. Sampling may miss transient memory peaks.

Mark exit unknown before cleanup, ignore repeated SIGTERM only during its
bounded operation and restore the prior handler afterward. Clear unknown only
from affirmative native-exit and empty-group proof; preserve any earlier
unknown state. Record cleanup exceptions. Frozen parent helpers are unchanged.

Keep exact argv, `/usr/bin/time -l`, raw CSVs, independent certificates, RSS
evidence, UTC/monotonic intervals, exit statuses and every clock flag. Preserve
first failures and partial captures. No overwrite, trimming, normalization,
ceiling increase, solver omission, case replacement or favorable early stop.
Strict reload rechecks the entire frozen proof, schedule, raw rows, resource
and empty-group evidence, and exact child-to-combined CSV concatenation.
Incomplete or failed captures cannot become successful summaries.

Archive power-query status separately; optional private-log correlation is
diagnostic, not proof of sleep inhibition, complete coverage or thermal
stability. Add private raw-log ignore rules before capture. No raw private
power events belong in published artifacts.

## Complete statistics and interpretation

Pair exact case, graph, sampler, repetition and clock. Report eighth/half for
all six solvers, preserving unchanged-control drift without using it to
normalize KKT. Report KKT against all five controls within each variant and
all absolute times. Keep every integer pair endpoint, loss and full range.

| Tables | Pooled | Realization | Graph marginal | Sampler marginal |
|---|---:|---:|---:|---:|
| Direct KKT comparisons | 120 | 480 | 240 | 240 |
| Absolute solver times | 144 | 576 | 288 | 288 |
| Eighth/half solver comparisons | 72 | 288 | 144 | 144 |

These are **3,024 summary medians**, plus **2,880 direct** and **1,728
cross-variant** paired clock ratios. Pooled medians use all 24 paired ratios,
not medians of four medians or ratios of absolute medians. Realizations use
six trials; graph and sampler marginals use twelve. Ranges are descriptive,
not confidence intervals or population probabilities.

For each variant/family/control, reconstruct the four realization medians on
each clock from exact integer-endpoint Fractions. The median of six is the
mean of the middle pair. An endpoint is a strong lead if all eight medians
are at most 9/10, narrow if all are below one without being strong, loss if
all are strictly above one, otherwise mixed/tied. Keep all **30** two-endpoint
classifications. A strong observed bracket needs a small-endpoint loss and
large-endpoint strong lead. Two points cannot establish persistence beyond
the larger size, an interpolated threshold, literal linear runtime or
asymptotic dominance. One comparator win is not an all-six win.

The fixed-p expected-work argument permits testing this change under its
assumptions; it supplies no speed forecast. Fewer accepted records leave the
parent scan and one RNG draw per edge intact. A smaller sample can make the
subsequent light-edge filtering weaker and increase other recursive work.
Historical packed or query-compression gains cannot be multiplied into an
expected eighth-sampling result. Elapsed time alone does not identify CPU,
allocation or cache causality.

An independent audit must recompute all estimates and classifications from
raw rows without collector aggregation. Any later work-counter study requires
a separate release and exact input fingerprint joins. For these unchanged
scalar loops, RNG words equal `sampling_edge_visits`; existing cumulative
counters do not expose per-call distributions or vector reallocations. No
result or promotion decision is assumed by this declaration.
