# Held-out family work counts: complete diagnostic capture

All 72 fresh inputs passed: six families, six sizes and two graph seeds, with
216 certified solver outputs, 65 counter fields, 144 exact comparator replay
chains and 1,188 replay-round rows. Input fingerprints match the completed
[timing study](../README.md). The full controller exited 0 with every owned
group empty. Strict analysis and the descriptive mechanism tables also passed
in separate archived attempts. The independent numerical audit also passed
after all four focused mock groups: all 14,040 counter cells (including 144
explicitly unmeasured hash-counter cells), 144 chains, 1,188 rounds, 72 query
rows, 432 exact normalizations and 36 matched topology twins agree. Both audit
wrappers exited 0 with their owned groups empty; see the
[independent audit](independent-counter-audit-attempt01/audit.json) and
[execution receipt](counter-audit-actual-attempt01.json).

The counters expose the useful distinction between ordered attachment weights
and their shuffled twin. At 1,048,576 vertices, retained-edge Borůvka takes
19 rounds on `leaf_distance4`, but only 8–9 on the same topology with shuffled
core ranks. Its contraction edge visits fall from 51.49 per original edge to
21.20–22.66. KKT's corresponding counts are much closer: 11.65 versus
10.74–10.99. This supports repeated contraction scans as one reason the
ordered family is more favorable to KKT. It does not by itself establish a
runtime win: the timing study found approximate parity against retained-edge
Borůvka at the largest ordered instance, and a loss on the shuffled twin.

The following ranges cover both graph realizations at 1,048,576 vertices and
33,554,432 original edges. “Visits/m” means cumulative contraction edge visits
divided by the original edge count; these are logical counters, not CPU work
or elapsed time. Deduplicating and retained-edge Borůvka have the same round
counts on these inputs.

| Family | Borůvka rounds | KKT visits/m | Retained visits/m | Deduplicating visits/m |
|---|---:|---:|---:|---:|
| `leaf_distance4` | 19 | 11.65 | 51.49 | 26.62 |
| `leaf_shuffled4` | 8–9 | 10.74–10.99 | 21.20–22.66 | 14.74–14.77 |
| `grid2d_metric` | 11 | 11.25–11.27 | 28.27–28.51 | 17.03–17.04 |
| `grid2d_random` | 8 | 10.68–10.90 | 20.68–21.04 | 13.75–13.76 |
| `line_metric` | 9 | 11.42–11.43 | 24.30–24.31 | 19.50 |
| `line_random` | 8 | 10.71–10.93 | 20.61–20.84 | 13.73–13.77 |

Across the six declared sizes, ordered attachment rounds are exactly
9, 11, 13, 15, 17 and 19 in both graph realizations. The line-metric rounds
instead reach 9 at 65,536 vertices and remain 9 at the next two sizes.
Geometric weight ordering therefore does not reproduce the ordered attachment
family's measured contraction pattern. These finite sequences are not an
asymptotic complexity fit or proof of future crossover.

Filtering is substantial in every family. At the largest size, the cumulative
ratio `filtered_edges/verifier_edges` ranges from 0.195% to 0.600% across all
twelve inputs. This is the fraction **retained** across recursive verifier
calls, not a root-only survival rate. KKT additionally records 1.67–1.90
sampling edge visits and 3.35–3.84 verifier edge visits per original edge.
The scan savings above must therefore be considered alongside these other
operations, allocations and data-access costs; the counters do not assign
comparable CPU costs to them.

The compressed-query representation yields cumulative `U/Q` of 0.264%–1.265%
at the largest size. Here `Q` is the number of endpoint requests and `U` is
the sum of per-call distinct lower-vertex/ancestor-depth requests, inferred
from the validated identity `U = path_query_visits - 2Q`. It is not global
uniqueness or a per-call distribution. This single-variant diagnostic does
not measure an uncompressed reference or claim a corresponding speedup.

