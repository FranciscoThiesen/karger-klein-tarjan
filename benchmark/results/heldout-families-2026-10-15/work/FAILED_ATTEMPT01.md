# First diagnostic attempt: frontend rejection, preserved failure

`capture-attempt01.json` is **failed**, with two completed inputs out of72.
The next declared input, `grid2d_metric_n1024_d32_p0`, graph seed9000011 and
sampling seed2003, exited1 with the exact message `unsupported diagnostic family`.
Its raw JSON output is empty: the frontend rejected the family before graph
generation, certification or any solver call. This is not an observed MST,
counter or replay correctness failure.

The older, unchanged diagnostic driver accepts attachment fixtures or
`gnm_random`; its whitelist does not include the four line/grid families that
the timing harness already supports. Source/artifact hashes proved the intended
binary was executed, but did not establish coverage of every declared frontend
family. The nine mocks used synthetic raw outputs and therefore did not exercise
this native dispatch condition. Preparation should have included one actual
small native gate per declared family.

The failure audit rechecked both completed inputs and their certificates,
counter/round schemas and resource evidence, then checked the failed child's
actual exit and cleanup. The launched groups40384,40385,40386 and outer40383
were affirmatively empty in their original receipts and in a fresh bounded
process-table observation. `failure-audit-attempt01.json` records that proof.
The outer controller's conservative failed-status receipt remains unchanged;
the supplementary audit resolves group status without relabelling capture.

The separately authorized repair lives in `../work-spatial-v2/`. It copies the
driver and extends only the spatial-family whitelist, compiles one new main,
and links the same eight existing instrumented production objects. Before its
new freeze, all six families at n1024 and both declared graph seeds must pass
native certificate, fingerprint,65-counter and replay checks. Its eventual
capture reruns all72 inputs; neither old success is reused. No old protocol,
collector, freeze, driver or partial output was overwritten.

No aggregate diagnostic conclusion is drawn from this incomplete attempt.
Instrumented process durations are not algorithm performance measurements.
