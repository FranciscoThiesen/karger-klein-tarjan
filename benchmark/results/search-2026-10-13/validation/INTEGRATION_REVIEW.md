# Deferred attachment integration review

Source-only review during the frozen density pilot. No draft was compiled,
imported, executed or benchmarked. No repository capture helper, C++ source or
Makefile was changed. The checks below describe reviewed code and pending
integration gates, not successful native test outcomes.

## Findings

No concrete fixture, pairing, counter-scope or timing-boundary defect was found
in the reviewed drafts. A temporary `mst_search.cpp` copy now adds only the
attachment include, the two fixture dispatch branches, and accurate help.
Native timing integration and build validation remain pending until the
existing captures finish. `MAKEFILE_NOTES.md` describes the deferred dependency
and native/instrumented test/export targets; the current `measure()` and
certificate paths remain unchanged in the temporary copy.

## Reviewed contracts

* **Count domain:** for `b=4/16`, `q=n/b`, local edges are `n-q` and external
  edges are `E=nd-n+q=q[b(d-1)+1]`. The independent Python/native checks agree
  on `q-1 <= E <= q(q-1)/2` and the global size/density/edge/sentinel caps.
  The upper bound is equivalently `q >= 2b(d-1)+3`; no complete-bundle division
  or divisibility correction belongs in this family. Rejection precedes graph
  allocation. Nonallocating tests include the exact global edge cap.
* **Sixteen families:** both endpoint modes and both block sizes support
  hierarchy, distance, core-only shuffled, and global-random weights. The
  shuffled branch places every external edge in one shuffled core tier while
  preserving the exact cheap local prefix. The random branch subsequently
  permutes every expanded edge rank. Only hierarchy/distance claim later
  dyadic partitions; shuffled asserts the first star collapse only.
* **Paired inputs:** separate topology, endpoint, weight, label and order streams
  preserve topology/IDs/input order within each endpoint mode and block size.
  Python fingerprint groups reflect precisely that boundary. Leaf/community
  topology fingerprints may differ; those cases are not incorrectly forced
  into one topology group. The native test independently checks projected
  core endpoints, identical per-ID weights and physical ID order, then exact
  selected vectors and physical quotient vectors for cheap-star twins.
* **Historical compatibility:** the new header appears in `NATIVE_FILES` but
  is mandatory only if an attachment family occurs in the loaded manifest.
  Old pilot inventories can therefore be reanalyzed without inventing a hash
  for a header that did not exist. Existing path/tree/lifted/geometric pairing
  groups and the six-helper hash registry are unchanged. The new self-test
  source explicitly exercises old-inventory compatibility.
* **Independent correctness:** fixture tests reconstruct labels and simple
  edges, check dense IDs and rank permutations, compare sorted-incidence
  minima against a small vertex-by-edge oracle, and use a separate DSU/map
  for the complete quotient. Selected original IDs reconstruct component
  partitions. Hierarchy has a separate star/path MST oracle; distance has a
  separate minimum-per-dyadic-cut oracle. The cycle certificate checks every
  solver, including Kruskal itself, rather than trusting the reference name.
  The source expects 176 fixtures and 1,232 certified solver outputs; these
  counts have not yet been observed. Instrumented endpoint checks expect
  24 all-field counter pairs.
* **Untimed work:** `search_work.cpp` has no timers. Graph generation,
  reference construction/certification, result checking and original-component
  ledger reconstruction are outside the counter scopes. KKT and compactor
  both count tuple conversion and temporary input destruction. The compactor
  trace independently crosschecks every input/output volume, while the KKT
  root-after-two dimensions must match its first two production contractions.
  Trace allocation is auxiliary diagnostic storage, not counted algorithmic
  work and never a performance observation.

## Required integration gates after timing stops

1. Add only attachment include/dispatch/help/build dependencies to the native
   search harness. Preserve the five algorithm bodies and rotation exactly.
   Solvers must receive the expanded original edge list, not `core_graph` or
   a precontracted quotient.
2. Preserve the present fair API boundary: KKT/compactor tuple conversion and
   temporary input destruction are inside timing; native classical calls are
   timed directly; all returned-result destruction and validation are outside.
   No result-type conversion or fixture-aware shortcut should be introduced.
3. Keep Kruskal reference construction plus the independent cycle certificate
   before timing. Retain the same input-bound certificate marker and exact
   ID checks; tuple-returning solvers additionally need original endpoint/cost
   membership. The existing certificate validates simple connected inputs and
   distinct positive weights before the timing harness indexes its dense IDs.
4. Run the deferred Python self-test and both native fixture configurations,
   then a tiny full wrapper/analyzer capture for representative new modes.
   Compare old fixture fingerprints and old solver source/code provenance.
   Reanalyze both completed old pilots with the new parser to verify backward
   compatibility using actual evidence, not only the synthetic source checks.
5. Freeze the new C++/Make/helper/binary inventory and manifest before a new
   campaign. Keep all five contemporary solvers, order balance, warmups,
   resource observations, power/clock flags, and losing observations. The
   source review alone establishes no speedup or crossover.
