# Lower-density KKT crossover study

Prospective status, 15 October 2026: source installation, independent source
reviews and all 47 mocked groups passed. No native timing or counter result
has been collected for this study. The mocked checks are 23 timing groups,
four paper-plot groups, and 20 work-companion groups; they are not benchmark
results or new native correctness cases.

The [fixed protocol](PROTOCOL.md) declares distance-ranked and shuffled twins
at densities 16 and 8, respectively seven and eight sizes, with fresh graph
seeds 23000003/23000029 and sampler 3407. All six solvers use the unchanged
eighth-sampling executable. The complete schedule has 60 children and 2,520
certified outputs. Every loss, range and density-specific crossover outcome
will be retained. The largest inputs have 33,554,432 edges; the density-eight
ladder reaches 4,194,304 vertices.

Installation, pinning, actual wrapper exits and empty-group observations are
archived under [validation](validation/). The timing/paper gate summary is
[owner-gates-attempt01.json](validation/owner-gates-attempt01.json); the separate
counter companion has [20 passing mocked groups](validation/WORK_MOCK_VALIDATION.md).
The three timing declaration hashes are pinned in the independent audit, with
the original unpinned file and exact change preserved.

The timing source must be committed and its full inherited binary/source proof
frozen and reloaded before a separate quiet capture. The work companion may
only be frozen after the complete timing matrix and independent numerical
audit pass. Its instrumented durations will not be used as performance data.
The [execution checklist](validation/source-preparation/work/POST_GOOGLE_CHECKLIST.md)
records the preparation sequence; source-preparation notes retain their
historical pending status rather than impersonating execution receipts.

Sleep inhibition is not verified. Raw machine power history stays local;
successful log queries cannot establish stable thermals or an idle host.
