# Prospective compressed-query verifier comparison

Prospective protocol, 2026-10-15. The implementation is installed and the native, sanitizer, final-object and mocked collector gates have passed; see [validation](validation/NATIVE_VALIDATION.md). Performance binaries have not run. Freezing this protocol and an explicit scheduling release remain prerequisites for performance capture. The completed packed-sampling study is separate.

The isolated worktree is `/Users/random_person/Desktop/kkt-compressed-queries`, based on Edge revision `30728a3dedb9f6fc9b52289053e05d78a47ceffd`. Both variants retain the same scalar recursive sampler, retained-parallel contraction, and direct-Edge verifier queries. The candidate compresses repeated endpoint-to-ancestor requests in the verifier; the reference keeps the existing query-record/maxima representation. No reserve change or unrelated lifetime change is included.

## Builds and prerequisite gates

The parent is the original frozen Edge experiment at `/Users/random_person/Desktop/kkt-edge-verifier-view/benchmark/results/edge-view-2026-10-15/freeze.json`, SHA-256 `f976a7d61650f5aaf8e7221c7684461e36bcb51492347f45a56497b6b1cee306`. Its complete strict source/build/helper checker must succeed before temporarily scoped seed overrides. Parent helper copies must have identical names and hashes; temporary bindings restore on every exit.

Use `benchmark/build_compressed_queries.py`; its archived preparation notes and executed validation receipts are in `validation/`. Variants are `reference` and `compressed`; only `verifier/verifier_v2.o` differs. Seven production objects, including `kkt.o`, and the six-solver driver object are physically shared and hash-equal. Only the candidate verifier compile adds `-DKKT_EXPERIMENT_COMPRESSED_QUERIES`. Both otherwise use the same parent native ARM compiler/SDK, `-O3 -march=native`, C++17, assertions, retained-parallel/direct-Edge flags, and 512 MiB main-stack setting. Work-statistics flags are absent from performance objects. No packed-sampling macro is permitted.

The timing collector reconstructs all 12 compile/link commands in order and verifies exact recipe/source/object/binary hashes, variant paths, native profile, shared objects, and distinct verifier objects/binaries. Allowed production source differences from the parent are only `verifier/verifier_v2.cpp`, plus the new experimental verifier header and focused test. The default verifier body remains textually unchanged; fresh reference timings are still required.

Before any freeze or native release, source review, mocked collector tests, native direct-mark/linked-dispatch/full-MST correctness gates, ASan+UBSan, and final-timing-object correctness gates must pass. Same inputs and fixed RNG policy must produce the same certified MST IDs; the 61 invariant counters and four exact changed-counter identities are specified in [the source proof](validation/SOURCE_PREPARATION.md) and checked in [native validation](validation/NATIVE_VALIDATION.md). No intermediate sample/forest trace is claimed unless separately collected. No historical timing result is substituted for the fresh reference.

## Fixed matrix and order

Use the six cases in `manifest.csv`, with graph seeds **8000009** and **8000023**, and the single fixed sampling seed **1801**. There are two variants per input: **24 native children**. Each child executes all six solvers once as warmup and six times as timed calls: **1,008 certified outputs**, comprising **864 timed calls** and **144 warmups**. Solvers are KKT, compacting Boruvka, retained-edge multigraph Boruvka, Kruskal, Prim, and original Boruvka.

Graph seed one uses manifest order and adjacent `reference,compressed` children. Graph seed two reverses the complete case order and uses adjacent `compressed,reference` children. Six timed repetitions rotate solver order so every solver occupies every position once within each child. The largest graph has 33,554,432 edges. No case, seed, trial, or loss is removed after observing a result.

Graph seed is confounded with the case-order and variant-order reversal. This counterbalancing reduces a simple fixed-order bias but does not separate seed effects from host/order drift or prove that such drift is absent.

Hierarchy and shuffled weights are topology/order twins for each size and graph seed. Their topology fingerprints must match and weighted fingerprints must differ; all four matched pairs must be present. Every paired variant and solver receives exactly the same weighted input fingerprint. The existing driver independently certifies its reference tree and checks every output exactly; a fingerprint is an input-identity check, not a substitute for MST correctness.

## Measurement, resources, and preservation

Reuse the unchanged six-solver harness and its original timed boundaries, result representations, clock diagnostics, exact output checks, resource monitor, and cleanup semantics. Preserve raw wall/steady and process CPU times and UTC envelopes. Report all flagged calls without trimming, correction, or normalization using unchanged-solver drift.

Freeze native sources, compiler/link commands, objects, binaries, parent chain, manifest, protocol, and collector/helper hashes before native capture. Capture requires explicit `--released` scheduling. No builds, tests, counters, plots, profiling, or competing performance runs may overlap it. User-authorized sleep inhibition is managed by the root; a power-log correlation is not itself proof of uninterrupted wakefulness.

Use the inherited bounded owned-group RSS monitor: 40 GiB sampled RSS ceiling, two-second polling, stop after three consecutive unavailable observations or sampler poison, bounded termination, and a retained successful empty-group observation after wrapper exit. Preserve failures and partial child outputs; do not overwrite or substitute inputs. Strict reanalysis must verify every hash, complete schedule, raw row/certificate, clock diagnostic, resource observation, process-group exit, and exact combined-CSV concatenation before aggregation.

## Comparisons and crossover definition

For each case, clock, and algorithm, pair candidate/reference times by graph seed and repetition. For each variant, also pair KKT directly with **all five** other solvers. A case median uses all **12** paired trial ratios; each graph-realization median uses its six trials. Preserve individual trials and ranges, both graph medians, both clocks, and absolute solver times. The single sampling-seed marginal is identical to the pooled case result and is not another independent observation.

Report all six candidate/reference algorithm comparisons so drift in unchanged controls remains visible. Those controls are diagnostics, not normalization factors. Trials on one graph are repeated measurements, not independent graph samples. One fixed sampler seed does not establish robustness across sampled forests; promising outcomes require separate confirmation on fresh sampling and graph seeds.

A **strong crossover bracket** for a family/density and comparator requires, for each of the two graph seeds on **both clocks**, KKT/comparator median **greater than 1** at the smaller endpoint and **at most 0.90** at the larger endpoint. This produces four required medians per endpoint. A lead already present at the smaller size is not an observed crossover. A bracket between two measured sizes is not proof of monotonicity, an exact crossing location, asymptotic dominance, or an all-solver win.

The fixed analysis exports 864 candidate/reference all-solver ratios and 1,440 within-variant KKT/comparator ratios, along with all aggregate and realization tables. All five comparators and both variants remain in crossover classifications. An isolated speedup in the verifier experiment does not establish that KKT beats retained-edge Boruvka; the direct comparison is required.

There is no promised improvement, automatic promotion, or next timing run. Only the root can release a later experiment after the outstanding gates are reviewed.
