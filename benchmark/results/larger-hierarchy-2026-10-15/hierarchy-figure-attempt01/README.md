# Analytic hierarchy retention

**Theoretical expectation, not observed work or timing.** All three declared hierarchy sizes at d=32 are included; the shuffled twin has no fixed-partition prediction here. Every defined input round is plotted.

| n | q | Core rounds | Full calls | Exact-model expected total input / m |
|---:|---:|---:|---:|---:|
| 65,536 | 16,384 | 14 | 15 | 13.61150258 |
| 1,048,576 | 262,144 | 18 | 19 | 17.48455230 |
| 4,194,304 | 1,048,576 | 20 | 21 | 19.42192487 |

The CSV retains exact rational numerators and denominators for every expectation. Independent finite-pair and exhaustive small-subset enumeration checks passed before rendering. This checks the formula on small domains, not the native solver, generator RNG, measured memory or hardware. Visual review is pending; PNG has SVG/PDF counterparts.