All outcomes remain in the [72 exact per-input summaries](mechanism-attempt01/per_input.csv)
and [36 family/size ranges](mechanism-attempt01/family_size_ranges.csv), including
small cases and non-winning families. Ranges are minima and maxima over two
graphs, not confidence intervals. The full [work table](analysis-attempt01/work.csv),
[round chains](analysis-attempt01/round_chains.csv),
[individual rounds](analysis-attempt01/rounds.csv) and
[query counts](analysis-attempt01/query_work.csv) retain all original fields.
Prim, Kruskal and original Borůvka are not instrumented here. KKT's cumulative
recursive contraction-call count is not directly comparable to a comparator's
single full-chain round count.

## Validation and preserved failures

The new frontend passes all twelve small native inputs: every declared family
at n=1024,d=32 and both graph seeds. All 36 solver outputs, 65 counter fields,
24 replay chains, certificates and completed-timing fingerprints passed.
Only the copied driver's family whitelist changed. Its new main links the
same eight existing compressed instrumented production objects; none was
rebuilt. This is diagnostic validation, not a performance result.

The first new-main link attempt failed because injected library search paths
selected an x86 libunwind for the arm64 target. Its evidence is retained.
Attempt02 clears only `LIBRARY_PATH` and `CPATH` for compile/link, records their
removed values, and uses unchanged compiler, SDK and flags. Both commands and
all twelve gates exited0 with affirmative empty-group proof. See
[FRONTEND_BUILD_VALIDATION.md](FRONTEND_BUILD_VALIDATION.md).

The adapter's six mocked groups passed in 6.878 seconds on attempt02. The
first mock attempt's two failures came from incompatible fake executable
sentinels in the test fixture; its logs and exact test source snapshot remain.
Only those fixture strings/comments changed. The actual collector and native
sources were unchanged by that test repair. Preparation and a fresh-process
strict freeze reload both passed, with actual exit0 and known-empty wrapper
groups. Independent source review is retained separately. A final independent
readiness check also passed in `independent-readiness-attempt01`, including
the full original proof inside and outside adapter scope, all artifact
identities, the fixed schedule and restoration of the inherited checker.

- Freeze SHA-256:
  `cd6e7a349f689879af04b6b458bfd9a6db16ecfdf10e8fd93b134310e8e09663`.
- New binary SHA-256:
  `83819e7b22a47cf5174ae2507cf71c88dbc6f9a9153e2b37a948bddea1608e96`.
- Build record SHA-256:
  `2c93d8504ed4d984d0baa72cff502387f67d4fec9733ff264a650eca43eee365`.
- Bound files: 464. Completed full capture: 72 fresh inputs, 216 solver outputs,
  144 replay chains and 72 cumulative query summaries. Prior outputs reused: 0.

The old [failed attempt](../work/FAILED_ATTEMPT01.md) remains failed. Its first
two successes are not part of this new capture. All six families, six sizes
and both graph seeds remain fixed, without selection by outcome.

The repair/declaration and freeze were committed before capture as
`e3997c0dab4deaa08a0a3172094ae8d265612ec9` and
`1f226729d18b17c0fb2956a2bf9109f9a88860c9`. The executed capture and analysis
entry points were:

```sh
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/run_capture_attempt.py --released
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/collect.py analyze --capture benchmark/results/heldout-families-2026-10-15/work-spatial-v2/capture-attempt01.json --output-dir benchmark/results/heldout-families-2026-10-15/work-spatial-v2/analysis-attempt01
```

The exact analysis invocation and source hashes are archived in
[analysis-controller-attempt01.json](analysis-controller-attempt01.json),
the mechanism-summary invocation in
[mechanism-controller-attempt01.json](mechanism-controller-attempt01.json),
and the actual capture exit/group proof in
[capture-controller-attempt01.json](capture-controller-attempt01.json).
Process durations and sampled RSS are monitoring evidence only; no
per-algorithm timing or peak-memory claim is made.
