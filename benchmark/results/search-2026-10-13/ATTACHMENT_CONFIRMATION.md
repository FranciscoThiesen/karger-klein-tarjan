# Prospective large-size and fresh-seed attachment experiments

Declared 14 October 2026 UTC after the complete 80-case attachment discovery
capture, before running any case below or consuming a reserved seed.

Select **leaf_hierarchy4, d=16** and **leaf_distance4, d=16**. Their largest
discovery cases have the two lowest KKT/compactor paired wall medians across
all 133 cases in the three completed pilots: 0.830921 and 0.838606. No pilot
case wins against all four competitors, so selection follows the protocol's
compactor-specific fallback. This is selection on observed discovery data;
the fresh-seed results must stand separately. Both selected families lose
to all three classical implementations at their largest discovery size.

## Additional discovery sizes

The frozen ten-case `attachment-large-pilot.csv` adds n=524,288, 2,097,152
and 4,194,304 for both selected groups. The shared leaf_shuffled4 and
leaf_random4 weight controls are included at 2,097,152 and 4,194,304.
All use d=16, graph seed 5009 and sampling seed 149. The shuffled control
keeps cheap local stars; the random control also randomizes local weights.
Ordering uses Python Random(202610142). These results remain discovery-only.
The 4,194,304-vertex, 67,108,864-edge points are stress extensions, not part
of the confirmation grid. This distinction is fixed **before** seeing their
results; their favorable or unfavorable outcomes will both be published.

## Two complete confirmation campaigns

The confirmation grid is frozen now, independent of the extra discovery
outcomes. For both selected ordered groups it contains n=65,536, 262,144,
524,288, 1,048,576 and 2,097,152. Both shared controls are measured at
2,097,152. This is 12 cases per campaign. The lower sizes test crossover
onset; the upper two selected sizes are 1,048,576 and 2,097,152.

Use all three reserved graph seeds 1000039, 1000081, 1000099 and both sampling
seeds 401, 503, with five rotated repetitions and one checked warmup for
each of the five unchanged solvers. Each campaign therefore has 72 native
seed-pair captures, 1,800 timed calls and 360 checked warmups. Campaign A
uses `attachment-confirmation-a.csv`, shuffled with Random(202610143).
Campaign B uses the exact reverse case order in
`attachment-confirmation-b.csv`; seed-pair order remains unchanged.
Repeated graphs in campaign B are not new independent graph samples.

The original descriptive success criterion applies separately to every
competitor: case medians at most 0.90 at both upper selected sizes in both
campaigns, every graph-level median below one, and the same threshold and
direction for process CPU. A smaller measured loss/tie is required to call
the observed transition a crossover. No fitted extrapolation, confidence
interval or guarantee about all larger sizes is implied. No further family
will be selected using these held-out results.

## Unchanged measurement rules and power limitation

Keep all five solvers, original public-call timing boundaries, native
512 MiB stack profile, independent cycle certificates, exact output checks,
resource limits, source/binary hashes and all losses from `PROTOCOL.md`.
Run native timing serially with builds, plotting, browser activity and work
instrumentation stopped. No solver or fixture implementation is changed.

Both idle-sleep and AC system-sleep caffeinate assertions failed in this
environment. `pmset` confirmed no assertion was created. Do not describe
these captures as sleep-inhibited. Preserve this limitation, record power
state and audit logged sleep intervals against every completed campaign.

Untimed counter diagnostics use discovery seeds only. Their observed
contraction volumes can be compared with the occupancy model, but are not
execution-time measurements or proof of asymptotic runtime on this machine.
