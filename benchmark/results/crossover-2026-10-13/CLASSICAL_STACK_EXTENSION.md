# Retained classical failure and stack-profile extension

The first predeclared classical capture (`classical_timing.csv/.json` and
`classical_timing_cases/`) failed with SIGSEGV on the hierarchical path at
n=1,048,576 during warmups. The native child buffered its CSV until the end of
a four-algorithm block, so its retained raw CSV is empty. It is not a successful
timing campaign. The wrapper retained the failure, source hashes and log.

An LLDB reproduction (`classical_crash_lldb.log`) shows checked KKT, Kruskal
and Prim warmups followed by EXC_BAD_ACCESS in original Boruvka's recursive
selected-forest traversal, on a stack store. Debugger observations are diagnostic
only, never performance samples. This baseline recursively traverses a path of
linear depth, including a final pass over the completed tree. The default
main-thread stack is about 8 MiB. The compacting baseline uses different code;
all three completed KKT/compactor screens remain unaffected.

Before collecting any replacement observations, validate a separate executable
linked with an explicit 1 GiB main-thread stack reservation using Apple's
`-Wl,-stack_size,0x40000000`. Preserve original solver sources, compiler flags,
objects, public result types and timing boundaries. Verify the Mach-O stack
size, compare executable instruction-section hashes, and run a worst-depth
4,194,304-vertex path through the unchanged original Boruvka implementation.
Keep the original binary and failed capture. The larger virtual stack is a
resource-profile change, not a solver optimization or extra physical-memory
allowance; retain the existing approximately 40 GiB observed-footprint limit.

Only if those checks succeed, run the ENTIRE same three-case, four-algorithm
adjunct again, with identical seeds, warmups and rotated repetitions, to
`classical_large_stack_timing.csv` and separate metadata/logs. All algorithms
run under the same enlarged-stack executable. Label the new profile throughout,
retain the failed original attempt, and count neither the crash nor debugger
observations as a KKT timing win. This is separate from the frozen two-run
confirmation rule, for which no new candidate or capture was selected.

## Validated supported reservation, before the new timing capture

Apple's arm64 linker rejected 1 GiB because its supported maximum is 512 MiB;
the failed build is retained in `large-stack-validation/`. The separately
validated 512 MiB profile uses `-Wl,-stack_size,0x20000000` and is the profile
selected for the complete new adjunct. See
[validation provenance](large-stack-validation-512m/provenance.json).

The recursive lambda uses 64 bytes per active level. A 4,194,304-vertex path
therefore needs 256 MiB plus fixed caller frames. The supported 512 MiB reservation
passed the endpoint-rooted worst-depth path test with every original tuple and
64-bit total weight checked. Mach-O reports 536,870,912 bytes; the entire
`__TEXT,__text` section is byte-identical to the original executable. Sources,
objects and the original executable are unchanged. This result supersedes the
proposed 1 GiB value above, not the failed original capture.
