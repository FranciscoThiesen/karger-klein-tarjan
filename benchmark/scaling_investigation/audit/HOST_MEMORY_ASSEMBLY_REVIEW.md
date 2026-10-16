# Host calibration: actual assembly review

Independent source/disassembly review PASS for `host-memory-build01`. No compiler, probe, solver, or performance command was executed by this reviewer. Identity below is copied from the completed build and assembly receipts, rather than a fresh hash claim:

- Source: `host_memory.cpp`, SHA-256 `6f34d7deeba2ff7321592bd7eb91674fa7908351b72d27f560a673abaa2fcaa8`.
- Binary: `host-memory-build01/host_memory`, SHA-256 `effb3a4046c3de54b9c5a1587cdfdcafcfad949d0d6ba4d30135ed578b6d937f`.
- Reviewed `assembly.stdout`, SHA-256 `f706e53c7666e1e2176570fe012eddbd6d148b9a667ac6586bdd767470985030`, as bound by `assembly.json` and `attempt.json` in that build directory.

The one-chain loop at `0x1000033fc–0x100003408` performs one indexed 32-bit load into its own next index, one position store, and a decrement/branch. Its constant counter is `0x1000008` (16,777,224). The four-chain loop at `0x100003428–0x10000344c` has four independent index registers and four indexed loads/stores per iteration, with counter `0x400002` (4,194,306). The eight-chain loop at `0x100003474–0x1000034b8` similarly has eight independent index registers and eight indexed loads/stores per iteration, with counter `0x200001` (2,097,153). Thus all three retain exactly 16,777,224 logical indexed loads. Each individual chain remains dependent across iterations; different chains need not wait for one another's returned index.

The scan loop at `0x1000034e4–0x100003528` computes four masked consecutive indices, issues four scalar 32-bit loads (`0x100003500–0x10000350c`), and uses four scalar accumulators. Its index advances by four to the same `0x1000008` endpoint. There is no SIMD scan reduction in this loop. Vector loads/stores at chase return sites copy the small return array; they do not replace the indexed traversal.

The actual calls to chase-4, chase-1, chase-8, and scan occur at `0x100002cd4`, `0x100002d0c`, `0x100002d44`, and `0x100002d58`. They lie after the start steady-clock/process-CPU calls (`0x100002c70`, `0x100002c84`) and before the end calls (`0x100002d6c`, `0x100002d78`). The measured intervals also contain dispatch, argument/return copying and clock-boundary overhead.

Interpretation: nanoseconds per logical load include loop instructions and the hot position-array store after every chase load; this is not pure memory latency. The artificial access patterns can demonstrate host sensitivity to footprint and available independent chains. They do not count KKT cache/TLB misses, identify cache capacity, or assign a fraction of KKT runtime to memory stalls. Final-position validation cannot alone exclude omission of whole traversal cycles; the reviewed fixed loop counters supply the necessary machine-code evidence for this binary.
