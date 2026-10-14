<!-- Draft for benchmark/results/search-2026-10-13/README.md.
     Relative links below assume that final destination. Lifted and density results.
     Attachments, diagnostics and confirmation remain explicitly pending.
     Keep the final printed follow-up short; pagination has not been checked. -->

# Searching for a KKT crossover against five MST solvers

The two completed pilots find KKT leads over compacting Borůvka, but **none
of their 53 cases has KKT ahead of all four competitors**. The density pilot
has four case medians at least 10% below the compactor, best ratio **0.8665**
at 262,144 vertices and 16,777,216 edges. It also loses every paired timed
trial to Kruskal and original Borůvka. The lifted pilot's best compactor ratio
is **0.9274** at 1,048,576 vertices and 67,108,864 edges. These are discovery
observations from one graph seed, not completed fresh-seed confirmation.

This is a focused follow-up to the [implementation and complexity report](../../../docs/kkt-report/REPORT.md)
and the [previous large-instance study](../crossover-2026-10-13/README.md).
Those reports contain the repairs, Google Benchmark results, earlier graph
families and detailed work diagnostics. Here the question is narrower: can a
graph family make KKT competitive with **all five implementations measured in
the same campaign**, while also exhibiting a clear size-dependent advantage?
Production solvers are unchanged. The full [protocol](PROTOCOL.md) was frozen
before timing.

| Part of this search | Current evidence status |
|---|---|
| Complete-bundle lifted pilot | Complete: 28 cases, 700 timed calls, 140 checked warmups |
| Existing-family density pilot | Complete: 25 cases, 625 timed calls, 125 checked warmups |
| Single-edge attachment extension | **PENDING**; 80 predeclared cases; no measured claims |
| Large-input work counters and contraction traces | **PENDING**; structural calculations below are not captured traces |
| Fresh-seed confirmation | **PENDING**; no outcome or selected winner asserted |

## What the two pilots actually measured

The [28-case manifest](lifted-pilot.csv) contains four ordered families at
65,536, 262,144 and 1,048,576 vertices with `d=m/n` equal to 16 or 64, plus four
random-weight control cases at the largest size. Each case uses graph seed
5009 and KKT sampling seed 149. Five timed repetitions rotate each algorithm
through all five execution positions; one checked warmup precedes them.
These five repetitions reuse one graph realization. They do not supply five
independent graph samples.

All algorithms receive the same shuffled, relabeled edge tuples with unique
weight ranks. KKT is compared with repeated production `boruvka_step`
(**compacting Borůvka**), and with the existing public Kruskal, Prim and
**original Borůvka** implementations. The two Borůvka implementations are
distinct: original Borůvka repeatedly scans its original edge array, while
the compactor constructs and deduplicates quotient graphs.

Both captures use revision `d4da64ceca0667b7e637b913cc7668b4e467052a`, native
Apple clang C++17 `-O3 -march=native`, assertions enabled, and no work counters.
All five algorithms use the same 512 MiB main-thread stack profile. This
supports original Borůvka's recursive traversal; it changes no solver source.
The [build audit](validation/HARNESS_VALIDATION.md) checks byte identity of
the normal and enlarged-stack executables' instruction sections. Exact
source, helper, Makefile, binary and input hashes are retained in the
[lifted metadata](lifted-timing.json) and [density metadata](density-timing.json).
Their binary SHA-256 is identical. They remain separate captures and tables;
their durations are not pooled. Together they retain 1,325 timed calls and
265 checked warmups.

The original public-call boundaries are preserved. Tuple-to-problem
conversion, temporary-input destruction and output construction are inside
the KKT/compactor steady-clock interval. Returned-result destruction and
validation are outside it. Classical solvers retain their tuple-returning
APIs; no common output conversion is inserted into their timed bodies.
Generation, reference MST computation and its independent cycle certificate
are outside all solver timing. Every timed output and warmup matches that
certified unique MST.

