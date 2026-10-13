# Predeclared line-gap precision ablation

Declared UTC: 2026-10-13T05:43:26.240273+00:00

This hypothesis arose from source/mathematical review while the existing
three-case extension was still running. It is a new retained model, not a
replacement for any measured line_metric graph or a solver optimization.

Original line gaps are IID integers 1..1024. Equal raw path gaps are ordered by
original path edge IDs, which increase from left to right. At each Boruvka
round all occurrences of the smallest remaining raw gap are selected; once
only equal maximum gaps remain, the remainder merges in one round. Thus a
fixed K-gap alphabet gives at most K rounds, in addition to the ordinary
halving bound. K=1024 is not the binding worst-case bound at current sizes,
and this observation alone does not prove that ties explain a measured curve.
The untimed component traces must establish what actually happened.

Add line_wide_metric: the same line topology and independent RNG streams,
with gap = 1+one full 32-bit mt19937 output, uniform over 1..2^32. Keep all
other construction and distance-ranking rules. At 8,388,608 vertices the largest
possible coordinate is (2^23-1)*2^32<2^55; exact absolute distances fit int64.
This approximates continuous IID gap ordering more closely over the measured
range, while still allowing ties and still having a forced adjacent-path MST.
It remains a fixed-alphabet family asymptotically and is not a general road
network or an unplanted-MST test. Its endpoints, IDs, label permutation and
input order must match the original line/random twins for the same seed.

Screen all four sizes 262,144;1,048,576;4,194,304;8,388,608 at m=16n, using
graph seed 3037, sampling seed 101, two balanced repetitions and one checked
warmup. Fixed manifest order: 1M,8M,262K,4M. Preserve every loss and near-tie.
The 40GiB/no-sustained-swap resource condition and exact MST certificates remain.
No timing starts until arithmetic, fixture, parity and old-fingerprint tests
pass and the source/binary/protocol are committed. Old captures stay unchanged.

Any later selection may consider this new family but must retain the complete
original discovery and extension screens. Fresh holdout seeds and the two-run
wall-and-CPU 0.90 criterion remain unchanged. This ablation cannot rescue or
replace an already-executed failed confirmation: no confirmation has yet run.

## Larger hierarchy control

Declared UTC: 2026-10-13T05:49:37.794085+00:00

Append hierarchical_path,n=4,194,304,d=16,p=0 after the four wide-line cases,
with the identical screen seed/repetition protocol. This is a retained control,
not a new candidate family. It asks whether the previously confirmed dyadic
hierarchy advantage survives a fourfold vertex increase on this machine.
The existing family size limit already permits it; no construction changes.
