# Completed standalone host calibration

Strict reanalysis passed all 224 native records: 168 measured calls and 56
warmups. [All calls](all-calls.csv) retain both clocks, the exact visit count,
positions/checksum and warmup identity. [The 112 summaries](summary.csv) retain
all three measured durations plus their minimum, median and maximum, separately
for each footprint, chain count, clock and size order. Each call makes
16,777,224 logical indexed-array reads.

CPU medians below are ns per logical indexed-array read. A slash separates the
ascending and descending process orders; neither order is discarded.

| Access pattern | 16 KiB | 64 MiB | 64 MiB measured range, ascending | 64 MiB measured range, descending |
|---|---:|---:|---:|---:|
| One dependent chain | 1.136 / 1.119 | 105.530 / 107.567 | 104.747–105.946 | 104.877–109.173 |
| Four independent chains | 0.2805 / 0.2813 | 24.738 / 25.820 | 23.967–25.123 | 23.426–26.333 |
| Eight independent chains | 0.1494 / 0.1492 | 11.623 / 11.345 | 11.355–12.139 | 10.994–12.168 |
| Contiguous scan | 0.1583 / 0.1570 | 0.16135 / 0.16206 | 0.15312–0.16755 | 0.16099–0.16540 |

At 64 MiB, corresponding wall medians are 106.136 / 108.775 ns for one chain,
24.977 / 26.111 for four, 11.689 / 11.352 for eight, and 0.16714 / 0.16213 for
the scan. Every intermediate footprint and all wall/CPU ranges remain in the
tables. One-chain CPU cost per logical read grows about 93–96 times between the
two endpoint footprints in these runs; this is a finite host observation.

The archived assembly review confirms the three fixed chase loop bounds and
independent register chains. Each chase read also stores its new position to
the hot stack array. The scan uses four scalar loads/accumulators per iteration,
not a SIMD reduction. The measured boundary includes loop work, dispatch,
argument/return copying and clock overhead. Consequently these figures are
neither pure memory latency nor STREAM bandwidth. They demonstrate sensitivity
to footprint and independent access chains for these artificial kernels; they
do not measure KKT cache/TLB misses, determine cache capacities, explain a
particular fraction of KKT CPU time, or establish its asymptotic complexity.

Both processes use the same deterministic arrays. They are different size
orders, not independent graph or random-input samples. Caches were not flushed;
the three measured repeats alone are not fully balanced across mode positions.
Warmups are preserved separately and never pooled into medians.

The [analysis receipt](analysis.json) binds the completed native attempt,
build/assembly artifacts, sources, raw logs and canonical CSVs. The arithmetic
command ran under the existing owned guard: actual exit 0, empty group, about
0.197 seconds; see `../host-memory-analysis01-guard/analysis.json`. No additional
native calibration or solver was run for this analysis. Plots remain pending
the explicit quiet release; this prose was added after the canonical analysis.
