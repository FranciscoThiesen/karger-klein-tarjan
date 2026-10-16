# Depth-query correctness execution

The source-only runner is prepared for root execution after the candidate build completes. It has not been imported or executed by its author. It does not modify production sources or the candidate protocol.

From the worktree root, using a fresh output directory:

```sh
/usr/bin/python3 -B benchmark/scaling_investigation/candidates/run_correctness.py \
  benchmark/results/scaling-investigation-2026-10-15/depth-correctness01 \
  --build .build/scaling-investigation/depth-build01/build.json --released
```

The successful `gate.json` has schema `kkt_depth_correctness_gate_v1`, the exact candidate build's `source_sha256`, and a separate `bound_sha256` inventory that includes this runner, compilers, the two existing full-solver tests, included harness, commands, logs, receipts, objects and binaries. The candidate loader accepts it as the correctness prerequisite alongside the separate work and smoke captures. Failed attempts must remain intact; retry with a new directory.

The focused positive link uses four source files: generic LCA, reference verifier, renamed depth verifier and `depth_queries_test.cpp`. The depth verifier alone receives all four symbol renames documented in `DEPTH_QUERIES_PREPARATION.md`; the test receives none. Both verifier objects' defined symbols are archived and checked. A separate native wrong-dispatch object uses those renames without the depth macro; its test must exit exactly 1 with `depth dispatch / exact removed-height initialization mismatch`. All four native guard modes must exit by SIGABRT with their corresponding assertion expression/function/header in stderr. Arbitrary failure, timeout, unknown group or sanitizer crash never counts as a passed negative gate.

The native edge-view suite reuses the exact eight `depth-work` objects. The retention suite includes the timing-only harness and therefore reuses the eight **uninstrumented** `depth-reference` objects, with an uninstrumented main. The sanitizer profile rebuilds two separate eight-object sets with matching Homebrew LLVM, ASan+UBSan, assertions enabled, `-O1 -g`, frame pointers and nonrecovering sanitizers: work counters on for edge-view, off for retention. Only the instrumented LCA object is shared with the focused sanitizer link. This prevents mixed inline definitions across instrumented and uninstrumented TUs. Both profiles retain the four existing optimized flags, same SDK and 512 MiB stack. The depth macro is absent from the focused reference verifier. This gate tests the default inline depth policy; the noinline control remains a provenance-bound compiler attribute experiment.

Each profile runs the focused parent-walk/forest-path differential oracle, `edge_verifier_view_test` (1,248 positional cases and exactly 1,344 full-KKT identities) and `retention_control_test` (28 simple cases, 35 raw/exhaustive cases, 819 solver outputs and its existing rejection gates). Native and sanitizer records and summary output must match exactly. Helper loops/repeated IDs do not broaden the full solver's valid-input contract. The separate candidate work campaign remains responsible for exact historical RNG/selected-ID/all-65-field replay and the initialization delta on the diagnostic inputs.

All children use the unchanged bounded owner. Compiles have 180-second/4-GiB limits, links 60 seconds, and tests 300 seconds/12 GiB; helper metadata commands have 30-second limits. The 3,600-second overall ceiling is a ceiling, not a predicted duration. Source/artifact checks bracket children and final acceptance. `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1` are explicit; this is not a LeakSanitizer gate. The caller's options are restored. An expected nonzero child is accepted only after the exact recorded exit, error cause, deadline, resource and empty-group proof have been checked.

Root's attempt01 stopped at the retention main's deliberate timing-only compile guard. Its focused native positive, four assertion guards, wrong-dispatch rejection and edge-view suite had completed; this partial success is not the full gate. Original runner/doc/review bytes remain in `depth-correctness01/runner-repair-before/`. The repair separates whole-object instrumentation as described above. Use a fresh `depth-correctness02` output directory; do not resume or overwrite attempt01.
