# Large-attachment figure QA and bounded reading

Rendered with the unchanged plot helper:

```sh
python3 -B benchmark/plot_mst_search.py --analysis-dir benchmark/results/search-2026-10-13/attachment-large-analysis --output-dir benchmark/results/search-2026-10-13/attachment-large-figures --include-cpu
```

All four PNGs were opened and visually checked: wall runtimes, wall paired
ratios, process-CPU runtimes and process-CPU paired ratios. Each contains all
four family groups on one page. The ten cases, five runtime series, four
competitor-ratio series, trial-range bars, legends, parity/0.9 guides and
observed-size labels are visible and readable. No clipped plotted data or
missing panels were observed. PDF/SVG companions were generated from the same
figures but were not separately rendered. Lines connect measured sizes only;
the figure set includes no fitted crossover or extrapolation.

## All ten cases

The strict analysis retained 250 timed calls and 50 checked warmups, with one
graph seed (5009), one KKT seed (149), and five timed repetitions per algorithm.
The ratios below are medians of matched per-repetition ratios. They are not
ratios of independently summarized algorithm medians.

| Family | n | KKT / compacting Borůvka, wall | KKT / compacting Borůvka, CPU |
|---|---:|---:|---:|
| leaf_hierarchy4 | 524,288 | 0.8751 | 0.8750 |
| leaf_hierarchy4 | 2,097,152 | 0.8134 | 0.8141 |
| leaf_hierarchy4 | 4,194,304 | 0.8251 | 0.8250 |
| leaf_distance4 | 524,288 | 0.8885 | 0.8885 |
| leaf_distance4 | 2,097,152 | 0.8082 | 0.8082 |
| leaf_distance4 | 4,194,304 | 0.8302 | 0.8300 |
| leaf_shuffled4 | 2,097,152 | 0.9892 | 0.9889 |
| leaf_shuffled4 | 4,194,304 | 0.9913 | 0.9913 |
| leaf_random4 | 2,097,152 | 1.0190 | 1.0183 |
| leaf_random4 | 4,194,304 | 1.0447 | 1.0447 |

All cases have `b=4` and `m=16n`; the largest graph has 67,108,864 edges.
The six ordered cases favor KKT against the compactor in every one of their
five individual paired repetitions, for both clocks. Their wall paired medians
are 11.2–19.2% lower. The relative advantage is slightly smaller at 4,194,304
than at 2,097,152 vertices, so it is not monotonically increasing here. This
campaign's smallest ordered cases already favor KKT; it alone does not locate
the onset of a crossover.

Core-only shuffled controls are near parity and retain individual losses
(three KKT wins, two losses at each size). Global-random controls lose in paired
median at both sizes. **There is no all-four-comparator winner:** every case
has KKT paired medians above one against Kruskal, Prim and original Borůvka,
for both wall and CPU clocks. The full comparison and all individual losses
remain in the linked analysis tables.

## Both diagnostic flags remain

Both flags are `steady_exceeds_process_cpu` in
`leaf_shuffled4_n2097152_d16_p0`:

- Original Borůvka warmup: wall 9.078889458 s, CPU 6.179232 s.
- KKT timed repetition 0: wall 24.016168667 s, CPU 14.564061 s.

Neither call is excluded. The checked warmup remains in the raw/diagnostic
records; as with all warmups, it is excluded from timing summaries by protocol.
The flagged timed KKT call remains in its paired ratios and trial-range bars.
No flag is a diagnosis of its underlying cause. There are no capture/child UTC
interval flags. Separate CPU figures preserve the secondary clock comparison.

This is still one pilot graph/sample-seed pair. The large-size result supports
the compactor-specific mechanism on these structured instances; it establishes
neither broad practical superiority nor an asymptotic timing theorem.
