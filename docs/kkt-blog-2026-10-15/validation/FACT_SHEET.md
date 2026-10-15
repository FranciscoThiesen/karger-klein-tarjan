# KKT blog fact sheet — independent source and numeric audit

Source snapshot: `/Users/random_person/Desktop/kkt-eighth-sampling`, commit `ab46700`; exact requested report `docs/kkt-report/current-2026-10-15/html-attempt03/REPORT.md`, SHA-256 `afe0941ab3883aab2e1f0ee414bd0fe521d014adb7c541e76a94be4093967062`.

No benchmarks were run for this audit. `docs/kkt-blog-2026-10-15/validation/verify_claims.py` independently rebuilt paired medians, graph medians, ranges and win counts from the already independently audited `validated_calls.csv` tables, using exact rational arithmetic. It verified 560 comparator rows / 6,720 timing ratios across the lower-density, hierarchy-extension and distance studies, plus all 72 half/eighth comparison rows, all 150 lower-density point states, and the current Google model-choice inventories. Full selected values, source hashes and check counts are in `docs/kkt-blog-2026-10-15/validation/verified-claims.json`. This supplements the studies' prior raw/provenance audits; it is not a new measurement or a fresh independent rebuild.

## The claim the evidence supports

**This implementation can make KKT practically useful on particular engineered weight arrangements. There is now a measured, sustained crossover against a strong retained-edge Borůvka control. It is not the fastest assessed algorithm at every size—or even the fastest case-level algorithm at the headline largest endpoints.**

The decisive new example is distance-ranked attachments at `m=16n`: retained-B ratio 1.142253 wall at n=512, 0.940215 at 2,048, 0.820461 at 8,192, then a strong lead at every measured larger size through 2,097,152. At that endpoint, ratio 0.708792 means **29.1% less elapsed time**, or approximately **1.41× speedup**, against that comparator. Kruskal still wins there.

“Galactic” is not a property established or refuted by a single plot. The old implementation had defects that prevented a fair implementation of the intended work bound. Repairing those and testing strong controls reveals useful finite cases; it does not establish blanket superiority, automatic eventual domination, or a new theorem about actual hardware time.

## Original failures: separate categories

### 1. A shrinking graph still paid for original edge-ID space — asymptotic accounting defect

Audited baseline `693c6a5` (2026-01-11), repaired `60c65b4`. This bitmap regression was introduced by the January 2026 attempt to replace hash sets; it was **absent from the 2022 implementation**, which used sets. `R = 1 + max(original ID)` sized tracking/result bitmaps and their merge loops. Contractions preserved original IDs, so a tiny recursive child still cleared and scanned root-sized storage. Sparse IDs made cost depend on an arbitrary numeric range rather than represented input. The old signed maximum-ID arithmetic could overflow; negative IDs were invalid bitmap indices.

Illustrative pseudocode, not literal code:

```text
# Old: R survives contraction
solve(G):
    selected = zeros(R)
    sample_result = solve(sample(contract_twice(G)))
    for id in 0 .. R-1: merge selected[id]

# Repaired: original ID is payload; local position sizes local work
solve(G, answer_ids):
    local_marks = zeros(G.edge_count)
    append safely selected original IDs to answer_ids
    recurse using the current graph's edge positions
```

A hierarchical weighted path supplies logarithmically many main-branch contraction levels; a tree has no removable F-heavy edges. Repeated original-range work is therefore superlinear even with dense IDs. Do not imply that all vectors became sets: internal selected IDs became append-only vectors; the public API still returns a reserved hash set.

### 2. The supposedly linear verifier built its lookup table superlinearly — asymptotic preprocessing defect

Repaired `312954e`. The bad builder was already present in `805a330` (2020-06-17, `verification.cpp`), copied to `verifier_v2.cpp` in `8a56a5a` (2020-08-31), and persisted in the 2022 report revision `ae02010`. Old table generation repeatedly enumerated set members across masks. In an h-bit universe the memberships total `h·2^(h−1)`, so even one slice costs `Ω(h·2^h)`. For the relevant equal-depth full binary case, `L=2^h`, giving `Ω(L log L)` work.

