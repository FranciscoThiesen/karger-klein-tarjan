# Work figure checks

The three actual PNGs were opened and inspected: `contraction_volume.png`,
`edge_materializations.png` and `verifier_incidences.png`. All ten case labels,
vertex counts, legends, bar values and explanatory captions are readable, with
no clipping or overlap. Each figure retains the same declared case order.
PNG, SVG and PDF versions share the same figure objects; visual inspection
was of the PNGs.

Contraction and materialization figures compare the same logical counter for
both algorithms, divided by each graph's original edge count. The verifier
figure stacks two parts of one counter: retained F-light and removed F-heavy
incidences. Its caption states that these are recursive incidences, not unique
original edges. All figures identify their untimed, one-graph/one-sampling-seed
scope and avoid runtime, byte-volume or uncertainty claims.

An independent direct lookup against `diagnostics_work.csv` checked all **70
figure points**, seven per case, including numerator and original-m denominator.
See [figure_data_checks.json](figure_data_checks.json). No point was omitted.

The complete strict diagnostic baseline passed with 20 work rows, ten traces,
124 recorded rounds and 134 derived stages including stage zero. The complete
renderer baseline also passed. Twenty-four semantic/provenance mutations were
rejected, including missing/duplicate rows, invalid counters, broken trace
chaining, root/trace disagreement, inconsistent moments, altered frozen source
and binary identities, normalization errors and mismatched singleton summaries.
For renderer CSV mutations, the test deliberately recomputed the declared
hashes so rejection depended on semantic checks rather than stale hashes.

The [validation results](../diagnostics-analysis/validation_checks.json) and
[check source](../diagnostics-analysis/validation_checks.py.txt) are archived.
Tests changed only temporary copies or in-memory records. Raw evidence was
unchanged, and no native executable was run. Source review and whitespace
checks found no remaining issue.
