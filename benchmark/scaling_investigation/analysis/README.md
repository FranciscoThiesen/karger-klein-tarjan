# Matched-input diagnostic analysis

This consumes **completed** phase/work/allocation/calibration captures from
`../run.py`. It launches no native processes and changes no captures. Build,
source, object, binary, receipt and raw-output hashes must all verify. Case joins
include family, n, m, graph seed, sampling seed and both fingerprints. The exact
historical Google native rows are independently reread before timing/count joins.

```sh
/usr/bin/python3 -B benchmark/scaling_investigation/analysis/analyze_diagnostics.py \
  --phase benchmark/results/scaling-investigation-2026-10-15/phase01 \
  --work benchmark/results/scaling-investigation-2026-10-15/work01 \
  --allocation benchmark/results/scaling-investigation-2026-10-15/allocation01 \
  --calibration benchmark/results/scaling-investigation-2026-10-15/calibration01 \
  --build /absolute/path/to/completed/build-directory --output /tmp/kkt-diagnostics-new
```

An optional `--MODE-build PATH` overrides the common build for that mode; source
inventories and base flags must remain identical. The three diagnostic builds
are not comparable uninstrumented performance campaigns. The calibration table
reports both matched-repetition phase/reference ratios and ratios of medians,
without assuming they are the same statistic or applying an overhead correction.

All per-case summary plots use medians and full ranges, retaining every graph and
sampler. Endpoint phase contribution uses **arithmetic means**, without trimming,
so exclusive phase plus outside-collector differences sum exactly to the total
endpoint difference. Median total differences are retained alongside it. The
outside bucket is measured wall minus the sum of exclusive phase clocks; it is
not assigned to a particular operation.

Allocation requested/usable bytes are cumulative bytes allocated in the solver
scope. Only peak/returned **usable** bytes are live-byte measures. These are
instrumented C++ new/delete allocations, not RSS, not all libc allocations, and
not live requested bytes. Allocation-build phase clocks are kept separate from
the phase-only clocks.

Phase-time/count denominators are explicit named logical events. They are not
CPU instructions, hardware-cache misses, or exhaustive costs. In particular,
path-walk normalization uses visits + unique requests + binary-search steps,
where unique requests = path_query_visits − 2×verifier_queries. Add-request and
lookup counters occur outside path_walk and must not be charged to its traversal.
Undefined zero-denominator ratios remain empty with status `zero_denominator`.
All65 counters are exported; figures select declared fields without dropping
any other evidence. Historical Google CPU/count ratios refer to old native CPU
measurements and new exact-input work counts, never to work-build runtime.

Count-space fits independently apply Google's zero-intercept coefficient and
normalized-RMS formula to N and NlogN over the six selected sizes, for kkt_edges,
contraction_edge_visits, verifier_queries, path_binary_search_steps,
lca_sparse_cells, initialized_slots and edge_materializations. This is numerical
count-space reanalysis, not an invocation of Google Benchmark and not an
instruction count. Zero means/denominators remain explicit undefined results.

After a candidate changes native sources, pass `--source-snapshot PATH` with the
explicit `kkt_scaling_source_snapshot_v1` manifest. The analyzer pins the previously
verified build04 record and its complete 46-source inventory, checks every copied
source against its old digest, and records original-to-copy aliases. Only source
paths are redirected: existing binaries, objects, raw outputs and command receipts
must still verify at their original locations. The live row-validator Python
helpers and counter-schema header must remain byte-identical. This preserves the
baseline evidence; it does not certify a new implementation or reuse old timing as
a fresh candidate comparison. The historical CPU/count table includes the union
of all declared figure and fit counters (13 fields including the proxy).

Source/test preparation is separate from runtime acceptance. A passing result
requires all four completed capture matrices and strict artifact rechecks.
