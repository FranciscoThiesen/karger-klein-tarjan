# What the complete lower-density work capture shows

The ordered distance weights make retained-edge Borůvka revisit much more edge
volume as the graphs grow. KKT's cumulative contraction volume grows much less
per original edge, but it also pays for sampling, verification and temporary
representations. Shuffling the same core weights shortens Borůvka's continuation
substantially. These measured differences help explain why the weight ordering
matters; they are not a conversion of logical counters into CPU time.

The density-8 reversal has an additional, concrete complication. Its two 4M
graphs have almost identical contraction and sampling counts, but the graph
that loses on timing performs **67,347,598 more cumulative edge visits in the
verifier's disconnected-forest partition path**. The exact source/accounting
identity below establishes this counter difference. Additional integer bounds
prove that this graph's root forest is disconnected, whereas the other root is
connected. Neither result assigns a fraction of elapsed time to that path.

## Complete input and correctness coverage

This is the separately declared, untimed companion to the [completed timing
study](../README.md). It includes **all 30 cases and both graph seeds**, without
selecting winners: distance-ranked and shuffled weights, density 16 at seven
sizes from 512 through 2,097,152, and density 8 at eight sizes from 256 through
4,194,304. Every input uses graph seed 23000003 or 23000029 and sampler seed
3407. All 30 topology twins retain identical endpoints, labels, IDs and physical
order with different weighted fingerprints. Every fingerprint matches the
completed timing capture.

The existing instrumented eighth artifact was reused without rebuilding or
changing its eight production objects. The [prospective protocol](PROTOCOL.md)
retains its original preparation status as historical evidence; the
[freeze](freeze.json) precedes the diagnostic capture. KKT, deduplicating
Borůvka and retained-edge Borůvka each passed independent exact-MST certification
on all 60 inputs. Both comparator continuations were also replayed outside the
counter scope. The [standalone raw audit](independent-counter-audit-attempt01/audit.json)
reconstructed:

- 180 solver rows and all **11,700 cells across 65 fields**;
- 120 full continuation chains, containing **1,236 round rows**;
- 60 cumulative query/engine-word rows and all 30 topology twins;
- 11,700 exact count/original-m normalizations, including **120 null**
  unmeasured comparator hash-insertion cells.

The native outer controller exited 0 after 615.367 seconds and proved all 60
native groups and its own group empty. That duration is a resource/scheduling
observation, not a solver benchmark. Strict reload, canonical analysis and the
independent audit also exited 0. See the [capture receipt](capture-controller-attempt01.json),
[strict verification](../validation/work-verify-attempt01.json),
[analysis](analysis-attempt01/provenance.json) and
[audit execution](../validation/work-counter-audit-attempt01.json).

## Contraction volume explains an important structural difference

`contraction_edges` sums the input edge-record count over contraction calls.
It is different from `contraction_edge_visits`, which counts the explicit
passes inside those calls. KKT totals include both recursive branches; the
comparator totals cover their complete iterative continuations.

The following largest-size table is a compact summary, with ranges over the
two graphs. Each volume is divided by original m. The two Borůvka controls have
the same number of rounds for each input, although deduplication changes their
edge volumes and the work inside a round.

| Weights / density / largest n | B rounds | KKT contraction input/m | Dedup B input/m | Retained B input/m | KKT MT words/m | KKT cumulative U/Q |
|---|---:|---:|---:|---:|---:|---:|
| Distance / 16 / 2,097,152 | 20 | 2.4031–2.4037 | 7.4542–7.4544 | 17.9059–17.9066 | 1.1565–1.1568 | 3.5913–3.5941% |
| Shuffled / 16 / 2,097,152 | 8–9 | 2.2889–2.2895 | 3.9707–3.9748 | 7.3141–7.9232 | 1.1031–1.1035 | 0.9110–0.9203% |
| Distance / 8 / 4,194,304 | 21 | 2.5231–2.5233 | 7.9752–7.9754 | 17.6875–17.6876 | 1.1733–1.1734 | 6.6664–6.7194% |
| Shuffled / 8 / 4,194,304 | 9 | 2.2937–2.2943 | 4.1379–4.1422 | 7.5173–7.5700 | 1.0660–1.0662 | 1.9932–2.0151% |

The entire size progression remains below. Numbers are cumulative input
records/m, rounded to three decimals; a single value means the two rounded
endpoints coincide, not that the raw counts necessarily match. The B round
range applies to both controls. Exact two-graph values and every counter are
linked after the table.