```text
# Old idea
for mask in depth_masks:
    members = enumerate_set_bits(mask)
    table[mask] = members[len(members)//2]  # upper median

# New constant-word recurrence, masks visited in increasing order
highest = highest_set_bit(mask)
inner = remove_lowest_set_bit(mask) with highest cleared
table[mask] = index(highest) if inner == 0 else table[inner]
```

The implementation maintains the highest bit while scanning masks; it does not hide a per-mask linear search. Removing both extremes preserves the upper median. The table has `2^(height+1)` slots. Its linear-size justification needs **equal-depth leaves plus at least two children per internal node**, properties of this reduction: `L≥2^height`, hence at most `2L` slots. An arbitrary unbalanced binary tree would not justify the claim. Current source: `verifier/median_table.hpp:12–29`.

### 3. Every recursive sample restarted a global RNG — probabilistic-model and state-isolation defect

Repaired `ccb833f`. Restarting with `srand(0)` is present by `93f6c54` (2020-09-07); the 2022 revision uses `srand(seed)` inside every sample. Thus this issue, unlike the bitmap regression, predates the 2022 post:

```text
# Old
sample(G, seed):
    srand(seed)
    return edges whose next rand() is odd

# New
kkt(G, seed):
    rng = MT19937(seed)
    recurse(G, rng)  # one continuing stream, passed by reference
```

Restarting repeats prefixes and mutates global state. It undermines the intended fresh-choice discipline conditional on recursively generated graphs. It is **not by itself proof of a wrong MST**; sampling affects expected work, while safe contraction/cycle filtering can still return the right answer. MT19937 remains a deterministic PRNG, not literally independent mathematical coins. Replaying an entire solver invocation with a fixed seed is intentional.

### 4. The original benchmark answered a narrower question than it appeared to — measurement defect

`693c6a5:benchmark/mst_benchmark.cpp` fixed n=10,000 and swept m=1.25M…20M. That primarily changes density, rather than tracing a fixed-parameter family as n grows. Its generator default seed was zero; measured outputs had no independent certification. KKT's tuple-to-internal conversion happened outside its timer.

```text
# Old boundary
P = convert(input_tuples)       # excluded
time: kkt(P)

# Current public-API boundary
time: {
    P = convert(input_tuples)
    answer = kkt(P)
    destroy P
}
certify/check answer            # excluded, same declaration for all solvers
```

Current comparisons retain actual return types: KKT and continuation controls return ID sets; classical algorithms return edge vectors. Return-value construction is included; result validation/destruction is outside. Do not call the older conversion exclusion a newly discovered slowdown: it actually favored KKT, and changing the boundary makes historical/current numbers nonmultiplicative.

### 5. Testing and linking had separate correctness hazards

- `17aa5cf`: Prim and KKT defined incompatible global `Edge` types. Prim's helper moved into an anonymous namespace, avoiding a C++ one-definition-rule violation when linked together. This is not an algorithmic improvement to Prim.
- Earlier repeated/default seeds weakened coverage; exact independent unique-MST edge IDs, input metadata, separate path/cycle certificates, and adversarial IDs/orders now strengthen it.
- The legacy `get_solution_cost` still accumulates into `int` (`kkt/kkt.cpp:281–290`). A matching or overflowing sum is not a certificate. Some original lightweight helpers already used 64-bit sums; do not claim every old test used overflowing arithmetic.
- Correctness and expected-work claims are distinct. Current valid-input study uses loop-free undirected graphs, distinct IDs/weights and represented integer bounds; isolates are normalized. Equal weights can be consistently ordered in general MST theory—unique weights are this implementation/study contract, not a universal MST requirement.
- Do not claim original Borůvka has general disconnected-MSF support: it may loop on disconnected input. Declared timing inputs here are connected. KKT's independent tests include disconnected forests.

