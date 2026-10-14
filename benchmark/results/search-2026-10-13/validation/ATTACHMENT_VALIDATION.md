# Attachment integration validation

The 80-case extension was declared before any attachment build or run. The original
53-case campaign finished first. Only benchmark fixtures, dispatch, analysis and
untimed diagnostics were added; `git diff` reports no production solver changes.

- Native Make build passed for normal/512 MiB harnesses, normal/work-counter
  fixture gates, untimed work driver and exporter. Compiler commands are in
  `attachment-build/build.log`; assertions remain enabled.
- Both fixture executables passed 176 fixtures, 1,197 independent full contraction
  stages, 1,060 sorted-incidence versus exhaustive minimum checks, 1,232 certified
  solver outputs, 66 exact endpoint-twin trajectories, 13 distance-MST chords,
  20 rejected dimensions and 32 allocation-free maximum-edge checks. The
  instrumented executable also passed 24 comparisons of every logical counter.
- Build/CLI audit passed 86 invalid-input rejections and both help checks.
  Normal and 512 MiB instruction sections are byte-identical; SHA-256
  `6d7e8593809309d49bade60e6d35b6948d36f5dfbc136e4504654aa6611f9a5b`.
  Full binary/source/object/helper hashes are in `attachment-build-validation/`.
- All sixteen integrated native families passed one checked warmup and five
  rotated repetitions: 400 timed outputs and 80 warmups. The strict analyzer
  accepted all 480 outputs and 640 wall/CPU pairs. These tiny integration timings
  are not used as performance evidence.
- Python capture/analyzer self-tests passed 12 positive checks and 39 rejected
  mutations. Updated readers also revalidated both complete older captures:
  840 lifted and 750 density calls. The frozen attachment manifest has 80 cases.
- Sixteen work dumps and sixteen graph exports passed. The Python viewer
  independently recertified all sixteen native exports and checked fingerprints,
  metadata and dimensions. Browser visual QA is still pending and is not claimed.
- Occupancy-model and renderer self-test details are retained in their JSON logs.
  A source review found a non-study oversized-domain issue in the occupancy
  helper; the accepted domain was bounded before exact-count shortcuts and
  regression checks passed. The model remains an expectation, not a timing fit.

Raw stdout/stderr, rejected inputs, build logs, and source reviews remain here.
The actual attachment timing campaign starts only after this validation and a
new source freeze. Its results are not pooled with the earlier binary profile.
