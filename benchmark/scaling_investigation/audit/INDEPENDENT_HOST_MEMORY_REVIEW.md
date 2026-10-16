# Independent host calibration source review

PASS, source only. No imports, tests, compilation, assembly inspection or native execution were performed by this reviewer. Actual build, manual machine-code inspection and the separately released calibration remain pending.

Reviewed SHA-256 values:

- `run_host_memory.py`: `b94d59922467bfc87d64d533e15569fcd87313c1628d318fa9a102a1603b5bcc`
- `host_memory.cpp`: `6f34d7deeba2ff7321592bd7eb91674fa7908351b72d27f560a673abaa2fcaa8`
- `HOST_MEMORY_PREPARATION.md`: `d67500dfa0e9a04d56d42e7470282f1f20fec586de48d3bd1813da1ea3db4ae6`

The fixed 7-footprint × 4-repetition × 4-mode schedule yields 112 rows per process, including 28 warmups. Ascending and descending launches retain 224 rows / 168 measured rows / 56 warmups, with the same seed and per-size arrays. Every mode performs 16,777,224 logical element loads. The 1/4/8-chain modes therefore require 16,777,224 / 4,194,306 / 2,097,153 dependent steps per chain. The native independent cycle walk verifies one full permutation cycle; rank-based final positions, unused zero slots and the permutation checksum are checked outside measurement. Source arguments are not assembly or runtime results.

The initial executor lacked full reconstruction of its saved build recipe and required proof inventory. The final version closes this gap with the same exact seven-command recipe for build and reload, canonical binary/SDK paths, mandatory source/helper/compiler/SDK/binary and 21 receipt/log bindings, metadata-content checks, and receipt stdout/stderr digest checks. It reuses the frozen candidate's pure `check_receipt` validator for command/cwd, actual zero exit, interval/deadline, RSS observations, poison/unavailability and nested empty-group proof, while every actual child still runs through the unchanged bounded owner. The validator source is itself bound. A changed included source or omitted build proof cannot silently pass reload.

The row parser enforces exact typed identity/order/count fields, positive wall/process-CPU durations, CPU endpoint differences and ordering, eight bounded positions and zero unused slots, and zero chase checksums. Run completion additionally requires identical fingerprints per footprint and identical positions/checksums per footprint/mode across all eight replays. Array-content correctness remains the native cycle/position/checksum oracle's responsibility; the Python layer does not independently regenerate the large arrays. Malformed first-process output prevents the second launch. All artifacts and failed attempts remain exclusive, and unknown cleanup state comes from the conservative inherited owner.

The build never runs the executable. Execution requires a separate explicit assembly-review acknowledgement, so root can inspect all chase loops, loop counts, independent dependencies, scan vectorization and timing boundaries first. Final positions alone cannot rule out omitted complete cycle traversals; the preparation note correctly requires actual instruction/loop review. The 300-second / sampled 1-GiB parent limits and supplementary native 240-second CPU / 285-second alarm are ceilings, not predicted runtime or continuous peak bounds.

Interpretation is appropriately limited: these are artificial repeated-array access patterns, not KKT profiling, KKT cache-miss attribution or a measured cache-capacity/STREAM result. Mode order is only partially balanced after excluding warmup; caches are not flushed; two size orders are not independent input realizations. No claim about KKT's fraction of memory-stall time follows from this calibration.