**Historical typo, not a new discovery:** `a5fcc78c82b978d216c2d8e4df28e052792edabd`, dated **2020-09-10**, already fixed the Hagerup-derived mask expression from `1 << ((k+1)-1)` to `(1 << (k+1))-1`. This was a parenthesization/prefix-mask typo. The Portuguese report was added in 2022; do not date the repair to 2022 or imply the recent work rediscovered/fixed it.

## Constant repairs: expensive work is not automatically an asymptotic bug

| Change / commit | Actual mechanism and boundary |
|---|---|
| Flat contraction, `e45e861` | Replaced per-vertex allocation/pair hashing with flat adjacency and stamped endpoint buckets. Still deduplicated parallel quotient edges. |
| Verifier storage, `a3a4395` | Dense arrays for fresh branching-tree IDs, borrowed inputs, direct child links, no redundant retained LCA graph copy, skip components with no queries. |
| Local heavy marks, `4eb3ca1` | Positional byte marks replace building/probing a heavy-edge ID hash set. Public arbitrary-ID set API preserved. |
| Query ranges, `2749ced` | Contiguous endpoint ranges replace linked query lists and duplicate per-query arrays; direct graph-edge maxima. |
| Cheapest-neighbor walks, `2e37b4e` | Label selected-edge components without materializing selected adjacency or duplicate bitmap; terminal component short-circuit. |
| Sample forest recovery, `af12309` | Private sample IDs are parent-array positions: recover chosen records directly, eliminating recovery hash set and full parent scan. Public sampler IDs/draws preserved. |
| Owned compaction, `ba39977` | Reuse temporary edge-vector storage while removing isolates; preserve const-input adapter. |
| Final reserve, `2d4fbf1` | Reserve known selected-ID count once before public hash-set insertion. |
| Retained quotients, `ae03ec6` | Keep every crossing parallel record; avoid dedup buckets/extra scans, typically at most three full input scans. Public dedup step and control remain. Changes edge order/draw assignment; not an identical-random-trajectory test. |
| Direct Edge verifier, `b7aa02b` | Borrow existing records instead of copying every query edge to a tuple vector. Both reference/candidate share the refactored verifier. |
| Compressed requests, `a7cb2d6` | Share requests with identical (lower vertex, proper ancestor depth). Logical Q stays; path-query visits go `4Q → 2Q+U`. Still processes/maps all original requests. |
| Private eighth sampling, `116c316` | Change private predicate `(word & 1)==1` to `(word & 7)==7`. One RNG word per visited edge, same order, public half sampler unchanged. Half reserve remains. Expected sample work drops; survivor bound grows. |

The separate packed-half experiment consumed 32 bits per word and improved its own comparison, but is **not combined into the current compressed/eighth executable**. Query lifetime shortening, full sample reserve and complete hierarchical metric were source proposals, not measured wins. The rejected minimum-edge cache enlarged per-vertex working storage and regressed the largest tested case about 6%; it must not be presented as an accepted improvement.

Current default build is also **not** the final experiment: ordinary build still deduplicates, copies tuple query inputs, uses individual queries and samples half. Current measured opt-in path is retained parallel + direct Edge + compressed verifier + scalar eighth; current timing binary SHA `954068775a83e1c42db62ffb6777c398dc05fd5792c60d2f293df6532130951a`.

## Why these shapes help—and why the controls matter

Four-vertex cheap-leaf stars contract quickly, leaving a core. In the ordered hierarchy family every forced path edge is cheaper than every chord; dyadic path ranks force slow pair merges. The distance-ranked family instead ranks **all core edges** by dyadic ancestry: shortcuts can enter its MST. It is not a Euclidean/road/nearest-neighbor benchmark and its rank weights need not satisfy triangle inequality.

After two ordered contractions, both families have `q=n/8`, `r=(d−7/8)n` crossing records. Many vertices disappear while most edges survive. Retained Borůvka repeatedly scans that large quotient. Sample/filter recursion can pay to certify large numbers of edges unnecessary. Many rounds alone do not suffice: a tree loses geometric edge volume and has nothing to filter.

