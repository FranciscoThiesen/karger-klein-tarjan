# Classical adjunct analysis checks

Both rendered PNGs (`classical_wall.png` and `classical_cpu.png`) were opened
and visually inspected. Titles, case sizes, logarithmic seconds axes, algorithm
labels and range whiskers are readable, without clipping or overlap. The caption
identifies the one-graph, four-repetition scope, the common 512 MiB stack profile,
and the distinction between original Borůvka and compacting Borůvka. Observed
trial ranges are explicitly not confidence intervals. PNG, SVG and PDF versions
use the same figure objects; visual inspection was of the PNG versions.

The analyzer accepted all 48 timed calls and 12 warmups, with no clock flags.
It checked the complete per-case schedules, selected discovery fingerprints,
raw CSV/log hashes, combined CSV ordering, stored clock diagnostics and medians,
and the archived large-stack validation. It retains every timed observation and
warmup. No compacting-Borůvka timing is imported.

A complete temporary copy passed. Twelve malformed copies were rejected:
boolean repetitions, an incorrect completed count, a different binary hash,
an altered log hash, an incomplete combined CSV, an invalid enclosing UTC
interval, an incorrect stored median, altered clock diagnostics, a missing
warmup, an incorrect algorithm order, inconsistent CPU arithmetic, and a
different input fingerprint. These checks modified only temporary copies;
the raw capture and archive were unchanged. See
[validation_checks.json](validation_checks.json) and its
[check source](validation_checks.py.txt). No native process was started.

KKT lost all four timed repetitions to Kruskal and original Borůvka on each
selected case, while beating Prim in all four. Both wall and CPU tables retain
those outcomes. These selected single-graph observations do not establish a
general algorithm ranking or a crossover.
