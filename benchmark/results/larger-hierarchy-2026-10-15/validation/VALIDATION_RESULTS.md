# Independent larger-study validation results

Both first attempts passed: five synthetic audit groups, followed by independent
reconstruction of the complete capture. Exact commands, source hashes, logs and
empty-group evidence are in [the mock receipt](audit-mocks-attempt01.json) and
[the actual receipt](audit-actual-attempt01.json). Groups 35652 and 35691 exited
with status 0 and were verified empty. No native solver was launched by this
validation. No validation jobs remain running.

The [audit](independent-numerical-audit-attempt01/README.md) agrees with all 720
paired clock ratios, 396 medians and associated ranges/counts, 30 point states,
30 earlier/later endpoint pairs and ten crossover summaries. It independently
checked 12 children, 504 outputs, 12 certificates, six topology twins, exact raw
concatenation, resources and the full frozen ancestor chain without importing
collector code. No call or capture/child UTC clock flags were present.

Ratios below are pooled medians of KKT/control wall times; below 1 favors KKT.
Each point contains six repetitions on each of two graphs. Classifications
additionally require the per-graph medians on both wall and CPU clocks.

| Family | Control | 65,536 | 1,048,576 | 4,194,304 | Classified sequence |
|---|---|---:|---:|---:|---|
| Ordered hierarchy | Compacting Borůvka | 0.807722 | 0.319096 | 0.392388 | Strong lead throughout |
| Ordered hierarchy | Retained-edge Borůvka | 1.118110 | 0.967405 | 1.078605 | Loss, narrow lead, loss |
| Ordered hierarchy | Kruskal | 1.270189 | 1.510136 | 2.110850 | Loss throughout |
| Ordered hierarchy | Prim | 2.268118 | 1.763093 | 1.681680 | Loss throughout |
| Ordered hierarchy | Original Borůvka | 1.644206 | 1.011129 | 0.886100 | Loss, loss, strong lead |
| Shuffled hierarchy | Compacting Borůvka | 0.860684 | 0.338585 | 0.399376 | Strong lead throughout |
| Shuffled hierarchy | Retained-edge Borůvka | 1.738165 | 1.519935 | 1.533682 | Loss throughout |
| Shuffled hierarchy | Kruskal | 1.105924 | 1.304781 | 1.679895 | Loss throughout |
| Shuffled hierarchy | Prim | 1.990898 | 1.531011 | 1.359760 | Loss throughout |
| Shuffled hierarchy | Original Borůvka | 2.519746 | 1.561274 | 1.278455 | Loss throughout |

Only ordered hierarchy versus original Borůvka has a declared strong measured
bracket: **(1,048,576, 4,194,304]**. At the upper endpoint the pooled wall ratio
is 0.8861003267 and CPU ratio 0.8859880241. The two graph medians span
0.8826862501–0.8861381296 on wall and 0.8825417818–0.8860088431 on CPU, all below
0.9. All twelve trials beat that control, but the maximum wall trial ratio is
0.9106854895: a 10% improvement does not hold for every individual trial.

The ordered retained-edge comparison reverses its small 1M advantage. Its 4M
wall graph medians are 1.0725136047–1.0874837577; all twelve trials lose.
The two compacting comparisons already lead at the smallest size, so they do
not constitute observed loss-to-lead crossings in this matrix. KKT does not
win against every solver on any tested case.

The bracket is descriptive evidence for this binary, machine and fixed matrix,
not an interpolated threshold or proof of eventual dominance. There is no
measured point beyond 4M; the declared sustained-suffix condition therefore has
no later point to test. Two graph seeds and one fixed sampling seed do not
establish a population-wide result or provide confidence intervals.