Shuffled twins preserve topology, IDs, labels, input order, cheap leaves and exact core-weight multiset, while permuting ranks. They change the contraction/filtering problem without changing the drawing. KKT loses **every retained-B pair** in the current hierarchy, distance and lower-density shuffled series. Therefore the story is about **organized weights and persistent crossing edges**, not merely many leaves or density.

The deduplicating compactor is a materially different competitor. KKT's early large advantage against it largely exposed expensive deduplication; the shared retained-kernel continuation then beat that KKT version. Keeping original Borůvka also matters: although it repeatedly scans the original tuples, it avoids quotient materialization. Its lower per-pass cost can win despite more logical edge visits. Prim and Kruskal remain necessary independent controls.

## Verified numerical claim table

Ratios below mean median of matched `KKT time / comparator time`, never quotient of separate runtime medians. Wall/CPU both retained. Values <1 favor KKT. Read the named studies' full ranges and loss cases before quoting.

| Current experiment / claim | Verified value | Limit |
|---|---|---|
| Half → eighth, six cases | All 144/144 KKT trial pairs improve on both clocks; case medians about 24.6–32.0% less time | Separate six-case policy experiment, not universal optimal p; unchanged controls drift .97735–1.03339, unadjusted |
| Hierarchy d32, 1M / retained B | .67130 / .67130 | Smallest measured point already leads; no lower-loss bracket |
| Hierarchy d32, 4M / retained B | .84144 / .84125; 9/12 wins per clock | Wall range .64095–1.46180 includes large losses; graph/clock medians .83103–.84144 |
| Distance d32, 1M / retained B | .680665 / .680418 | All72 distance pairs win; all72 shuffled pairs lose; no measured lower loss |
| Distance d16, retained B | Sustained strong bracket `(512,8192]`; strong through2M | Two graphs, one repeated sampler, five strong suffix sizes; no interpolation |
| Distance d16, 2M / retained B | .708792 / .708792;12/12wins | Graph/clock range .706646–.711577; wall trial range .685811–.731127 |
| Distance d8, 4M / retained B | .972608 / .972607;7/12wins | Four graph/clock medians .941382–1.015940; mixed reversal, **no sustained strong bracket** |
| Lower-density all20 comparisons | 13 qualifying outcomes;102/490 endpoint pairs | Only1 outcome vsretained B, none vsKruskal; two shuffled-d16 brackets end at last point |
| Lower-density overall winner | No case beats allfive controls by pooled both-clock medians | Seven individual trials beat allfive on each clock; do not say “never fastest in any run” |
| Current Google Benchmark | All24 exported choices NlogN, including all12 KKT curves | Expected linear theorem ≠ finite timing fit; all192 custom clock/window choices also NlogN |
| Historical repairs | 62.662ms→13.985ms at4096vertices/524288edges; median paired speedup4.536719× | Separate old boundary/revisions; displayed median quotient differs; don't multiply across campaigns |

Largest endpoints, all five alternatives (pooled wall / CPU):

| Family, density, n | Dedup B | Retained B | Kruskal | Prim | Original B |
|---|---:|---:|---:|---:|---:|
| Distance16,2,097,152 | .2425/.2425 | .7088/.7088 | **1.2152/1.2152** | .6281/.6281 | .5299/.5299 |
| Shuffled16,2,097,152 | .2729/.2729 | **1.1219/1.1219** | **1.0815/1.0815** | .7431/.7431 | .8186/.8186 |
| Distance8,4,194,304 | .3509/.3509 | .9726/.9726 | **1.8485/1.8485** | .5267/.5267 | .4484/.4484 |
| Shuffled8,4,194,304 | .3199/.3199 | **1.1558/1.1558** | **1.3355/1.3355** | .5253/.5253 | .5419/.5419 |

