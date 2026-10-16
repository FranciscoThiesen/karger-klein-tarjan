# Read-only native call-boundary inspection plan

Historical preparation instructions only; no disassembly executed by this agent.
Root subsequently completed bounded object inspection at
`benchmark/results/scaling-investigation-2026-10-15/depth-codegen01`; its actual
evidence and design-agent review are described in
`docs/scaling-investigation/depth-codegen.md`. That evidence supersedes this
unexecuted plan. This note makes no independent instruction-level finding.

For the original proposed inspection, inspect the
actual final `depth-reference` and `depth_noinline-reference` objects/binaries
from the checked `depth-build01/build.json`, retaining their recorded hashes.

Use the same Apple toolchain's `nm -C` and `otool -tvV` (or an available LLVM
objdump with its version recorded) on `verifier_v2.o` and the linked executable.
Archive commands, exit status and complete output before selecting excerpts.
Locate `verifier_detail::depth_lca::query_depth` and its callers inside the
Edge and tuple `test_graph::compute_heavy_marks` instantiations. The noinline
variant must contain an actual call to the named depth-query body in the query
gather loop. The default depth variant may inline it; absence of a standalone
symbol alone does not prove inlining, so examine the call sites and relocated
branch targets. Also locate the reference's calls to out-of-line `LCA::query`.

Check both overloads if their compiled bodies remain distinct. Compiler merging
or outlining can change symbol appearance. A call-boundary conclusion requires
resolved instruction evidence, not just source attributes or symbol counts.
The already checked object inventory should still show equality for every
non-verifier object. Do not infer that instruction counts are cycle costs or
that the noinline comparison isolates every compiler optimization: it tests
the actual query-call boundary and its downstream code-generation effects.