| Density / weights | n | KKT input/m | Dedup B input/m | Retained B input/m | B rounds |
|---|---:|---:|---:|---:|---:|
| 16 / distance | 512 | 2.320–2.354 | 2.279 | 6.769–6.770 | 8 |
| 16 / distance | 2,048 | 2.370–2.371 | 2.937–2.938 | 8.568–8.574 | 10 |
| 16 / distance | 8,192 | 2.387 | 3.764–3.765 | 10.418–10.421 | 12 |
| 16 / distance | 32,768 | 2.395 | 4.658–4.661 | 12.279–12.286 | 14 |
| 16 / distance | 131,072 | 2.398–2.400 | 5.582–5.584 | 14.156–14.158 | 16 |
| 16 / distance | 524,288 | 2.402 | 6.517–6.518 | 16.031 | 18 |
| 16 / distance | 2,097,152 | 2.403–2.404 | 7.454 | 17.906–17.907 | 20 |
| 16 / shuffled | 512 | 2.212–2.225 | 2.009–2.012 | 3.590–4.114 | 4–5 |
| 16 / shuffled | 2,048 | 2.266–2.267 | 2.204–2.212 | 4.466–4.563 | 5 |
| 16 / shuffled | 8,192 | 2.271–2.279 | 2.522–2.557 | 4.993–5.408 | 6 |
| 16 / shuffled | 32,768 | 2.279–2.281 | 2.887–2.891 | 5.532–5.935 | 6–7 |
| 16 / shuffled | 131,072 | 2.285–2.287 | 3.241–3.246 | 6.401–6.696 | 7–8 |
| 16 / shuffled | 524,288 | 2.288 | 3.625–3.632 | 7.078–7.190 | 8 |
| 16 / shuffled | 2,097,152 | 2.289 | 3.971–3.975 | 7.314–7.923 | 8–9 |
| 8 / distance | 256 | 2.365–2.445 | 2.224 | 5.610–5.611 | 7 |
| 8 / distance | 1,024 | 2.476–2.487 | 2.855–2.859 | 7.244–7.246 | 9 |
| 8 / distance | 4,096 | 2.475–2.495 | 3.640–3.642 | 8.955–8.957 | 11 |
| 8 / distance | 16,384 | 2.500–2.504 | 4.484–4.486 | 10.687–10.691 | 13 |
| 8 / distance | 65,536 | 2.512–2.515 | 5.350–5.352 | 12.437–12.439 | 15 |
| 8 / distance | 262,144 | 2.519–2.521 | 6.224 | 14.187–14.188 | 17 |
| 8 / distance | 1,048,576 | 2.522–2.523 | 7.100 | 15.937–15.938 | 19 |
| 8 / distance | 4,194,304 | 2.523 | 7.975 | 17.687–17.688 | 21 |
| 8 / shuffled | 256 | 2.169–2.191 | 1.952–1.970 | 3.279–3.464 | 4 |
| 8 / shuffled | 1,024 | 2.209–2.271 | 2.133–2.161 | 3.825–4.190 | 5 |
| 8 / shuffled | 4,096 | 2.243–2.262 | 2.419–2.459 | 4.682–4.869 | 6 |
| 8 / shuffled | 16,384 | 2.278–2.280 | 2.816–2.835 | 5.120–5.220 | 6 |
| 8 / shuffled | 65,536 | 2.286–2.289 | 3.144–3.145 | 5.838–5.961 | 7 |
| 8 / shuffled | 262,144 | 2.293 | 3.482–3.494 | 6.506–6.757 | 8 |
| 8 / shuffled | 1,048,576 | 2.293 | 3.804–3.813 | 6.243–7.399 | 7–9 |
| 8 / shuffled | 4,194,304 | 2.294 | 4.138–4.142 | 7.517–7.570 | 9 |

Every KKT first-two-contraction result equals the corresponding retained replay.
All 30 ordered inputs also satisfy the source-derived dimensions n/8 vertices
and (d−7/8)n edge records exactly. Thus many edges remain after the cheap stars
and sibling pairs have contracted. The dyadic rank ordering continues forcing
small sibling merges. At ordered d16, retained input volume rises from about
6.77m to 17.91m while KKT contraction input remains 2.32m–2.40m. At d8 the
corresponding ranges are 5.61m–17.69m and 2.37m–2.52m. These are observed
finite-domain counts, not a fitted asymptotic proof.