A reported ratio is `KKT time / competitor time`, paired within the same
repetition before taking medians over repetitions, sampling seeds and graph
seeds in that order. Thus 0.9274 means approximately 7.3% less elapsed time,
while 2.4906 means approximately 2.49 times the elapsed time. Ratios of
separately aggregated runtime medians are a different statistic. Process CPU
is a separate enclosing diagnostic interval. Trial ranges describe observed
variation; they are not confidence intervals.

## The complete-bundle models

Each of `q=n/b` core vertices is replaced by a star of `b=2` or `b=4`
vertices. Its `n-q` local star edges receive the cheapest ranks. Each core
edge becomes a complete `b`-by-`b` bundle, with a disjoint interval of unique
ranks above all star edges. The expanded graph has exactly `m=nd` edges.

The core is a path plus distinct randomly proposed shortcuts. In
`lifted_hierarchy{b}`, path ranks increase by dyadic merge level and all
shortcuts are heavier, so the core MST is deliberately prescribed. In
`lifted_distance{b}`, every core edge is ranked by its endpoints' dyadic
separation, then shuffled within that tier. Shortcuts can enter the MST;
these are hierarchical ranks, not Euclidean distances. The independent
fixture suite includes a certified distance example using seven non-backbone
core bundles. The global-random twins permute all expanded weight ranks,
including local stars, while preserving topology, IDs, labels and edge order
at fixed `b,n,d,seed`. All solvers see only the expanded graph, not core
metadata. These are engineered constructions, not application datasets.

The [schematic](lifted-figures/illustrative_lifted_hierarchy.png) illustrates
the construction; it is explicitly an invented small layout, not a measured
fixture or a downsampled large input.

## Size trends: a modest parity crossing, not the target separation

Every entry below is a paired **KKT / compacting-Borůvka wall-time ratio**.
Values below one favor KKT. All ordered family/density combinations are
included; random controls measured at one size appear in the next table.

| Lifted core ordering | Block size b | d=m/n | n=65,536 | n=262,144 | n=1,048,576 |
|---|---:|---:|---:|---:|---:|
| Hierarchy | 2 | 16 | 1.2404 | 1.1000 | 1.0246 |
| Hierarchy | 2 | 64 | 1.0513 | 0.9741 | 0.9274 |
| Hierarchy | 4 | 16 | 1.1671 | 1.0667 | 1.0469 |
| Hierarchy | 4 | 64 | 1.0250 | 1.0155 | 1.0048 |
| Dyadic distance | 2 | 16 | 1.2238 | 1.0786 | 1.0319 |
| Dyadic distance | 2 | 64 | 1.0625 | 0.9817 | 0.9293 |
| Dyadic distance | 4 | 16 | 1.2256 | 1.0915 | 1.0554 |
| Dyadic distance | 4 | 64 | 1.0273 | 1.0002 | 1.0025 |

For the two `b=2,d=64` groups, this screen brackets an **observed parity
crossing between 65,536 and 262,144 vertices**. It does not locate an exact
crossover size or show that every larger input wins. At the largest hierarchy
case, all five paired ratios favor KKT, ranging from 0.9121 to 0.9356;
their median is 0.927429. The corresponding CPU median is 0.927437.
The largest distance case has wall median 0.929345 and CPU median 0.929344.
Neither reaches 0.90, and the screen contains only one graph seed.

Increasing the block size to four does not improve the compactor comparison
here. Its largest dense cases remain near parity on the losing side. The
observed curves also need not be monotone: `distance4,d=64` changes from
1.0002 to 1.0025 across its last two points.

The [complete figure bundle](lifted-figures/README.md) retains all four
comparators, absolute runtimes, wall and CPU panels, and every control.
Its [visual audit](lifted-figures/QA.md) covers all nine PNGs. Points are
measured sizes, lines merely connect them, and error bars show individual
trial ranges. There is no fitted extrapolation.

## The classical losses remain decisive

The largest size makes the tradeoff visible. These are all twelve
`n=1,048,576` cases, including every random control. Each cell is a paired
wall-time ratio with KKT in the numerator.

