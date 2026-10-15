# Scalar half versus eighth sampling: preparation only

This package is **source-only and unexecuted**. No collector import, test,
installation, build, preflight, freeze or timing is claimed. The separate
larger-hierarchy capture has priority; root owns every later release. No
partial timing was read to choose this design.

The [protocol](PROTOCOL.md) and [manifest](manifest.csv) declare fresh `half`
and `eighth` binaries with compressed queries fixed, one RNG draw per edge,
the same `reserve(m/2)`, unchanged public sampling and all five controls.
Only the private all-ones acceptance mask changes from 1 to 7. There are six
cases, two graph seeds and two sampling seeds: 48 children / 2,016 outputs,
4,608 paired clock ratios, 3,024 summary medians and 30 exact endpoint
classifications. The same-seed recursive forests may differ; no speedup is
assumed and no historical timing is pooled.

Prepared collector and synthetic tests are `benchmark/run_eighth_sampling.py`
and `benchmark/test_eighth_sampling.py`. They retain the full compressed
parent proof, twelve exact build commands, seven shared non-KKT objects and
shared harness, local seed validation, bounded resource/cleanup evidence,
strict reload and independent Cartesian/Fraction test oracles. Source hashes
do not substitute for later correctness validation. **No test has run.**

Before timing, install the reviewed overlay in a separate worktree; execute
and archive native/sanitizer/final-object and controller gates; recheck source
declarations and private-log exclusions; freeze and commit exact artifacts;
then obtain root's quiet release. Preserve every failed attempt. Independent
raw audit and actual plots will need separate post-capture work.
