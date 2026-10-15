# Independent audit preparation: source review

Reviewer: `/root/multigraph_design`. Source-only review during the isolated
Google Benchmark capture; no import, test, graph generation, native execution,
hash walk, or partial timing inspection was performed.

Reviewed `independent_numerical_audit.py`, `test_independent_numerical_audit.py`
and `INDEPENDENT_AUDIT_PREPARATION.md`, including their source differences from
the completed density-32 distance audit. **No source blocker found.**

The independent literal matrix retains seven density-16 sizes and eight
density-8 sizes, both weight twins and two fresh graph seeds, with the complete
second-graph schedule reversed. Counts agree: 60 children, 2,520 outputs (2,160
timed and 360 warmups), 3,600 exact paired clock ratios, 1,980 summary medians,
30 topology twins, and 150 / 490 / 20 point / endpoint / crossover records.
Case IDs carry density; crossover grouping and table identity keys also retain
it explicitly. No cross-density pooling or bracket is introduced.

Ratios, medians and threshold predicates are rebuilt with `Fraction` from raw
integer durations without collector imports. The exact threshold is inclusive
at 0.90, the lower endpoint must strictly lose on both graph seeds and clocks,
and every later measured point within the same density must remain strong.
The six prepared test groups independently enumerate raw identities and cover
density isolation, sustained/late/recovered leads, reversals, ties, threshold
equality, one-clock epsilon and one-graph failures. Raw value/identity/certificate
negatives update surrounding hashes where needed, avoiding stale-hash-only
failures. The inherited artifact/resource/concatenation proof is retained.

The three declaration digests are deliberately `None` and are rejected before
an audit proceeds. Filling them from the final independently reviewed source,
protocol and manifest after release is a required deployment step. The real
prospective freeze path and SHA must also be supplied, not invented. This
review makes no current hash-binding or runtime-PASS claim; source pins,
installed-byte verification, six mocked gates and actual full-capture audit
remain pending under root's scheduling authority.
