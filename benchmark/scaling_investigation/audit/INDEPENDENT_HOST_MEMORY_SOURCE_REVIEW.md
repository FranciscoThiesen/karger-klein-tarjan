# Independent host-calibration source review

Source-only review of `host_memory.cpp` and `HOST_MEMORY_PREPARATION.md` while
KKT timing is active. No imports, builds, native runs, disassembly or measurement
were performed. No release-blocking source or arithmetic defect was found.

The shuffled order creates one complete permutation cycle; the independent
visited bitmap checks all indices and closure. Each chain starts at a distinct,
equally spaced rank and its expected final index follows directly from the
cycle rank plus `visits / chains`. Unused position-array entries remain zero.
The fixed budget 16,777,224 is divisible by 1, 4 and 8, and the added eight gives
a nonzero final displacement at every declared footprint. All array/index and
rank additions fit their declared integer domains.

Every declared array length is a power of two, at most 2^24 entries. The scan
therefore performs complete permutation sums plus an eight-element suffix.
Its maximum possible sum is less than 2^48, well inside uint64. Fingerprint
multiplication deliberately uses defined unsigned wraparound. The rejection
shuffle uses the correct unsigned threshold and has a positive bound.

Setup, expected-value calculation, result checks, printing and array destruction
are outside the intended kernel interval. Final positions and checksums are
observable. Those safeguards do not prove the optimized load count: omitting
whole cycle traversals could preserve a final pointer position. The declared
machine-code gate must consequently inspect dependent-load bodies, independent
chain state and loop bounds, as well as scan array reads/vectorization.

Four-position mode rotation includes the warmup. The three measured repeats
alone are not a fully balanced four-position design; retain the recorded order
and do not call them balanced. Multiple chains share one array/cycle and offer
independent dependencies, not independent random graph inputs.

The scientific limitations are appropriately stated: repeated-array, unflushed
host calibration; active index-array footprint rather than process RSS; logical
loads rather than machine instructions; no automatic cache-size identification,
STREAM-bandwidth claim or fraction of KKT CPU attributed to memory. The separate
quiet-interval requirement is essential. Actual native/profile/codegen/complete
matrix/clock/known-empty-group gates remain pending root release.