The shuffled twins provide a useful limit: KKT has lower contraction volume
there too, yet loses every retained-B timing comparison. A contraction-only
advantage is insufficient to predict the full algorithm's winner. Dedup B
also starts with slightly less contraction input than KKT on the smallest
ordered graphs. Neither loss is omitted.

## Sampling, filtering and query sharing remain real costs

Here are the eight predeclared KKT counters at the largest points, all divided
by original m and retaining both graph extremes. Complete curves for all three
solvers are in the [six-figure gallery](figures-attempt01/README.md); the
[720 selected case/solver/field ranges](report-data-attempt01/selected_counter_ranges.csv)
include every size and the comparator zeros.

| Counter / m | Distance d16, 2M | Shuffled d16, 2M | Distance d8, 4M | Shuffled d8, 4M |
|---|---:|---:|---:|---:|
| Sampled edge records | 0.1446 | 0.1379–0.1380 | 0.1467 | 0.1333 |
| Filtered edge records retained | 0.0878–0.0881 | 0.0335–0.0337 | 0.1761–0.1762 | 0.0673–0.0675 |
| Contraction edge visits | 7.2092–7.2111 | 6.8661–6.8680 | 7.5691–7.5698 | 6.8805–6.8825 |
| Sampling visits / MT words | 1.1565–1.1568 | 1.1031–1.1035 | 1.1733–1.1734 | 1.0660–1.0662 |
| Verifier edge visits | 2.5115–2.5129 | 2.2169–2.2177 | 2.7463–4.7531 | 2.1532–2.2643 |
| Path-query visits | 4.7079–4.7092 | 4.4328–4.4343 | 4.8477–4.8496 | 4.3063–4.3077 |
| Initialized slots | 3.0840–3.0854 | 2.5590–2.5599 | 3.8724–4.9231 | 2.8418–2.8992 |
| Edge materializations | 3.6845–3.6859 | 3.4069–3.4079 | 3.9477–4.9509 | 3.3894–3.4456 |

These totals cover the complete recursive solve, not just its root. For all
60 inputs, scalar engine words equal sampling edge visits exactly; nominal
acceptance probability 1/8 does not mean only m/8 engine calls. `filtered_edges`
counts survivors, not removals. At the four largest endpoints, cumulative
survivors/verifier input range respectively over 7.5903–7.6130%,
3.0405–3.0561%, 15.0082–15.0162% and 6.3156–6.3345%. Those are ratios of
cumulative volumes, not root retention rates or averages of per-call ratios.

Q is cumulative connected-tree verifier requests; U is the sum of unique
requests within each such tree call. The compressed implementation gives the
exact identity U = path_query_visits − 2Q. All 60 Q values are positive here;
the schema retains undefined ratios rather than replacing them with zero.
The endpoint U/Q values in the first table show substantial within-call
sharing, but their increase with size is retained. This study has no half-rate
or uncompressed control, so it cannot estimate a new implementation gain.

## Why the two density-8 largest graphs have different verifier counts

The [audited source](../../../../verifier/verifier_v2.cpp) separates a connected
forest fast path from a disconnected-forest path that builds components,
remaps the forest and queries, verifies each nonempty component and scatters
the marks back. Let M be the cumulative connected-tree query-edge count, T the
number of tree-verifier/FBT calls, and Bsum the sum of their FBT vertex counts.
Each FBT has one fewer edge than vertices. On this compiled compressed path,

`partition_visits = verifier_edge_visits − 2M − 2(Bsum − T)`.

The first subtracted term is the two query scans; the second is the two
FBT-edge scans. The remainder is exactly the sum of **2F + G + Gin** over
nonempty disconnected-forest invocations: two forest scans, one whole-graph
partition scan, and one within-component mark-scatter scan. Empty cases add no
edge visits. The direct-Edge KKT path does not call the public ID-set conversion
that would add another scan. The [small derivation script](analyze_verifier_partition.py)
binds source and audited table hashes and exports [all 60 residuals](partition-analysis-attempt01/partition.csv);
all are nonnegative. Its [receipt](../validation/work-partition-analysis-attempt01.json)
records a successful nonnative execution and empty owned group.

For distance d8 at n=4,194,304:

