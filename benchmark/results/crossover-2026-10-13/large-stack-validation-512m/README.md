# Unchanged classical baseline with an explicit stack reservation

Validation passed. The new executable is
`bin/large_stack/crossover_baselines`; the original executable, all production
sources and all existing object files remain unchanged. This is an execution
resource change, not an iterative-DFS repair or a performance result.

The [original adjunct attempt](../classical_timing.json) failed during the
original Borůvka warmup on the one-million-vertex hierarchical path. LLDB
identified the recursive selected-forest traversal at a stack store. The
algorithm rebuilds component labels using a recursive `std::function` DFS.
After completing a path MST it performs another component-labeling iteration,
so the selected path eventually produces linear recursion depth. The original
Mach-O `LC_MAIN` stack size is zero, selecting the platform's default; Apple's
installed linker manual documents an 8 MiB default main-thread stack.

The requested 1 GiB stack relink was rejected by the linker, which reports a
512 MiB maximum on this arm64 platform. Its [failed build and provenance](../large-stack-validation/provenance.json)
are retained. The supported reservation uses
`-Wl,-stack_size,0x20000000` with the existing Make compilation/link flags and
the same production object files.

| Check | Result |
|---|---|
| Recursive callable frame in existing `boruvka.o` | 64 bytes; no dynamic stack allocation in that callable |
| Worst path DFS depth tested | 4,194,304 active levels |
| Depth × recursive frame size | 268,435,456 bytes (256 MiB), plus fixed caller frames |
| New `LC_MAIN` stack reservation | 536,870,912 bytes (512 MiB) |
| Entire executable `__TEXT,__text` | 104,080 bytes, byte-identical to original |
| Exact original path tuples returned | All 4,194,303, once each |
| Checked 64-bit total path weight | 8,796,090,925,056 |
| Original source/object/binary hashes after validation | Unchanged |

The identical executable-code section has SHA-256
`96dd3569a2e3d06364166178bb1f16f5c47fd357d309bfc8813763b349b17b17`.
The complete binary hashes differ because the stack load command, UUID/signature
and related executable metadata differ. Both hashes and exact commands are in
[provenance.json](provenance.json); the new load command is retained in
[large_stack_load_commands.stdout](large_stack_load_commands.stdout).

The [temporary correctness test](worst_depth_path.cpp.txt) is a connected path
rooted at endpoint zero, with distinct weights increasing along the path.
Every path edge is selected immediately; the following DFS reaches all
4,194,304 vertices before unwinding. It links the existing production
`boruvka.o`, checks every returned ID, endpoint and weight against the original
tuple, rejects duplicates, and checks the total in 64-bit arithmetic. Because
the connected input is itself a tree, its only spanning tree is an independent
exact MST oracle. The test does not invoke an alternate Borůvka implementation.
See [result](worst_path_run.stdout), [operational resource log](worst_path_run.stderr)
and [recursive disassembly](recursive_frame.txt).

This establishes stack headroom for the planned adjunct's maximum of four
million vertices with this compiled recursive body. It does not authorize an
eight-million-vertex path: 64 bytes per level would already consume the full
512 MiB reservation before caller frames. A future larger bound requires a
separate safety decision or implementation repair.

The full three-case, four-algorithm adjunct must be run afresh under the same
512 MiB-stack executable/profile for every algorithm, retaining the failed
default-stack capture. The original failure is not a KKT timing win. Absolute
times from this executable must not be pooled with the two-algorithm screen
as if they were paired observations. A future iterative DFS repair would be a
separate source change with its own correctness and benchmark evidence.

The archived [validation driver](validation_driver.py.txt) records the exact
temporary build/run procedure. It was executed from `/tmp`, not this archive;
copy it to a new temporary directory and choose fresh artifact/output paths
before reproducing it. The temporary test source and binary were created
outside the repository. No graph-view export or fresh timed capture was run
as part of this validation.
