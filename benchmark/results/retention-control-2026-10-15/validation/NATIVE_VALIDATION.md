# Six-solver native validation

The native and ASan/UBSan correctness gates passed the same **819 solver
outputs** across **28 simple-input fixtures** and **35 raw multigraph fixtures**.
The raw fixtures also passed **35 exhaustive minimum-forest checks**. The exact
harness result validator rejected **140 damaged tuple/ID results**, and the CLI
gate rejected **10 invalid repetition counts**. These are untimed correctness
checks: they call the solvers directly and do not execute the harness's
`measure()` function or produce performance rows.

- [Native gate result](native-correctness-final.json) and [log](native-correctness-final.log).
- [ASan/UBSan gate result](sanitizer-correctness.json) and [log](sanitizer-correctness.log),
  with leak detection and halt-on-error enabled; [sanitizer build](sanitizer-build.json)
  and [build log](sanitizer-build.log).
- [Native build record](native-build-record.json), including exact build argv,
  Apple Clang identity, SDK, native source/recipe/object hashes, binary hash and
  Mach-O load commands; [build log](native-build-final.log).
- [Source-preservation checks](source-preservation.json).

The initial gate tried a G(n,m) fixture with density two, outside that generator's
declared density-at-least-16 domain. It correctly rejected the fixture before
testing that case. The [failed result](native-correctness.json) and
[failed log](native-correctness.log) remain retained. The corrected gate uses
supported G(n,m) dimensions; neither generator nor validation was weakened.

The six solvers are candidate `kkt`, existing `compacting_boruvka`, new
`multigraph_boruvka`, `kruskal`, `prim`, and original `boruvka`. The new continuation
mirrors the existing compactor's selected-ID vector accumulation, quotient move,
reserved result hash set, and return type. Only its contraction call changes to
the same `kkt_experiment::retain_parallel_step` used by candidate KKT. All eight
production object files, including KKT, are byte-identical to the screened
candidate build. Existing tracked source files remain unchanged.

The parent agent independently reviewed the native source and approved its
timing boundaries before release. The three ID-set solvers include tuple-to-
`problem` conversion and temporary input destruction inside the steady-clock
interval. Their returned results, and those of the three tuple-returning
solvers, are validated and destroyed after the finish clocks. The independent
reference certificate and graph generation remain outside timing. Six timed
repetitions balance each solver across all six positions; one warmup produces
42 checked calls per native child. No performance conclusion follows from
these correctness gates.

Recorded binaries:

| Artifact | SHA-256 |
|---|---|
| Native six-solver harness | `4603d2a29ca9f924a5edb4be46a41f7314d150ee12f57d82fb1d404491f5c995` |
| Native correctness gate | `9eee301eeb350e36ef50c96f1beba01b4ca3eaa7646c0cf3a96bc37e586424a0` |
| Sanitizer correctness gate | `bfada0cacc5b1a37830b98262c754d4c6df9da9f80142f05e2f315031c410fc0` |

The native harness is arm64 with a 512 MiB main-thread stack. The source and
object identity claims are hash-bound in the linked records; they do not imply
identical final code addresses, allocation state, or runtime cache behavior.
