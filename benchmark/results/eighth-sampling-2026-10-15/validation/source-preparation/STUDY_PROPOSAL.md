# Prospective scalar half versus eighth study

Status: source-only, unexecuted, 2026-10-15. The larger hierarchy capture is
running separately. This declaration was chosen from source and prior study
designs, without inspecting any partial larger timing. Root owns later worktree
creation, implementation approval, validation, commits, freeze and release.

Preparation scope update, 2026-10-15: root's later direction supersedes the
initial optional compressed/uncompressed 2-by-2 correctness suggestion.
Both policies now use one shared, unchanged compressed verifier throughout;
the existing focused direct-verifier and wrong-policy gates remain required.

## One controlled change

Use fresh same-source `half` and `eighth` binaries. Keep compressed queries,
retained parallel edges and the direct Edge verifier fixed. Change only the
private all-ones acceptance mask from 1 to 7; keep one RNG draw per edge and
`reserve(m/2)`. Both builds include the same pure-predicate refactor. The public
legacy API keeps its odd-word stream, IDs, order and metadata. Do not enable
packed sampling, bit scanning, a new rate threshold, full reservation or any
other optimization. Do not substitute historical half timings for the rebuilt
same-source reference.

## Deferred correctness and artifact gates

1. Check the actual original compressed freeze and its complete source/helper/
   build/binary/object proof. Assert the exact native overlay allowlist. The
   `kkt.cpp` change must be only the include, comment, compile-time selector and
   predicate call shown in `native.patch`; reserve, append and accounting code
   must remain textually unchanged. Pin all new source and recipe bytes.
2. Compile the finite-word predicate test and the actual private integration
   test in both policies. Integration source includes `kkt.cpp` and is linked
   **instead of** `kkt.o`, with the seven shared production objects. Expected
   runtime arguments are `half` or `eighth`; deliberately swap each argument
   and require exit 1 with the private-policy mismatch message, with no
   sanitizer diagnostic. Validate public legacy state and records in both
   policies. An invalid argument is an additional rejected request, not a
   substitute for wrong-policy dispatch evidence.
3. Run the unchanged regression, simple correctness, contraction, attachment,
   certificate, direct tuple/Edge verifier, and compressed-query oracle suites.
   Retain disconnected/isolated/empty cases, loop-free parallel records,
   signed extreme weights/IDs, input order changes, multiple graph seeds and
   sampling seeds. `edge_verifier_view_test` produces the existing 1,344 full
   KKT fixture/order/seed records, with all 65 counter fields, for each policy.
   Match exact input fingerprints and independently certified sorted MSF IDs
   across policies. Validate record schemas and integer types exactly.
4. Fresh `half` must replay every one of the parent's 65 counters, input IDs
   and exact MSF on the same correctness fixtures. This validates the common
   predicate refactor logically; it is not assembly or speed equivalence.
   Across `half` and `eighth`, require equal root-after-two dimensions and
   exact MSF/input identity, plus a positive changed-private-work witness.
   Reject substitution of half records for the candidate. Do not require
   61 or 65 equal cumulative counters across different sampling rates.
5. Keep compressed-verifier dispatch positive and its wrong-reference-policy
   negatives in both builds. Both share the unchanged compressed verifier;
   no extra compressed/uncompressed 2-by-2 experiment is part of this study.
   Preserve direct mark/oracle and malformed-query coverage on the recursive
   forests exercised by each sampler. Existing compression identities are
   not cross-rate gates.
6. Run native AppleClang correctness, then native Clang 22 ASan/UBSan with leak
   detection, using separate objects and the same positive/negative tests.
   Inspect exact exit status and logs. Preserve every rejected attempt and
   investigate it; no source/counter/certificate gate may be weakened to pass.
7. Build fresh uninstrumented timing objects only after correctness passes.
   Compile the seven non-KKT objects once, including one shared compressed
   verifier; physically link those same objects and one shared six-solver
   harness main into both binaries. Compile `kkt.cpp` twice with identical
   flags except `KKT_EXPERIMENT_EIGHTH_SAMPLING` on the candidate only. Native
   C++17/O3, assertions, explicit `/usr/bin/arch -arm64`, compiler/SDK profile,
   512 MiB main stack, raw harness and certificate boundary stay unchanged.
   Keep compression selection on the shared verifier compile. Neither link
   adds an eighth/packed/query-selection macro; retained-edge/direct-Edge
   flags may remain in the shared base argv as in the established recipe.
8. Record and validate exact commands, sources, compiler/SDK, logs, object
   paths/hashes, binary hashes/native profile and parent proof. Require equal
   seven shared object paths/hashes, equal main object, differing KKT objects
   and timing binaries. A default-compiled candidate or wrong object must be
   rejected. Run the existing final-object certificate harness against both
   actual uninstrumented object sets. Rebuild each KKT object with its exact
   frozen flags and require byte identity, then run the separate same-flags
   private/public integration gate with opposite-policy negatives. This joins
   actual final-object correctness with source/recipe/byte proof and a separate
   private-template oracle; it does not pretend the oracle executes inside
   the already linked timing binary.