| Quantity | Graph 23000003 | Graph 23000029 |
|---|---:|---:|
| Retained-B wall timing ratio, graph median | 0.941385 | 1.015940 |
| Total verifier edge visits | 92,150,891 | 159,486,729 |
| Connected-tree query + FBT scan base | 80,671,898 | 80,660,138 |
| Disconnected-forest partition visits | 11,478,993 | 78,826,591 |
| Partition visits / original m | 0.342101 | 2.349215 |
| Initialized slots | 129,935,052 | 165,192,550 |
| Edge materializations | 132,463,781 | 166,124,250 |

The partition difference is +67,347,598, while the base differs by −11,760;
together they give the exact +67,335,838 verifier-visit difference. This
establishes additional cumulative work in that source branch, rather than
merely noticing a timing fluctuation. The branch also copies component-local
records and initializes arrays, consistent with the other larger counters.
The root paths can be inferred more precisely using bounds, without a new
native trace. Both roots have r=29,884,416 edges. For graph 23000003, the whole
partition count 11,478,993 is smaller than r, excluding a nonempty disconnected
root, which alone would contribute at least r. Its whole-solve survivor count
5,912,160 is also smaller than r, excluding an empty root forest, which would
leave all r root edges unmarked. The root therefore uses the connected path.

For graph 23000029, suppose the root were not partitioned. The sum of graph
volumes in all partitioned calls would be at most
39,368,676−29,884,416=9,484,260; their within-component volumes cannot exceed
that sum. Their forest volumes are at most the cumulative forest total
738,777. This bounds partition visits by
2×9,484,260+2×738,777=20,446,074, contradicted by 78,826,591. Its root must
therefore use the nonempty disconnected path.

The [separate bound derivation](infer_root_partition.py) applies these tests to
[all 60 inputs](root-inference-attempt01/root_inference.csv), with source and
table [bindings](root-inference-attempt01/provenance.json). They force 59
connected roots and exactly this one nonempty disconnected root, with no
undetermined cases. This establishes connectivity and branch selection, not
the number of isolated vertices, the identity of every deeper partition call,
or a CPU-time fraction. Both density-8 graph counts and timing can also change
with other size/host effects. The measured mixed endpoint and failed sustained
timing crossover remain unchanged.

## All fields, undefined values and reproducibility

The [raw 180-row counter table](analysis-attempt01/work.csv),
[1,236 replay rounds](analysis-attempt01/rounds.csv),
[120 chain totals](analysis-attempt01/round_chains.csv),
[60 query rows](analysis-attempt01/query_work.csv) and
[11,700 exact normalizations](analysis-attempt01/normalized_work.csv) are the
canonical results. The extra [report derivation](summarize_report.py) rereads
all raw counters against the audited table and produces
[5,850 complete two-graph field ranges](report-data-attempt01/all_counter_ranges.csv)
and [all 30 continuation summaries](report-data-attempt01/continuation_summary.csv).
Its [provenance](report-data-attempt01/provenance.json) pins the inputs and
outputs; its [guard](../validation/work-report-summary-attempt01.json) passed.

For completeness, [7,800 KKT/control field comparisons](report-data-attempt01/counter_comparisons.csv)
retain 475 lower counts, 6,897 higher, 308 equal and 120 unmeasured. Their ratios
contain 1,320 defined values, 308 both-zero cases, 6,052 zero-denominator cases
and 120 unmeasured cases. These totals are **not an algorithm score**: many
KKT-only operations have zero comparator counts, fields describe different
logical events, and some fields measure sizes/depths rather than operations.
All 120 unmeasured hash-insertion counts remain null. No ratio is fabricated
for a zero or unknown denominator.

Input conversion, solver work and temporary input destruction share the
declared scope; graph generation, certification and the independent replays
are outside it. Counters omit implicit vector relocation, allocator bytes,
cache misses, bandwidth and instruction costs. No heterogeneous counter sum
is presented as CPU time. The six figures passed independent original-size
QA, recorded separately in [VISUAL_QA.json](figures-attempt01/VISUAL_QA.json);
their eventual page-scale readability is a distinct publication check.

The study measures the complete fixed matrix with two graph seeds and one
sampler seed, not sampling robustness. It supports a mechanism for the
observed family contrast and identifies a specific verifier work difference;
it does not by itself explain all finite-size timing changes or establish
that KKT beats all five timing competitors.