| Ordering | b | d | Compactor | Kruskal | Prim | Original Borůvka |
|---|---:|---:|---:|---:|---:|---:|
| Hierarchy | 2 | 16 | 1.0246 | 2.3780 | 0.9014 | 0.8279 |
| Hierarchy | 2 | 64 | 0.9274 | 2.4906 | 1.7777 | 1.5534 |
| Hierarchy | 4 | 16 | 1.0469 | 1.8521 | 0.8220 | 0.7205 |
| Hierarchy | 4 | 64 | 1.0048 | 1.9501 | 1.6409 | 1.4675 |
| Dyadic distance | 2 | 16 | 1.0319 | 2.3733 | 0.7253 | 0.8355 |
| Dyadic distance | 2 | 64 | 0.9293 | 2.4386 | 1.4135 | 1.6361 |
| Dyadic distance | 4 | 16 | 1.0554 | 1.8541 | 0.7110 | 0.7136 |
| Dyadic distance | 4 | 64 | 1.0025 | 1.9564 | 1.3373 | 1.4745 |
| Global random | 2 | 16 | 1.0195 | 3.0694 | 0.9446 | 2.4168 |
| Global random | 2 | 64 | 1.0367 | 3.5900 | 2.4151 | 5.2035 |
| Global random | 4 | 16 | 1.0276 | 2.5981 | 0.8260 | 2.0983 |
| Global random | 4 | 64 | 1.0351 | 3.4253 | 2.3502 | 4.7270 |

Kruskal beats KKT by case median at every largest-size input. Across all
28 cases, KKT's four case-median wins over Kruskal occur at the smallest
size and `d=16`; all four lose to the compactor. Conversely, its four wins
over the compactor occur in the two ordered `b=2,d=64` groups at the larger
sizes; all four lose to Kruskal. Their intersection is empty, so KKT is
never ahead of all four comparators by case median in this pilot.

At the best compactor case, KKT's wall ratios against Kruskal, Prim and
original Borůvka are 2.4906, 1.7777 and 1.5534. All five individual trials
lose to each of those three algorithms. All five also lose to those three
at the largest `distance2,d=64` case. CPU results preserve these outcomes.
The [full analysis](lifted-analysis/report.md) and
[individual paired ratios](lifted-analysis/paired_ratios.csv) retain every
smaller-size result and loss; these tables do not hide unsuccessful controls.

This is consistent with the previous study's central limitation: beating
the compactor does not establish being the fastest MST implementation. That
study's separate classical adjunct also lost to Kruskal and original Borůvka
in every trial on its three selected inputs. Those old times are context,
not observations pooled into this five-solver campaign.

## Why the bundled lift reduces the opportunity for filtering

The first ordered contraction selects every cheap star edge. Each complete
bundle then collapses to its cheapest representative, leaving exactly

`M = [nd − n(1−1/b)] / b²`

core edges. The fraction of original edges remaining after this one round
is therefore `[1 − (1−1/b)/d] / b²`:

| b | d | Edges retained after the first ordered contraction |
|---:|---:|---:|
| 2 | 16 | 24.21875% |
| 2 | 64 | 24.8046875% |
| 4 | 16 | 5.95703125% |
| 4 | 64 | 6.1767578125% |

These are exact consequences of the generator and contraction rules,
supported by the independent small-fixture oracle. They are **not measurements
of KKT's heavy-edge filtering fraction or large-input work counters**.
They apply to the two ordered modes, not the globally shuffled controls.

Both KKT and the compactor pay for the original first contraction, and both
already remove roughly 75–94% of input edges in that round. KKT then performs
its second contraction before sampling. The construction reduces its vertex
count, but also reduces the edge volume on which later sampling might save
repeated work. Thus it dilutes the opportunity for filtering to pay for its
additional work. It does not establish that filtering itself becomes less
effective, nor identify which allocator, cache or verifier cost accounts for
the measured seconds. Large-input counters remain pending.

For fixed b, this reduction is a constant factor. It neither refutes KKT's
expected linear bound nor proves a wall-time advantage at sufficiently large
inputs. Operation counts, measured crossover points and asymptotic theorems
answer different questions. The earlier [hierarchy work bound](../crossover-2026-10-13/HIERARCHY_BOUND.md)
concerns its stated model and contraction volume; it is not a timing lower
bound for all comparators or an extrapolated crossover for this new model.

