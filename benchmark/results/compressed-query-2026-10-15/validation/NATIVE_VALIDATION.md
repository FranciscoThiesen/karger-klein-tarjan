# Compressed-query native validation

All three profiles and the final-object gate passed on their first attempt. No implementation changes were needed. Timing and work-driver executables were built but never launched.

- Native Apple Clang 15 O3: 16 test executions across reference/compressed.
- Native Clang 22 ASan+UBSan, with leak detection enabled: the same 16 executions passed without sanitizer diagnostics.
- Each profile verified 1,344 paired full-KKT input fingerprints and exact sorted MST IDs; all 61 unchanged counters matched, all four changed-counter identities held, and 549 records witnessed reduced compressed-query work.
- Each focused binary checked 252 positional cases and seven malformed lookups. The unchanged direct verifier oracle checked 1,248 positional cases per variant. Both wrong-policy executions cleanly exited 1 in each profile, and passing the reference record stream as the candidate was rejected.
- Other gates included multigraph contraction, regression, independent contraction, simple graphs, core-attachment structure and the independent MST certificate. Detailed counts are preserved in their stdout files.
- The final uninstrumented object sets passed the unchanged six-solver harness separately: each reported 28 simple cases, 819 solver outputs, 35 raw/exhaustive cases, 140 rejected trees and 10 rejected options.
- All 122 owned process groups across correctness, builds and final-object validation were verified empty before advancement. No unknown exit remained.

Both timing binaries are native arm64 with a 512 MiB main stack and use fixed scalar sampling. They share seven physical production objects, including `kkt.o`, and the harness main. Only `verifier_v2.o` differs. The reference verifier translation unit is textually restored to the frozen parent by the source-contract gate. Counter observations prove input/result identity and the declared cumulative work identities; they do not directly observe intermediate sampled forest contents.

Reference SHA256: `86548fdd4a87a6627811db322ebb30ea07a7103e565226a2c04acd34ca88a688`.

Compressed SHA256: `74e604830c4c730395cd6c9e9dc61287a6d88a34cc89983bb4ee61dc3272a1b2`.

`native-validation-summary.json` binds the detailed receipts, source inventory and build records. Every profile also retains its `*-controller-attempt01.json`, controller log, build log, command records, stdout/stderr and bounded owned-group evidence. These are correctness/build results, not a speedup or memory-use measurement. Prospective performance capture still requires the root's freeze and release.