All build/test children and any later native capture need the unchanged
40 GiB group RSS ceiling, bounded two-second observations, three-unavailable
stop, sampler-poison stop, bounded termination and affirmative known-empty
owned-group evidence before another child. Preserve SIGTERM/finally cleanup,
including the guarded cleanup behavior in new adapters. Do not overlap future
performance with builds, tests, plots, or work counters. Timing-build profiles
must not execute the timing harness. Source-only builder and collector
preparations are now included; there is no installed worktree, freeze, compiled
work driver, binary or run receipt.

## Fixed six cases and fresh seeds

The following matrix is fixed prospectively; do not replace losing cases or
add a more favorable rate after observing it. It is a known-family optimization
screen, not a claim of generalization to previously unexamined shapes.

| Family | Vertex counts | Density parameter | Intrusion |
|---|---|---|---|
| `leaf_hierarchy4` | 65,536; 1,048,576 | 32 | 0 |
| `leaf_shuffled4` | 65,536; 1,048,576 | 32 | 0 |
| `gnm_random` | 4,096; 1,048,576 | 16 | 0 |

Graph seeds: **15,000,011 and 15,000,031**. Sampling seeds: **2,609 and 2,617**.
A source-only search of existing benchmark Python declarations, prospective
protocol text and prepared `/tmp` proposals found no prior declaration of
these four seeds before this proposal. No historical raw data was searched.
That is scoped declaration evidence, not a mathematical proof of global seed
novelty. Recheck source declarations at future freeze if other studies intervene.

Base case order: hierarchy small, shuffled small, hierarchy large, shuffled
large, gnm small, gnm large. Iterate graph seed, sampling seed, then case;
reverse the entire case list for graph seed 2. Each graph/sampler/case has
adjacent `half`/`eighth` child processes. Use half first when the sum of the
zero-based graph and sampling indices is even, eighth first otherwise.
Reverse-order and adjacency controls reduce some drift; fixed family/sampler
block order and thermal history remain possible confounders. Do not normalize
KKT gains using unchanged solvers.

Use all six current solvers, six balanced timed repetitions and one warm-up
per solver: 2 graph seeds × 2 sampling seeds × 6 cases × 2 variants gives
**48 children, 2,016 raw outputs, 1,728 timed outputs and 288 warm-ups**.
Each row retains both wall and process CPU clocks. The six timings within a
realization repeat one graph and initial sampling state; they are not six
independent random graph or sampler observations. There are four graph/sampler
realizations per case. Require identical graph/input fingerprints across
sampling seeds and variants, and equal topology with differing weight
fingerprints for each matched hierarchy/shuffled twin. Shuffling preserves
cheap leaves and changes core rank ordering; it is not globally random weights.

Keep all independent MSF certificates, exact row rotations/counts, clocks,
exits, raw hashes, no-overwrite captures and full original parent proof. Bind
sources, binaries, helpers, build records, manifest and protocol before
performance. Root must separately release capture. No historical timing pool.

## Analysis fixed before any capture

Independently match integer-duration pairs by graph, sampler, case, solver and
repetition. Report `eighth/half` for **all six algorithms** on both clocks
(1,728 cross-variant clock pairs), and KKT versus **all five comparators**
within each variant (2,880 direct clock pairs). Preserve every raw ratio,
absolute duration and loss. Summaries use the median of all 24 paired trial
ratios per case, each of four six-trial realization medians, and graph/sampler
12-trial marginal medians with clear labels and full ranges. Medians of ratios
must not be replaced by ratios of separate medians or median-of-medians.

For each of the three family/density groups, each variant and each comparator
(30 classifications), an exploratory **strong endpoint crossover** requires
all four small-size realization medians to exceed 1 and all four large-size
medians to be at most 9/10, on **both clocks**. Compute predicates using exact
rational ratios/medians from raw integer times. Classify narrow/partial leads,
losses and reversals explicitly. Two endpoints only locate an observed bracket;
they cannot establish durable asymptotic dominance. A later held-out matrix
and intermediate-size study would require a separate fixed declaration.

If root later releases untimed diagnostics, join every declared input by exact
fingerprints and retain all 65 existing counters for both policies. Root
contractions agree before sampling; recursive work can legitimately differ.
For this unchanged scalar loop total RNG words equal `sampling_edge_visits`
exactly. Report sample/filtered volumes, verifier forest/components and work
without inferring a peak-memory or vector-reallocation count. Current counters
are cumulative and do not expose every recursive call or allocator event.

The reviewed fixed-p lemma permits this experiment under its explicit ideal
randomness and linear-work assumptions. It does not predict a useful runtime
gain. Fewer accepted records do not remove the RNG draw or parent scan, and
weaker filtering may outweigh smaller recursive samples. Separate historical
packed or compression gains cannot be multiplied into a predicted eighth gain.
