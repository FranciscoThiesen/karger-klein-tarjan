# Separate host memory-access calibration

Source-only preparation; no build, execution, timing or machine-code inspection
has occurred. This is a host calibration, not KKT profiling and not a cache-miss
counter. It cannot identify the fraction of KKT CPU time attributable to memory.

The small standalone `host_memory.cpp` constructs one deterministic random
permutation cycle per footprint, independently validates that every index is
visited exactly once, and measures one dependent chain, four independent
chains, eight independent chains, and a contiguous sum over the same array.
Footprints are fixed at 16 KiB, 64 KiB, 256 KiB, 1 MiB, 4 MiB, 16 MiB and 64 MiB.
The index array alone defines the active footprint, not total process RSS.
Shuffle and validation buffers are destroyed before measurements.

Every cell performs exactly 16,777,224 logical 32-bit loads, including the scan.
The extra eight accesses make every final pointer position differ from its
start, including for the largest full-cycle case. Independent chains begin at
equally spaced ranks of the same cycle; each executes loads/chains dependent
steps. Setup retains exact expected positions from those ranks. The scan's
checksum uses the permutation's known full-cycle sum plus its eight-element
suffix. Final values are checked and printed outside timing. The scan may
vectorize: logical loads are element reads, not an asserted instruction count.

Each footprint runs one warmup and three measured calls for all four modes,
rotating mode order across the four repeats. This gives 112 rows per process,
84 measured and 28 warmup. Declare two independent process launches, ascending
then descending footprint order, with the same inputs: 224 rows, 168 measured,
56 warmup. Retain the order distinction rather than treating it as extra input
randomness. Repetition 0 remains in the raw data. Cache state is not flushed;
the three measured repeats alone are not fully balanced across mode positions.
These are repeated-array measurements. Allocation layout, frequency, thermal
state, page translation and scheduling remain possible influences. No knee is
automatically a cache-size measurement, and the scan is not STREAM bandwidth.

The intended boundary contains kernel dispatch, its memory accesses and result
assignment. Native wall and process CPU clocks are recorded separately. Each
process has a fixed 240-second CPU limit and 285-second supplementary alarm;
the existing owned controller must independently impose 300 seconds, a sampled
1 GiB RSS ceiling and affirmative child/group cleanup. These are ceilings, not
runtime estimates. No retry may quietly shrink work or change the footprint set.

## Root-only build and execution recipe

After explicit release, use the small `run_host_memory.py` executor. It reuses
the unchanged `benchmark/scaling_investigation/run.py` `run_owned` for every
compile, metadata and execution command, preserving exact receipts/logs.
Execute in a separate quiet interval, never alongside a KKT performance capture.
The owner calls `clean_environment()`. The executor binds source/helper SHA
before and after, compiler bytes/version, selected SDK path/SDKSettings.json,
full argv, binary SHA and the native arm64/512-MiB-stack profile. This hashes
SDK identity metadata, not every SDK header/library. Exact prospective commands,
from the worktree root (replace SDK with the checked depth-build01 SDK path):

```text
/usr/bin/python3 -B benchmark/scaling_investigation/audit/run_host_memory.py build
  benchmark/results/scaling-investigation-2026-10-15/host-memory-build01 --sdk SDK
```

The build phase makes exactly seven serial owned commands: xcrun SDK discovery,
Apple compiler version, compile/link, `file -b`, `otool -l`, `nm -C`, then
`otool -tvV`. All use a 300-second/1-GiB ceiling and retain stdout/stderr and
group-cleanup receipts. The compile argv is:

```text
/usr/bin/arch -arm64 /usr/bin/clang++ -std=c++17 -O3 -march=native -Wall -Wextra
  -isysroot <the checked candidate SDK> -L<the checked candidate SDK>/usr/lib
  benchmark/scaling_investigation/audit/host_memory.cpp
  -Wl,-stack_size,0x20000000
  -o <fresh-output>/host_memory
```

No KKT object is linked and no production source changes. Before execution,
inspect `symbols.stdout` and `assembly.stdout` from that successful build phase,
covering all three chase bodies plus the scan: dependent index
loads must remain in the loop, independent chains must not collapse into one
dependency chain, and the scan must read array values. The source's noinline
boundary, checked observable results and memory barriers are safeguards; they
are not a substitute for inspecting optimized code. Disclose unrolling,
vectorization or unexpected compiler transformations.
In particular, final positions cannot detect omission of complete cycle
traversals: inspect the actual loop bound and load structure, not just output.
For K=1,4,8, require respectively 16,777,224 / 4,194,306 / 2,097,153 iterations,
with 1/4/8 dependent-chain steps per iteration; account for any unrolling and
epilogue so each body still performs exactly 16,777,224 logical reads. Check
that each chain consumes its own previous loaded index, and that the outer
clock calls and memory barriers still enclose the kernel call. For the scan,
validate the same total element count, mask wrap and remainder despite SIMD.
These checks are manual assembly interpretation, not inferred from `noinline`.
Save a short source/binary/assembly-hash-bound review note before acknowledging
the next gate. The executor does not pretend to understand machine code.

After the actual assembly review, invoke:

```text
/usr/bin/python3 -B benchmark/scaling_investigation/audit/run_host_memory.py run
  benchmark/results/scaling-investigation-2026-10-15/host-memory-run01
  --build benchmark/results/scaling-investigation-2026-10-15/host-memory-build01/attempt.json
  --assembly-reviewed
```

The explicit acknowledgement is the root's manual review declaration. The
executor rechecks build receipts and source/binary/helper hashes, runs the exact
binary once with `ascending`, then once with `descending`, using
`run_owned(..., timeout=300, rss_cap=1024**3)`. Root records the actual outer tool
exit and requires both child receipts to prove empty groups. Independently check
224 unique mode/size/order/repetition identities, the fixed logical counts,
positive clock intervals, same per-size fingerprints in both orders, and every
native validation result. Reject partial matrices or altered counts; retain
failed attempts. Report wall and CPU ns/logical load with all three measured
values per cell, not just the favorable repeat.

The executor enforces literal ordered 112-row child matrices (224 total), strict
JSON types/keys, counts, active/unused positions, clock differences and order,
equal per-size fingerprints and identical per-mode results across repeats and
orders. Its strict receipt reload reuses the frozen candidate runner's pure
`check_receipt` validator for interval/resource/nested cleanup proof; execution
still uses only `base.run_owned`. The exact seven-command recipe, complete
required artifact inventory and receipt log hashes are checked before launch.
Native independent cycle/position/checksum
checks remain authoritative for exact array contents. Every output directory
is exclusive; malformed first-child output prevents the second child. An error
retains its `attempt.json` and existing child evidence. There is no automatic
retry, threshold change, library acquisition or KKT solver call.

This design borrows the distinction between dependent-load latency and memory
parallelism from the references already reviewed in `research.md`: [Beamer,
chapter 5](https://www.scottbeamer.net/pubs/beamer-thesis.pdf),
[lmbench, §6](https://www.usenix.org/publications/library/proceedings/sd96/full_papers/mcvoy.pdf),
and [Lemire's independent-chain experiment](https://lemire.me/blog/2018/11/05/measuring-the-memory-level-parallelism-of-a-system-using-a-small-c-program/).
Their published host measurements are not transferred to this machine.
