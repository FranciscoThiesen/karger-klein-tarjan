# Independent numerical review

The independent raw audit passed on attempt 01 with exit status 0 and empty stderr. It imported no collector code. Its exact rational reconstruction agrees with strict analysis for all 48 children, 2,016 outputs, 1,728 cross-variant clock pairs, 2,880 within-variant comparator clock pairs, 3,024 medians and 30 crossover classifications. It also rechecked certificates, raw/combined concatenation, four topology twins, declared artifact hashes, clock/resource records and 48 empty process groups. There are zero retained call or capture-clock flags.

Evidence: [invocation](independent-audit-attempt01.invocation.json), [archived source](independent-audit-attempt01.source.py), [stdout](independent-audit-attempt01.stdout), [stderr](independent-audit-attempt01.stderr), [exit/provenance receipt](independent-audit-attempt01.json), [audit report](independent-numerical-audit/audit.json), and [exact ratios and summaries](independent-numerical-audit/README.md). Audit source SHA-256 before and after execution: `48aa9426cbf1b5518e60a440fdfc8c2633884c859ad0e924810f319cf4f4253a`. The archived copy has the same hash. No native performance was run by this audit.

Packed KKT is faster than scalar KKT in all 144 paired trials on both clocks. Its six pooled wall ratios range from 0.822856 to 0.918966, corresponding to 8.1–17.7% lower elapsed time. All four graph/sampler realization medians in every case also favor packed KKT on both clocks. This compares two private sampling policies: matching initial seed numbers do not imply matching samples or identical recursion work.

| Case | Packed/scalar KKT wall | CPU | Packed/retained-edge Borůvka wall | CPU | KKT wins vs retained-edge Borůvka, both clocks |
|---|---:|---:|---:|---:|---:|
| hierarchy, 65,536, d32 | 0.872729 | 0.872726 | 0.895701 | 0.895709 | 24/24 |
| shuffled, 65,536, d32 | 0.866087 | 0.866084 | 1.459575 | 1.459583 | 0/24 |
| hierarchy, 1,048,576, d32 | 0.918966 | 0.918965 | 1.004827 | 1.004827 | 9/24 |
| shuffled, 1,048,576, d32 | 0.913831 | 0.913831 | 1.704134 | 1.704131 | 0/24 |
| G(n,m), 4,096, d16 | 0.822856 | 0.822974 | 1.333819 | 1.333594 | 0/24 |
| G(n,m), 1,048,576, d16 | 0.913378 | 0.913378 | 1.555317 | 1.555306 | 0/24 |

The last column counts **KKT wins against** retained-edge Borůvka. The small hierarchy case has a useful observed lead, but its four wall realization medians span 0.879053–0.907144 (CPU 0.879091–0.907136). It therefore fails the prespecified requirement that every realization median be at most 0.90 and is classified as a narrow lead. The large hierarchy case is mixed: wall realization medians span 0.996245–1.007448, with nearly identical CPU endpoints. This is no crossover in KKT's favor as size increases.

All five comparators remain in the review. Each cell below is the packed KKT/comparator pooled wall ratio followed by the CPU ratio; lower than one favors KKT.

| Case | Deduplicating compactor | Retained-edge Borůvka | Kruskal | Prim | Original Borůvka |
|---|---:|---:|---:|---:|---:|
| hierarchy, 65,536, d32 | 0.713376 / 0.713390 | 0.895701 / 0.895709 | 0.983707 / 0.983711 | 1.804239 / 1.804233 | 1.320038 / 1.320044 |
| shuffled, 65,536, d32 | 0.811962 / 0.811966 | 1.459575 / 1.459583 | 0.882492 / 0.882493 | 1.635042 / 1.635034 | 2.109631 / 2.109618 |
| hierarchy, 1,048,576, d32 | 0.335695 / 0.335695 | 1.004827 / 1.004827 | 1.531315 / 1.531289 | 1.867477 / 1.867481 | 1.098306 / 1.098306 |
| shuffled, 1,048,576, d32 | 0.368377 / 0.368378 | 1.704134 / 1.704131 | 1.352413 / 1.352416 | 1.690126 / 1.690125 | 1.780600 / 1.780598 |
| G(n,m), 4,096, d16 | 1.395852 / 1.395702 | 1.333819 / 1.333594 | 0.842052 / 0.841917 | 0.647965 / 0.647984 | 1.488137 / 1.487134 |
| G(n,m), 1,048,576, d16 | 0.394935 / 0.394933 | 1.555317 / 1.555306 | 1.333161 / 1.333160 | 0.406399 / 0.406400 | 1.073736 / 1.073736 |

Across all 144 trials, packed KKT wins 120 against the deduplicating compactor, 33 against retained-edge Borůvka, 63 against Kruskal, 48 against Prim, and zero against original Borůvka. The counts agree on both clocks. Scalar KKT's corresponding counts are 116, zero, five, 48, and zero. Thus neither variant is an all-six-solvers winner in any paired trial; original Borůvka wins every direct comparison with KKT. Complete scalar values, ranges, and losses remain in [comparisons.csv](independent-numerical-audit/comparisons.csv).

Exactly two of the 30 prespecified classifications are strong observed crossover brackets: scalar and packed KKT versus the **deduplicating compactor** on G(n,m), between the measured endpoints 4,096 and 1,048,576 vertices at d16. There is no strong crossover against retained-edge Borůvka, Kruskal, Prim, or original Borůvka. KKT already leads Prim on G(n,m) at both endpoints; that is not a crossover. The small packed G(n,m)/Kruskal lead becomes a loss at the large endpoint. The exact predicates and all non-winning classifications are retained in [strong_crossover_brackets.csv](independent-numerical-audit/strong_crossover_brackets.csv).

The five unchanged solvers show modest cross-variant case-median drift: their wall packed/scalar ratios jointly span 0.992592–1.011210, compared with KKT's 0.822856–0.918966. The CPU range is similarly 0.992594–1.011210. This supports the observation that the KKT improvement is much larger than the measured control drift; it is not proof that all host/order effects are absent. Controls are not used to normalize the reported results. All solver-specific values remain in the audit's `cross_variant_drift` and `variant_comparisons.csv`.

Each case has only two graph seeds crossed with two sampling seeds. Six repeated trials per realization yield 24 ratios, not 24 independent graph samples. A two-endpoint bracket cannot locate the threshold, establish monotonic improvement, or prove asymptotic dominance. The frozen source/build/machine scope and the sampling-policy distinction remain necessary qualifications.
