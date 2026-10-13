# Five-solver crossover search

Frozen before timing on 13 October 2026 UTC. Continues the
[previous search](../crossover-2026-10-13/README.md) with unchanged production
KKT, compacting Borůvka, Kruskal, Prim and original Borůvka. Dijkstra solves
shortest paths and is not an MST comparator.

## Hypotheses and fixtures

Higher density may amortize KKT's vertex-dependent costs. It can also shorten
the compactor's expensive phase, so a favorable trend is not assumed. The
density pilot uses existing exact fixtures: `hierarchical_tree` and
`distance_tree` at n=16,384, 65,536, 262,144 with m/n=16,64,128; both at
n=16,384 and 65,536 with m/n=512; and three globally random rank controls.
The frozen `density-pilot.csv` has 25 cases (shuffle seed 202610132).

The second hypothesis is that inexpensive initial contraction can reduce
KKT's constants while leaving a substantial, slowly contracting quotient.
The new **lifted** families replace each of q=n/b core vertices by b=2 or 4
vertices joined by a cheap local star. Each core edge becomes a complete
b-by-b bundle. There are q(b-1) local edges and exactly
`core_m = (nd-q(b-1))/b²` core edges, so the expanded simple graph has m=nd.
The core consists of a path plus uniformly proposed distinct shortcut pairs.

For `lifted_hierarchy{b}`, path ranks are ordered by dyadic merge level and
all shortcuts rank above them. For `lifted_distance{b}`, every core edge is
ranked by the dyadic separation of its endpoints, with shuffled ranks within
each level; shortcuts can enter the MST. Each core rank expands to a disjoint
bundle rank interval, all above the local star ranks. A first Borůvka round
collapses each star; the remaining quotient can merge slowly. This is a
testable mechanism, not an assurance that the first two KKT contractions
leave its verifier a cheap problem.

The global random controls `lifted_random{b}` independently permute all m
expanded weights. At the same b,n,d,graph seed, all three variants have the
same topology, edge IDs, relabeling and input order. All weights are unique.
Solvers see only shuffled, relabeled edge tuples, never core metadata.
These are engineered graph substitutions, not measured application networks.

The frozen `lifted-pilot.csv` has four ordered families at n=65,536,262,144,
1,048,576 and m/n=16,64, plus both random controls at the largest size and
both densities: 28 cases (shuffle seed 202610131). Run this pilot first.
Largest pilot graph: 67,108,864 edges. All pilot cases, including losses,
will be reported. Graph seed 5009 and KKT seed 149 are discovery-only.

## Measurement and correctness

Every fixture is independently cycle-certified before timing. All five
solvers process the same graph. Every result, including warmups, must match
the certified unique MST; classical solvers also require exact tuple
membership. A separate fixture suite checks topology, ordered bundles,
contraction partitions and variable-MST cases against independent oracles.

Use `bin/large_stack/mst_search`, the native Apple Clang Make -O3 profile,
assertions enabled, with the same 512 MiB stack for every solver. This
addresses original Borůvka's recursive DFS; it does not alter its algorithm.
The normal and enlarged-stack executable code sections must match. Maximum
study dimensions are n=4,194,304 and m=134,217,728; no extrapolated stack
safety beyond this domain is claimed.

One checked warmup and five timed repetitions per solver per graph/sampling
seed pair. Rotate the five algorithms through every position exactly once.
Use existing public tuple-input boundaries: KKT/compactor conversion and
temporary input destruction are timed, returned result destruction and
validation are outside. Log steady elapsed, enclosing process CPU and UTC
clocks, fingerprints and a bound reference certificate. No durations are
discarded or adjusted. Aggregate paired ratios within each repetition, then
take medians over repetitions, sampling seeds and graph seeds, in that order.
Repeated calls are not independent graph samples.

Run only one native experiment at a time. No concurrent builds, native tests,
plotting or instrumented runs. Record source, Makefile, helper, manifest and
binary hashes before/after every capture. Preserve partial failures. Sample
process-group RSS every two seconds; terminate above 40 GiB or after three
consecutive resource-observation failures. Sampled RSS is not a continuous
peak and shared pages may be counted twice. Record system swap and power
state; stop for sustained substantial new swap. Existing swap at protocol
preparation was about 660 MiB and is not itself evidence of study pressure.
Use `caffeinate -i` during each capture to inhibit idle system sleep; this does
not prevent lid or explicit sleep. Audit power events against measured UTC
intervals. Retain clock flags and
sleep-affected campaigns with explicit limitations.

## Extensions and confirmation

Any additional size/density screen is declared in a dated extension before
execution. Select at most two promising family/density groups for fresh
confirmation; freeze their size range and controls before consuming holdout
seeds. A crossover requires an observed smaller-size loss/tie and larger-size
advantage. An all-winning range identifies a winning family without locating
the onset. Neither implies that every larger size will win.

Reserved fresh graph seeds: 1000039,1000081,1000099. Sampling seeds: 401,503.
Use five rotated timed repetitions and one checked warmup. Run two complete
campaigns, with the second in reverse case order; repeated seeds are not new
graph samples. A **clear measured advantage over a comparator** requires
paired case medians <=0.90 at two adjacent largest selected sizes in BOTH
campaigns, every graph-level median <1, and the same threshold/direction on
the process-CPU diagnostic. Report separately success against compacting
Borůvka and success against all four comparators. This is a descriptive
criterion, not a significance test or an asymptotic proof. Near-ties, failed
criteria and unexpected classical wins remain visible.

Untimed counters and contraction trajectories can explain results, but their
durations are not performance observations. Changing weight magnitudes by a
strictly monotone map cannot affect rank-based decisions; useful hypotheses
must change rank/topology relationships, not merely the numerical scale.

The previous astronomical fitted crossover does not establish an algorithmic
lower bound. These repository experiments do not establish independent
published consensus and authorize no Wikipedia edits.
