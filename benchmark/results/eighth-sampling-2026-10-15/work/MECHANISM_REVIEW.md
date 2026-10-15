# Independent review of the eighth-sampling work mechanism

**PASS, 15 October 2026.** This review independently reread the completed raw
JSON records and compared all five canonical tables without importing the
collector or its aggregation. It checked 9,360 counter cells, including the 96
deliberately unmeasured comparator hash cells; all 1,560 paired KKT fields;
96 replay chains containing 1,000 rounds; and 48 cumulative query/engine-word
records. The original independent audit also passed. No native executable was
rebuilt or launched for this review.

The [review program](review_mechanism.py) passed through the archival guard on
its first attempt: actual exit 0, 0.217910417 seconds, owned group 49329 observed
empty. [Receipt](mechanism-review-controller-attempt01.json) and
[complete source/data bindings](mechanism-review-attempt01/review.json) retain
the evidence. All 639 inherited audit/review input bindings were rehashed before
and after computation. These are nonperformance review durations.

## All six cases and eight preselected fields

Each number below is the median of **four exact Fraction ratios**, eighth/half,
over two graphs crossed with two sampler seeds. They are four realizations
sharing two graphs, not four independent graph draws. Every count is cumulative
over the complete recursive solve. No instrumented duration enters the table.

| Case | Sampled edges | Surviving edges | Contraction edge visits | Engine words / sampling visits | Verifier edge visits | Path-query visits | Initialized slots | Edge materializations |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ordered 65,536 | 0.169907 | 3.883925 | 0.651621 | 0.678542 | 0.695819 | 0.679901 | 0.711599 | 0.659993 |
| Shuffled 65,536 | 0.175073 | 4.037411 | 0.662875 | 0.698928 | 0.699451 | 0.699404 | 0.715018 | 0.668984 |
| Ordered 1,048,576 | 0.159066 | 3.880805 | 0.628064 | 0.636435 | 0.657690 | 0.638194 | 0.673848 | 0.635607 |
| Shuffled 1,048,576 | 0.163409 | 4.016124 | 0.630711 | 0.653600 | 0.654126 | 0.654051 | 0.671227 | 0.633733 |
| G(n,m) 4,096 | 0.214469 | 3.935182 | 0.769751 | 0.847609 | 0.848336 | 0.847963 | 0.867171 | 0.777124 |
| G(n,m) 1,048,576 | 0.167736 | 4.018283 | 0.648022 | 0.670895 | 0.671072 | 0.671772 | 0.700405 | 0.648752 |

All 24 realizations increase `filtered_edges` and decrease each of the other
seven selected fields. The full four-point min/median/max values, with exact
fraction strings, remain in [selected_case_ratios.csv](mechanism-review-attempt01/selected_case_ratios.csv).
For example, the small random case's engine-word ratios range from 0.793589 to
0.984011: its saving is much less consistent in size than the larger cases.

`filtered_edges` means **retained survivors**, not removed edges. On ordered
1M, median cumulative survivors/original-m rise from 0.01133564 to 0.04402311;
median accepted samples/original-m fall from 0.90344252 to 0.14366598. The
corresponding sampling visits/original-m fall from 1.80689625 to 1.14946669.
These are separate marginal medians of cumulative totals; they must not replace
the paired-ratio statistic or be interpreted as root survival probabilities.

## Queries, engine calls and the unchanged starting problem

Source inspection confirms one engine word is consumed for each visited private
sampling edge under both scalar predicates. Thus `sampling_edge_visits` is the
exact engine-call count within these successful KKT solves; it does not include
graph generation or assert independence of MT words. Lower acceptance does not
reduce the words required for one fixed scan. It changes subsequent recursive
inputs, whose total visited sampling volume is measured to fall here.

Q is cumulative `verifier_queries`; U is `path_query_visits − 2Q`. This review
checked 0≤U≤Q and Q=2M, with M=`verifier_tree_edges`, for all 48 solves. U sums
per-call distinct answers, not globally unique pairs across recursion. No solve
has Q=0 in this completed matrix; the retained schema still defines that case.

| Case | Half U/Q range, % | Eighth U/Q range, % | Half engine words, millions | Eighth engine words, millions |
|---|---:|---:|---:|---:|
| Ordered 65,536 | 0.827823–0.851151 | 1.093590–1.264580 | 3.538650–3.542262 | 2.401043–2.404411 |
| Shuffled 65,536 | 0.304051–0.321609 | 0.448592–0.458070 | 3.298575–3.419825 | 2.336435–2.339586 |
| Ordered 1,048,576 | 0.790767–0.895935 | 1.279202–1.494370 | 60.432661–60.851245 | 38.559394–38.596770 |
| Shuffled 1,048,576 | 0.317474–0.387593 | 0.490625–0.583987 | 56.685353–58.657645 | 37.631657–37.642325 |
| G(n,m) 4,096 | 0.380219–0.500480 | 0.464011–0.511349 | 0.068734–0.083215 | 0.065329–0.068642 |
| G(n,m) 1,048,576 | 0.528349–0.540497 | 0.797201–0.802441 | 27.338097–28.005576 | 18.371576–18.380362 |