## Density pilot: stronger compactor leads, larger classical losses

The [25-case density manifest](density-pilot.csv) tests the existing
`hierarchical_tree` and `distance_tree` families at densities 16, 64 and 128
and three sizes, plus density512 at the two smaller sizes. The backbone
joins the halves of each aligned dyadic block using sampled endpoints.
Hierarchy ranks make that tree cheaper than every shortcut; distance ranks
apply dyadic ordering to all edges, allowing a different MST. Two globally
random-weight tree controls and a connected G(n,m) control retain the
negative comparisons. These are separate models from the bundled lifts.
The seed, repetition, order, certificate and clock rules are the same as
the lifted pilot; the largest input has 33,554,432 edges.

All entries below are paired KKT/compactor wall-time medians. A dash means
that size/density was not measured, not that a result was omitted.

| Core ordering | d | n=16,384 | n=65,536 | n=262,144 |
|---|---:|---:|---:|---:|
| Hierarchical tree | 16 | 1.3109 | 1.1854 | 0.9242 |
| Hierarchical tree | 64 | 1.2287 | 0.9989 | 0.8665 |
| Hierarchical tree | 128 | 1.1800 | 0.9684 | 0.8878 |
| Hierarchical tree | 512 | 1.0738 | 0.9913 | — |
| Distance tree | 16 | 1.2740 | 1.1995 | 0.9412 |
| Distance tree | 64 | 1.2542 | 1.0325 | 0.8724 |
| Distance tree | 128 | 1.1865 | 0.9548 | 0.8817 |
| Distance tree | 512 | 1.0956 | 1.0043 | — |

Ten of 25 cases have compactor ratios below one. Four reach 0.90 or less
on both wall and CPU time: both ordered families at n=262,144 and d=64/128.
All five repetitions of each of those four cases are individually below
0.90 as well. The best case, hierarchy/d64, has wall median 0.866514 and
CPU median 0.866511; its observed wall range is 0.8590–0.8999. That is a
13.3% elapsed-time reduction against this compactor on this realization.

Each of those four groups has a measured smaller-size loss and a larger
lead, so the screen contains observed parity crossings. It does **not**
pass the confirmation criterion: only one size in each group reaches the
10% threshold, only one graph seed has been used, and the two fresh-seed
campaigns have not run. Near-ties remain mixed: hierarchy/d64 at n=65,536
has three winning and two losing repetitions; hierarchy/d512 at the same
size has four wins and one loss. Distance/d512 has two wins and three losses.

Increasing density is not uniformly helpful to KKT's relative runtime.
At n=262,144 both ordered families have a better compactor ratio at d=64
than at d=128. The d=512 cases at n=65,536 are near parity rather than
decisive wins. These are observed comparisons, not a hardware-cause claim.

The strongest compactor cases and all three random controls still lose to
every classical baseline by case median:

| Input | n | d | Compactor | Kruskal | Prim | Original Borůvka |
|---|---:|---:|---:|---:|---:|---:|
| Hierarchical tree | 262,144 | 64 | 0.8665 | 3.4424 | 3.4632 | 3.6752 |
| Hierarchical tree | 262,144 | 128 | 0.8878 | 3.6317 | 5.3360 | 4.3335 |
| Distance tree | 262,144 | 64 | 0.8724 | 3.4834 | 2.4510 | 3.6916 |
| Distance tree | 262,144 | 128 | 0.8817 | 3.6410 | 3.7393 | 4.3080 |
| Global-random tree | 262,144 | 128 | 1.0319 | 3.1467 | 4.7787 | 8.1376 |
| Global-random tree | 65,536 | 512 | 1.0152 | 2.3643 | 7.4991 | 8.1192 |
| Connected G(n,m) random | 262,144 | 128 | 1.0415 | 3.1464 | 4.6976 | 8.2317 |

