# Final recovery and numerical assessment review

Independent review passed. The 12 recovery children complete the missing
numerical evidence; **the original frozen B execution remains failed**.
No benchmark was rerun by this review, and no observation was replaced,
removed or corrected. The independent calculations and input hashes are in
[final-recovery-independent-check.json](final-recovery-independent-check.json).

## Execution and provenance

The [release](../attachment-confirmation-b-recovery-release.json),
[execution record](../attachment-confirmation-b-recovery-execution.json) and
[capture sidecar](../attachment-confirmation-b-recovery-timing.json) agree on
revision `1d3f8c0c1ead58147b409ec4631b2e0911b75cfd`. The recovery adapter,
declaration and two-case manifest match their committed contents at that
revision. The entire captured C++ inventory, native binary, Makefile, build
profile and original six Python helper hashes match the interrupted prefix.
The adapter is explicitly recorded as a seventh helper. The native executable
SHA-256 remains
`8188f6b8717a0a4b4261369ac589ca0a65f2247ebfbfb8c56f98a544bd156faf`.

The tail retains exactly the declared cases in order: hierarchy at 262,144
vertices, then distance at 1,048,576; three graph seeds and two sampling seeds
per case, all five algorithms, five timed repetitions and one warmup.
All 12 children exited zero and all 360 calls passed. There was no cleanup
action or unknown/native-possibly-running state. The execution record's
`capture_pass_pending_independent_analysis` label records its state at native
completion; the subsequent [strict analysis](../attachment-confirmation-b-recovery-analysis/provenance.json)
and [corrected power audit](../attachment-confirmation-b-recovery-power-audit/audit.json)
both pass.

The composite preserves 60 original completed children plus precisely these
12 previously unstarted children. The original combined B CSV still contains
only 59 children; child 60 comes from its retained native CSV and recorded
zero exit status. The [source-parts ledger](../attachment-confirmation-b-composite-analysis/source_parts.csv)
identifies every call's actual source. A plus composite B contains 4,320 calls:
3,600 timed and 720 warmups. A and B are summarized separately; B repeats A's
graphs rather than supplying three additional independent graph realizations.

## Resources, clocks and environment

| Evidence part | Native calls | Clock-flagged calls | Nominal logged-sleep overlaps | Maximum sampled group RSS |
|---|---:|---:|---:|---:|
| A | 2,160 | 0 | 0 | 8.4011 GiB |
| Interrupted B prefix | 1,800 | 149 | 1 | 8.4853 GiB |
| Recovery tail | 360 | 0 | 0 | 4.3521 GiB |

These are sampled process-group RSS sums, not continuous maxima or unique
physical footprints. The parts contain different case sizes, and the tail
uses the declared `libproc` provider instead of `ps`; the table is not evidence
of reduced solver memory use. The tail has 409 observations, zero unavailable
observations, a maximum recorded sampler duration of **4.342125 ms**, and a
maximum request-to-request gap of **2.013101250 s**. Those records support the
bounded monitor's successful operation in this run, not a universal latency
guarantee.

The prefix's final successful RSS observation was at **07:18:39.742166 UTC**.
Its wrapper finalized at **08:29:20.445284 UTC**, 4,240.721 seconds later in that
process's monotonic clock. This large unobserved interval remains a limitation;
the final wrapper interval includes a post-native stall and is not substituted
for any solver duration. The single corrected clamshell interval is 803 seconds
and overlaps the retained Prim call at hierarchy2M, graph seed 1000099, sampling
seed 503, timed repetition 4. A `Wake Requests` scheduling notice is not treated
as a wake transition. The sleep correlation does not explain all 149 flags or
the cause of the broader disturbance.

Recovery wrapper duration is **809.350103 s in UTC** and **809.642784916 s in
its monotonic clock**, a difference of −0.292681916 s. This discrepancy is
retained; it is not used to adjust native call durations. The Python 3.9/macOS
runtime here has process-local monotonic origins, so only within-capture
monotonic ordering is comparable. Cross-part order uses the finalized stop,
explicit release, recorded exits and UTC provenance.

The A/prefix environment snapshots report occupied swap of **459.81M**; the
recovery release reports **5,617.69M**. This documents a changed desktop state,
not a measurement of active paging or an explanation of timing differences.
AC power was recorded. Sleep inhibition was not verified, and the retained
`caffeinate` assertion failure remains applicable. Zero tail clock flags and
power overlaps do not establish a quiet host, fixed frequency or stable core
placement.

## Independent numerical result

I recomputed every paired ratio directly from A's original CSV, all 60 original
B child CSVs, and the recovery CSV using only the standard library. Medians
were taken over repetitions, then sampling seeds, then graph seeds. All **192
case comparisons** agree exactly with the composite assessor. The calculation
does not replace paired ratios with ratios of independent runtime medians.

Both selected families meet the declared **numerical** upper-size rule against
compacting Borůvka: case medians at most 0.90 and every graph median below one
at both 1M and 2M, separately in A and composite B, on both clocks.

| Family | Range of its eight upper-size case ratios | Largest upper-size graph median |
|---|---:|---:|
| `leaf_hierarchy4`, d=16 | 0.814866–0.835517 | 0.837397 |
| `leaf_distance4`, d=16 | 0.812233–0.860366 | 0.932735 |

This is not a successful completion of the original frozen B protocol.
Distance2M in composite B retains two individual wall-time losses to the
compactor (largest ratio 1.433936), despite meeting the median/graph rule.
All four case/clock curves for each selected family show a parity bracket
between 65,536 and 262,144 vertices; these are brackets between measured points,
not fitted transition locations or promises about every intervening size.
The 10% threshold and parity onset remain separate, and the curves need not be
monotone.

Every case median still favors each of the three classical comparators over
KKT. Kruskal and original Borůvka also win every individual paired trial on both
clocks. Prim wins every CPU-time pair; composite B retains **two individual
wall-time KKT wins over Prim**, including the 803-second sleep-affected call.
Thus “all classical trials lose” would be incorrect for this final evidence.

Controls are retained: at 2M, shuffled-core KKT/compactor wall medians are
0.983319 in A and 0.992436 in composite B; global-random medians are 1.035935
and 1.035169. The latter is a loss. Matching topology fingerprints corroborate
the intended weight interventions; they are finite fingerprints, not an
independent proof of graph identity. Global-random leaf spokes remain forced
MST edges, although additional core edges may be selected in the first round.

The proper claim is a bounded, descriptive numerical crossover against this
unchanged compactor, with disturbed and interrupted B evidence explicitly
retained. It is not a claim that KKT is the fastest of all five implementations,
that the host was controlled, or that a finite timing experiment proves the
asymptotic work bound.