All individual Q, U and engine totals are preserved in
[query_realizations.csv](mechanism-review-attempt01/query_realizations.csv), with
[case ranges](mechanism-review-attempt01/query_case_summaries.csv). For ordered
1M, Q falls from 120,863,168–121,700,376 to 77,112,998–77,189,302. U ranges from
956,671–1,086,909 under half and 986,431–1,153,494 under eighth. A greater
distinct-request fraction therefore coexists with fewer logical queries and
fewer path-query visits. It does not mean query compression stopped working.

The initial two contraction dimensions match the retained-edge replay for
every child, and match across both rates and sampler seeds for all twelve
case/graph identities. Ordered roots are exactly (8,192 vertices, 2,039,808
edges) at 65,536 and (131,072, 32,636,928) at 1M. Other cases' graph-dependent
dimensions remain in [root_dimensions.csv](mechanism-review-attempt01/root_dimensions.csv).
The same input and deterministic pre-sampling contraction source explain this
invariance; the review observes the dimensions/replay, not every internal edge
array as a separately emitted trace.

For each of those twelve case/graph identities, **both comparator records and
their entire replay chains are exactly unchanged across rate and sampler**.
This includes every counter, the unmeasured-hash status and every round's
dimensions/selection count. Comparator constancy must not be imposed on later
KKT recursion, whose inputs legitimately differ. In particular, the old
compression experiment's 61-equal-plus-four-identities gate is inapplicable
across sampling rates.

## All 65 fields, including increases and zeros

Across 24 paired realizations × 65 fields, **774 decrease, 491 increase and 295
are equal**. The equal fields comprise 236 positive equalities and 59 both-zero
records. There are 1,501 defined ratios and no half-zero/eighth-positive record.
Four defined ratios are zero: `verifier_arc_visits` changes from positive half
work to zero eighth work. Those are genuine zero numerators, not undefined
ratios or discarded points.

The 59 both-zero records are `current_depth` (24), `hash_lookup_calls` (24) and
`verifier_arc_visits` (11). Root vertex/edge dimensions and KKT final hash-insert
counts are positive and equal in every pair. Many vertex, call, depth and
verifier-tree fields rise in some realizations even while the selected edge
volumes fall. [All 65 field totals](mechanism-review-attempt01/all_field_statuses.csv)
and [all 390 case/field summaries](mechanism-review-attempt01/all_case_field_statuses.csv)
retain their statuses and ranges. Comparator hash counts are 96 **nulls**, not
96 zeros. The heterogeneous counters must not be summed or voted into a CPU
speedup claim.

The data support a specific mechanism: less accepted sample volume and smaller
subsequent sampling/verifier edge volumes coexist with more surviving light
edges; net contraction/materialization/explicit-initialization counts decline
in every selected realization. Source structure makes that tradeoff plausible.
They do not isolate cache misses, allocation time, branch prediction, implicit
vector relocation or time spent in individual phases. The separate
uninstrumented timing study establishes the runtime result. Nothing here
establishes an all-six-solver win or a general advantage for every p or graph.

## README and figure review

The completed README's 48 displayed counter cells match these independently
computed exact medians after rounding. Its normalized-m examples, Q/U ranges,
status counts, capture hash and resource observations also agree. No numerical
or scope correction was needed. All 192 plotted realization ratios and 48
plot summaries were independently matched to raw counters, including exact
numerators/denominators and full ranges.

The PNG was inspected at original resolution: all six panels, eight fields,
full realization ranges, consistent log axes, counter increases above one and
the count-versus-time disclaimer are legible; no clipping or blocking overlap
was found. Page-scale report layout remains a separate check. The
[README/figure receipt](mechanism-review-attempt01/readme_figure_review.json)
binds the exact versions inspected.

Key SHA-256 bindings:

| Artifact | SHA-256 |
|---|---|
| Completed capture | `b7160f59fa2b953e9cd0b55f8bccb049512568ed758870bd57b43664806ee172` |
| Review program | `861a9197d85d6b43f57f341b07a6139d4be9ef52020421d779b93c294270fb60` |
| Counter registry | `fc3e8b9e2afba1e12c1e2c47b9c79a7ef4772c3a0185d36ca80f85f25085d9ef` |
| KKT source | `f5681b0384fb26ee6af5a23e4f7109b990393d831fc6ceb5385ce43643f5fd9a` |
| Scalar predicate header | `dc58872c0f6c8542ce67d8c9f3a1c5c5c4fd9f2b1e5ae9c1bb65b5e6c70293bd` |
| Compressed-query header | `3a60df765b5d48add30c3b4429ad501ae7c87de9d8d780151ca5afcb48aa8b60` |
| Reviewed README | `7089041605707ac5a96b62b9e7c34bdfeb5538f527a151819ef0991a35756ab6` |
| Reviewed PNG | `69371d66309f4a7901bc5e3ca819edfc6c0cb411b24ecf66bc1217a683caa103` |

The complete full-length inventories are in the two review JSON receipts.
All review processes have exited. No performance or native-solver execution
was performed by this review.