Across the complete density pilot, KKT loses **all 125 paired timed trials
to Kruskal and all 125 to original Borůvka**, on both wall and CPU time.
It beats Prim by median on five cases, but no case wins against all four.
Thus stronger filtering opportunities on these dense ordered graphs have
not supplied the practical all-comparator crossover being sought.
The [complete table](density-analysis/report.md),
[individual pairs](density-analysis/paired_ratios.csv),
[all size/runtime figures](density-figures/README.md), and
[eight-PNG visual audit](density-figures/QA.md) retain every case and loss.

## Remaining experiments — PENDING

**Attachment extension — PENDING.** The [declared extension](ATTACHMENT_PROTOCOL.md)
replaces each core edge by one original edge rather than a complete bundle.
Cheap stars can then shrink vertices while preserving much more edge volume.
Leaf and community endpoint variants separate where those edges attach.
Alongside hierarchy and distance ranks, a shuffled-core control keeps the
cheap stars but removes hierarchical ordering; a global-random control also
removes the cheap-star partition. The frozen 80-case pilot uses block sizes
four and sixteen, densities two and sixteen, and the same discovery seeds.
Independent fixture validation, the new source freeze and all measurements
are pending in this draft. This is a hypothesis, not a forecast of a win.

**Confirmation — PENDING.** At most two family/density groups may be selected
after exploration. Their exact sizes and controls must be frozen before
using fresh graph seeds 1000039, 1000081 and 1000099 and sampling seeds 401
and 503. The second complete campaign reverses case order while repeating
the same graphs; it is not another independent graph sample. A clear
advantage requires paired case medians at most 0.90 at two adjacent largest
selected sizes in both campaigns, every graph-level median below one, and
the same threshold/direction in CPU diagnostics. Success against each
competitor and against all four must be reported separately. An observed
smaller-size loss/tie is additionally needed to bracket an onset. This is a
predeclared descriptive criterion, not a significance test.

## Evidence quality and reproducibility

Strict validation passed all 840 lifted calls, including 140 retained
warmups, and all 750 density calls, including 125 warmups. The separate
[fixture correctness gate](validation/SEARCH_FIXTURES_TEST.md)
passed 167 fixtures, 917 complete contraction stages and 1,169 independently
certified solver outputs, with explicit malformed-dimension and edge-cap
checks. Those untimed tests are correctness evidence, not timing samples.
The [harness review](validation/PEER_REVIEW.md) records boundary, schedule,
certificate and provenance checks, including the corrected log-parser smoke
failure and its retained evidence.

Neither campaign has diagnostic call-clock or capture/child UTC flags.
The [lifted power audit](lifted-power-audit/audit.json) and
[density power audit](density-power-audit/audit.json) find no logged
Sleep/Wake/DarkWake event in their capture intervals or overlapping calls.
However, both `caffeinate` assertion attempts **failed**: these were not
verified sleep-inhibited runs. Absence of logged events does not establish constant
frequency, thermal state, contention or core placement. All observations
remain unchanged. Periodic process-group RSS is a sampled sum, not a
continuous peak or a count of unique physical pages.

The [raw CSV](lifted-timing.csv), [capture metadata](lifted-timing.json),
[validated analysis provenance](lifted-analysis/provenance.json),
[all case comparisons](lifted-analysis/comparisons.csv),
[separate runtime summaries](lifted-analysis/summary.csv), and
[figure provenance](lifted-figures/provenance.json) preserve the lifted commands,
hashes and observations needed to inspect this screen. Future campaigns
must retain their own revisions and data rather than replace these losses.
The density campaign's corresponding [raw CSV](density-timing.csv),
[metadata](density-timing.json), [analysis provenance](density-analysis/provenance.json)
and [figure provenance](density-figures/provenance.json) remain separate.
These repository experiments establish bounded implementation observations;
they do not establish independent published consensus about whether KKT is
universally practical or “galactic.”

Full machine power-history logs and parsed event lists remain local and ignored;
their hashes, campaign-specific overlap counts and per-call associations are
retained in the published audit summaries. They are not required to read the
performance results.
