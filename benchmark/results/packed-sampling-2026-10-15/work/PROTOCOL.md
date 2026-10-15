# Prospective packed-sampling work-counter matrix

Source preparation only during the performance capture. Do not import, test,
freeze, or execute this collector until root releases nonperformance work.
The native driver, objects, binaries, receipts, and frozen timing helpers are
unchanged. The already completed eight small smoke runs are separate evidence.

The diagnostic matrix is fixed now: all six cases from the timing manifest,
graph seeds 7000003 and 7000017, sampling seeds 1601 and 1613, and both scalar
and packed variants. Reuse the exact 48-child timing schedule. Every child runs
KKT, compacting Boruvka, and retained-edge multigraph Boruvka once, producing
144 certified solver outputs plus the existing two independent contraction
round replays per child. Include every case and seed, regardless of timings,
counter increases, or zero-valued counters. This is not another timing study.

Before diagnostic launch, strict-load the completed timing capture and freeze
its hashes, exact schedule and per-child graph fingerprints together with this
declaration, collector source, unchanged work driver, existing instrumented
build receipts, objects, binaries, and build logs. Each diagnostic input must
match its timing input's weighted and topology fingerprints. The unchanged
driver independently certifies the reference MST and requires exact ID-set
equality from all three solvers; the collector verifies that certificate and
the driver's successful output. No hash is substituted for native exact MST
comparison. No new native code or instrumentation is added.

The instrumented provenance check reconstructs the entire native-correctness
compile/link sequence in order, rejecting extra commands that could overwrite
a protected object. Both variants must share the same seven non-KKT object
paths and hashes, while their KKT object hashes must differ. The diagnostic
driver compile and both links are checked as an exact sequence too.

Retain all 65 existing KKT work fields. KKT recursive work may differ between
variants and sampling seeds. For a fixed case and graph seed, every compacting
and multigraph Boruvka counter and replay round must be identical across both
variants and both sampling seeds. Their uninstrumented final hash-insert count
remains `null`, explicitly unmeasured. Verify replay aggregates and the common
first two retained-edge contraction dimensions against KKT's root counters.

The WorkStats boundary includes public tuple-to-Edge input construction, the
solver and temporary input destruction. Reference generation/certification,
exact output checking, and independent round replays are outside that scope.
Counts are logical events, not instruction counts, bytes moved, elapsed time,
or proof of a runtime regression. Existing counters do not measure vector
reallocation or implicit edge relocation. No process duration is benchmark data.

Let M=`sampling_edge_visits` and C=`sampling_calls` for one KKT invocation.
The scalar stream uses exactly M engine words. Packed sampling uses
W=sum_i ceil(m_i/32), where the m_i are individual recursive sample input
sizes. The aggregate counters do not reveal those m_i. Report only the bounds

```
ceil(M/32) <= W <= min(M, floor((M + 31*C)/32)).
```

These bounds also hold with empty calls; when M=0 both bounds are zero. Never
report M/32 as an observed exact packed count. Candidate and scalar M may
differ because their recursive samples differ. There is no added per-call
engine observer in this experiment.

Use the unchanged bounded owned-group monitor: sampled 40 GiB RSS ceiling,
two-second polling, stop after three unavailable samples or immediately on
sampler poison, bounded TERM/KILL cleanup, and verified empty group before
the next launch. Each diagnostic child additionally has a 1,800-second deadline.
The deadline ends at the observed native exit: a successful return from a
bounded wait is checked immediately, and strict reanalysis checks it again.
Post-exit resource verification and output validation do not extend that budget.
Keep failed partials and forbid overwrite. Native capture requires `--released`.
No diagnostic runs may overlap performance timing.

After capture, strict reanalysis rereads all hashes, native certificates, exact
48-child schedule, fingerprints, resource evidence, and final empty groups.
Export all 144 solver work rows, all replay rounds, all 24 paired KKT records
for every one of the 65 fields, and 48 engine-word bound rows. Undefined ratios
with a zero scalar denominator remain explicit; zero rows are never dropped.
Any failure stops the matrix rather than replacing an input or relaxing a gate.

`test_collect.py` is prepared source, not executed validation. After release,
run `python3 -B benchmark/results/packed-sampling-2026-10-15/work/test_collect.py`
and preserve the first result. Its mocked gates cover the complete matrix and
zero-valued summaries, malformed JSON/schema/counters/certificates, comparator
drift, late exits during capture and reload, malformed RSS, resource failures,
unknown owned-group exit, sampler poison, source drift, exact build recipes,
and aggregate engine-word bounds. No native process is launched by those tests.
