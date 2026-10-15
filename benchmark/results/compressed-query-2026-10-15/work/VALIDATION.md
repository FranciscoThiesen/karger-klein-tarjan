# Cumulative work collector preparation

The owner-run mocked suite passed all **11 groups** on attempt 01, with exit 0.
It launches no native solver. The exact invocation, Python version, before/after
source hashes, stdout/stderr hashes and status are archived in
[tests-attempt01.json](tests-attempt01.json), with separate
[invocation](tests-attempt01.invocation.json), [stdout](tests-attempt01.stdout)
and [test log](tests-attempt01.stderr). All source hashes were unchanged during
execution. The wrapper process exited; no owned background process remained.

| Source | SHA-256 |
|---|---|
| `collect.py` | `6bba53051d5ce6565b6eaff43a9118f20d4eeb5491ac25686e2707c50233fda1` |
| `test_collect.py` | `d18dc5da283f2ccc77f9779eec2b42664d972e259a39d10e5abb8fde3e7cb8f4` |
| `PROTOCOL.md` | `cb646f8f2558371480990098b31b9625f513151ae19cee58b6b29e77fd258b77` |

Independent reviewer `/root/experiment_design` returned **source-review PASS**
for these exact hashes. The review checked the 36-command/nine-target build
proof, seven shared production objects and fixed scalar KKT, complete 24-child
timing-fingerprint schedule, all 65 fields, 61 equality checks and four exact
identities, correct cumulative U scope, 72/780/12 output counts, zero handling,
and bounded deadline/RSS/poison/cleanup/empty-group behavior. The reviewer did
not import, test or execute the collector or any native binary.

The owner tests cover complete mocked capture/reload/summary, every expected
pair/field identity, Q/U boundaries and wrong dispatch, all four algebraic
changes, unchanged-field violations, actual existing build artifacts and
mutation rejection, extra compile/flag/role changes, malformed JSON/schema/
certificate/fingerprints, comparator drift, late exits including consistent
reload metadata, RSS corruption, poison, unknown exit, overwrite protection
and refusal to launch another child after failure.

At the preparation checkpoint, native diagnostic capture was **unexecuted**. Its freeze required the
completed compressed-query timing capture and strict parent validation; native
execution required root's separate post-timing release. No timing helper,
native source or driver was edited. This receipt validates collector preparation,
not any numerical work result or performance claim.

After that separate release, [capture attempt 01](capture-attempt01-execution.json)
passed all 24 children and 72 certified solver outputs. All native groups and
the collector group were observed empty. [Strict analysis and independent raw
reconstruction](analysis-attempt01-execution.json) checked all 12 query pairs,
all 780 field comparisons, and both comparators' complete records and round
sequences. The [diagnostic report](analysis-attempt01/README.md) retains all 65
fields, including increased verifier vertex work. These are logical counters,
not performance or peak-memory measurements.