Kruskal wins all12 pairs at allfour largest lower-density endpoints. In the hierarchy extension Prim wins every ordered size by graph/clock medians; at ordered4M KKT/Prim≈1.264 and KKT/Kruskal≈1.662. These are indispensable limits to “where KKT shines versus all assessed alternatives.” Historical small-cover bipartite cases did beat the three classical solvers, but lacked the later two continuation controls and must not be relabeled current six-way victories.

Canonical sources (relative to worktree):

- `benchmark/results/lower-density-2026-10-15/analysis-attempt01/{validated_calls,comparisons,graph_comparisons,crossover_points,crossover_brackets,crossover_summary}.csv` and `independent-audit-attempt01/audit.json`.
- `benchmark/results/eighth-extension-2026-10-15/analysis/{validated_calls,comparisons}.csv`; equivalent `eighth-distance-2026-10-15/analysis/`.
- `benchmark/results/eighth-sampling-2026-10-15/analysis/{validated_calls,variant_comparisons}.csv`.
- `benchmark/results/current-complexity-2026-10-15/analysis-attempt01/{google_selection,model_fits,means}.csv`.
- `benchmark/results/repair-2026-10-09/{README.md,summary.csv}`.

## Work counters explain structure, not fractions of CPU time

At distance d16's largest input, retained contraction-input volume is about17.906m versus KKT2.403m. In shuffled controls retained falls to7.314–7.923m and KKT2.289m, yet retained wins. Volumes are cumulative repeated visits, not distinct edges; different loops have different costs.

For distance d8/4M the disconnected-verifier partition count is 11,478,993 for G1 versus78,826,591 for G2. Exact source-derived aggregate inequalities additionally prove a connected root sampled forest for G1 and a nonempty disconnected root forest for G2. This is stronger than merely observing a cumulative difference, but not a direct trace, isolate count or causal CPU profile. The difference is67,347,598 partition visits; other verifier edge-accounting terms differ by−11,760. See `work/partition-analysis-attempt01/INDEPENDENT_REVIEW.json`, `work/root-inference-attempt01/INDEPENDENT_REVIEW.json`, and the work README for all60 cases.

## Theory, empirical fits, and publication cautions

With two Borůvka steps `q≤n/4,r≤m`, independent fixed-p sampling gives expected `pr` sampled edges and at most `q/p` F-light records, even for a disconnected sampled MSF. Assuming linear local work `c(m+n)` and a linear verifier, `E[T]≤Am+Bn` follows with `A≥c/(1−p)` and `B≥2c+A/(2p)`. Half permits `(A,B)=(2c,4c)`; eighth permits `(8c/7,46c/7)`. Retaining parallels is the study's justified extension; the published KKT algorithm deduplicates and uses half. Hashing, machine words, representable counts and the PRNG model remain assumptions.

GoogleTest is correctness infrastructure. **Google Benchmark** `Complexity(oAuto)` is the empirical fit feature. Pinned1.5.2 chooses a zero-intercept model using library CPU time, then fits manual time to that chosen model; exported RMS is CPU only. The current24curve experiment uses explicit `N=n+m`,11sizes1024…1M,2376calls. All four native/library clocks and predetermined full11/upper6 windows remain. Reused graphs/sampler labels are not independent new realizations; G1ascending/G2descending confounds graph and size order. A fitted NlogN label neither proves a superlinear algorithm nor establishes observed linear runtime.

Machine: native Apple M3Max128GiB/macOS26.6.2/AppleClang15,C++17O3,assertions,512MiBstack. Six position-balanced timed repetitions plus warmups; graph generation and independent certification outside solver intervals. No points trimmed or control-drift correction. Two or four realization cells are not confidence intervals. Sleep inhibition was attempted but not verified; clean power association is not proof of an undisturbed CPU.

Say “the six assessed implementations,” not “all MST algorithms.” I-Max-Filter/Filter-Kruskal and other engineering are outside the six-way test. Sampling-rate balancing is also not novel: Katriel–Sanders–Träff2003 studied a different I-Max-Filter with `p≈sqrt(n/m)`; do not claim first discovery of smaller samples.
