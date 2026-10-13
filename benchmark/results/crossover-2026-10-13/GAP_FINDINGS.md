# Late-gap collapse: validated structure, small edge-volume effect

The [path-only simulation](line_gap_stages.csv) reproduces the two fixture gap
streams for graph seed 3037 at 1,048,576 and 8,388,608 vertices. Its
[capture metadata](line_gap_stages.json) records four graphs and 51 stages,
including each initial and terminal state. The independent small-path DSU
[self-test](gap_selftest.json) passed 3,297 cases and 6,360 transitions. The
[full-graph check](line_gap_full_graph_check.json) then matched all 47 production
rounds: component count, sum of squared original component sizes, largest
component and selected-edge count agreed exactly. Its hashes bind the simulator
to the [validated diagnostics](diagnostics-analysis/provenance.json) and the
actual [trace CSV](diagnostics_trace.csv) and [moment log](diagnostics_trace.log).
An independent recomputation confirmed these hashes, matches and the sums below.

These are structural observations for one graph seed, not additional timing
measurements. Moment agreement does not by itself identify every component's
membership; the source-level weighted-path argument supplies that connection.

## The equal-gap event exists, but happens late

At one million vertices, narrow gaps reach stage 8 with 42 components and
41 remaining path boundaries, all having raw gap 1,024. Their increasing
original-ID tie-break makes the next round merge the entire remaining path.
There are nine contractions in total. The wide-gap graph takes 13.

At eight million vertices, stage 8 has 300 components and 299 boundaries:
298 raw gaps are 1,024 and one is 1,023. The next round leaves two components;
their final boundary is 1,024, and the tenth round finishes. The wide-gap
graph takes 15 rounds. Wide-gap maxima are unique in every nonterminal
record of these two realizations; a distinct-value count for the full wide
alphabet was not collected.

The predicted late collapse therefore agrees with the production stages, but
round count alone exaggerates its possible edge-volume importance. Production
contraction keeps a simple quotient, so `q` components imply at most
`C(q,2)` surviving edges, whatever their weights or shortcut density.

## The remaining edge volume is small, even at its capacity bound

For the measured density `m=16n`, sum `C(q_r,2)` over every remaining
nonterminal stage `r≥8`. This bounds **all subsequent contraction-call input
edges**. Each call's input is counted once, not once per internal loop. Stage 8
is after eight completed contractions, so this sum starts with the ninth
call. The real trace attains the bound in all four cases: every quotient from
stage 8 onward is complete. The bound is a mathematical capacity; the observed
column is independently summed from the real trace.

| Gap alphabet | Vertices | Capacity upper bound | Observed tail edge inputs | Tail / original m | Tail / total V |
|---|---:|---:|---:|---:|---:|
| 1…1,024 | 1,048,576 | 861 | 861 | 0.005132% | 0.001010% |
| 1…2³² | 1,048,576 | 10,925 | 10,925 | 0.065118% | 0.012805% |
| 1…1,024 | 8,388,608 | 44,851 | 44,851 | 0.033417% | 0.005639% |
| 1…2³² | 8,388,608 | 738,693 | 738,693 | 0.550369% | 0.092361% |

The total volume `V` includes the original graph, so `V≥m`; the `tail/m`
percentages therefore upper-bound the fraction of total contraction volume
lying in that tail. The measured `tail/V` fraction is smaller still: below
0.093% in all four traces. The wide graph's additional rounds *after the narrow
graph has already terminated* consume only 1,195 edge inputs at one million
vertices and 8,667 at eight million, respectively about 0.00713% and 0.00646%
of `m`; these also attain their simple-graph capacity bounds.

The component-size moments tell the same chronological story. At narrow
stage 8 the largest component contains 8.204% of the one-million graph and
1.727% of the eight-million graph. In the latter, a component reaches 58.466%
at stage 9, when only two components—and therefore at most one quotient
edge—remain. The terminal giant component is confirmed in the real trace but is
too late to explain the bulk of repeated edge scans.

## Earlier partitions account for most of a small total difference

The full volumes agree with the independently generated
[trace summary](diagnostics-analysis/trace_summary.csv):

| Vertices | Narrow V | Wide V | Narrow V/m | Wide V/m | Wide increase over narrow V |
|---|---:|---:|---:|---:|---:|
| 1,048,576 | 85,237,236 | 85,316,683 | 5.080535 | 5.085271 | 0.093207% |
| 8,388,608 | 795,397,291 | 799,786,517 | 5.926172 | 5.958874 | 0.551828% |

At one million vertices, 69,383 of the 79,447 extra wide-line edge inputs occur
before stage 8: 87.33% of the net difference. At eight million, that earlier
difference is 3,695,384 out of 4,389,226, or 84.19%. Individual stages need not
all favor the same graph; these are differences of summed volumes.

The eight-million trace makes the earlier divergence visible. At stage 6,
narrow/wide component counts are 10,496/10,700 and remaining edge counts are
44,576,488/45,993,436. At stage 7 these are 2,861/3,511 components and
4,089,203/6,157,543 edges. Those two stages contribute 3,485,288 extra wide-line
edge inputs. The late equal-gap collapse therefore cannot explain the bulk
edge-volume work, and the *entire* alphabet change increases total compactor
volume by less than 0.56% in these realizations, despite four or five extra
rounds.

## What the alphabet comparison does not isolate

The narrow and wide generators share topology and use corresponding RNG words,
but `word % 1024` versus `word` changes the order of unequal gaps as well as
tie frequency. This is an alphabet/distribution comparison, not an isolated
change to tie-breaking. Different early partitions can change which parallel
edges survive and their storage order, and can affect KKT's sampled recursion.
Neither the simulator nor an edge-volume count identifies the wall-clock
cost of those effects. No hardware-level cause is established here.

Both alphabets are fixed. The bound `O(Km+n)` for alphabet size `K` therefore
applies to both mathematical extensions: `K=1024` and `K=2³²`. Wide gaps reduce
ties at these tested sizes but do not create an asymptotic continuous-weight
model. At eight million vertices, the ordinary 23-round halving bound is
already smaller than either alphabet cap.

The validated diagnostics establish the merge schedule's component statistics
and the associated edge volume. They do not establish why elapsed time differs
between campaigns or guarantee the same quantitative differences for other
seeds or sizes. The timing observations remain separate from this structural
explanation.
