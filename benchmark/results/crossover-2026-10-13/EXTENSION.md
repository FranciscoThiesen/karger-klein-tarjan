# Larger line and standard-random screen

Declared UTC: 2026-10-13T05:32:11.455898+00:00

The complete 19-case discovery is retained. Its geometric line ratios were
1.0541 at 262,144 vertices, 0.9317 at 1,048,576, and 0.9078 at 4,194,304.
This suggests a directional crossover but does not pass the 0.90 clear-win
threshold at its largest size. The geometric grid has a smaller large-size gain.

Extend the strongest candidate, line_metric at m=16n, to n=8,388,608;
add n=2,097,152 to measure the larger-size trend and approach to 0.90.
The observed parity crossing remains bracketed by 262,144 and 1,048,576. Also extend the
standard connected G(n,m) random-weight control to n=8,388,608. These are the
three cases in extension.csv, in its fixed recorded order. Use discovery graph
seed 3037, KKT seed 101, two balanced repetitions and one checked warmup.
This is exploration, not confirmation, and every result will be retained.

The largest input has 134,217,728 edges. The initial pilot's observed footprint
was well below 40GiB and observed swap use did not increase. The same 40GiB and
no-sustained-swap resource stop applies; no automatic retry or replacement.
This extension changes only benchmark input-range guards and associated
allocation-free domain tests. Existing-size fixture construction, timed bodies
and production solver sources remain unchanged. Archive the new binary/source
hashes separately before timing. Do not pool its absolute timings with the old
binary as if they were one uninterrupted campaign.

The previously declared fresh-seed confirmation protocol and 0.90 criterion
are unchanged. No holdout seed has been used. Freeze any selection only after
this complete extension and the original discovery have been analyzed.
