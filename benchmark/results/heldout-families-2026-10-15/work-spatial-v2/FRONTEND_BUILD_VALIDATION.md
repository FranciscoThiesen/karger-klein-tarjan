# Spatial diagnostic frontend repair

The separate frontend build and all twelve small-family gates passed. The
repaired driver differs from the frozen diagnostic driver only by admitting
`line_metric`, `line_random`, `grid2d_metric` and `grid2d_random` to its existing
crossover-generator branch. The graph generators, three solvers, certificate,
counter boundary and independent round replays are unchanged.

Exactly two native commands compiled the new main and linked it to the eight
original compressed instrumented object files. No production object was rebuilt.
The original source/header inventory, complete frozen parent proof, compiler,
SDK, flags and object hashes were checked before and after the gates. The new
executable is arm64 with the original 512 MiB main stack.

The twelve inputs cover all six declared held-out families at n=1,024,
density 32, graph seeds 9000011/9000049 and sampling seed 2003. Each reproduces
the completed timing capture's weighted and topology fingerprints. The unchanged
checker validated 36 certified solver outputs, all 65 counter fields per solver
(including the explicitly unmeasured comparator hash-count nulls), and 24
complete contraction replay chains. This is a frontend coverage/correctness
gate, not a performance measurement or a replacement for the fresh full matrix.

The first attempt failed during linking, before any solver gate: the shell's
`LIBRARY_PATH=/usr/local/lib` selected an x86 libunwind for an arm64 link. Its
source snapshots and all evidence remain in [attempt01-sources](attempt01-sources/),
the original `build.log`, `owned-groups.json` and controller attempt01 files.
[The failure audit](build-failure-audit-attempt01.json) confirms the compile,
failed linker and outer groups all exited; the eight original objects stayed
unchanged. The second attempt used fresh build/bin/log/group paths and removed
only `CPATH` and `LIBRARY_PATH` from the two compiler-command environments,
recording both original values and the exact policy. Independent source review
approved that narrow correction.

Captured invocation:

```sh
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/run_build_attempt.py --released-small-gates
```

[Attempt02 receipt](build-controller-attempt02.json) records exit 0 and all
14 native groups plus outer group 41918 empty. The root tool session also exited
0. [Build record](build-record.json) SHA-256:
`2c93d8504ed4d984d0baa72cff502387f67d4fec9733ff264a650eca43eee365`.
[Gate receipt](frontend-gates.json) preserves every input and raw output.
`build_driver.check_record()` independently reloads all bindings without running
native code. No full diagnostic capture or performance run was launched here.
