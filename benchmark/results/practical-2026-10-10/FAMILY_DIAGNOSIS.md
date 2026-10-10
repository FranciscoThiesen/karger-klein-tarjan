The final implementation at `2d4fbf1` uses sampling and heavy-edge filtering in
every tested hub, clustered, random, and geometric-grid observation. Stars
finish in one Borůvka contraction and never sample. These are **untimed logical
work observations**, not measurements of sampling's causal speed advantage.

The [raw CSV](family_work.csv), [probe source](family_work.cpp), and
[execution metadata](complexity/metadata.json) retain the evidence. The probe
uses the [unchanged shared fixtures](../../graph_fixtures.hpp), independently
certifies each reference MST, and requires every KKT result to match its exact
edge IDs.

The complete matrix contains six families × three vertex counts
(`1,024`, `16,384`, `65,536`) × graph seeds `{17,42,999}` × sampling seeds
`{0,1,7}`: **162 observations from 54 certified graphs**. The table aggregates
all three sizes and all nine seed pairs per size. Sampling calls count the
whole recursion, not just the root.

| Family | One-contraction finish | Two-contraction finish | Sampling with heavy removal | Sampling calls per observation |
|---|---:|---:|---:|---:|
| Hub | 0 | 0 | 27 | 1–3 |
| Star | 27 | 0 | 0 | 0 |
| Clustered | 0 | 0 | 27 | 2–8 |
| Random, `m=4n` | 0 | 0 | 27 | 1–7 |
| Random, `m=32n` | 0 | 0 | 27 | 1–7 |
| Geometric grid | 0 | 0 | 27 | 3–11 |

For the **16,384-vertex geometric grid**, all nine observations execute seven
sampling calls. The root's first two contractions reduce 64,770 input edges
to 4,653–4,741 edges, averaging 7.23% of the original edge count. Across all
verifier calls, heavy edges account for a mean 34.01% of their input edge
incidences. The sum of recursive KKT input edge counts, including the root,
averages `1.0936m`. This case exercises sampling and verification; it does not
finish through the initial contractions alone. Its small remaining graph also
shows how much reduction precedes sampling.

Hubs likewise use sampling: at 65,536 vertices the root retains a mean 6.05%
of its original edges after two contractions, followed by two or three
sampling calls. Stars provide no evidence of sampling benefit because they
never reach that code. At 65,536 vertices, clustered, random-4, and random-32
graphs retain respectively 24.63%, 73.08%, and 69.18% of root edges before
sampling. Their mean heavy fractions across verifier inputs are 97.31%,
96.40%, and 99.51%, showing substantial filtering activity even where timing
comparisons may favor another algorithm.

Percentages above are arithmetic means over the nine seed pairs at the stated
size. Light/heavy totals count edge incidences across recursion, so they are
not percentages of distinct original edges. Recursive input volume is not a
count of all edge passes. Establishing sampling's causal runtime advantage
would require a controlled comparison that changes sampling while retaining
the other implementation choices; this diagnostic makes no such claim.

Read-only validation checked the exact case/seed matrix without duplicates,
all success markers, identical input fingerprints across sampling seeds,
counter identities, and derived ratios. Edge counts were checked against
`n-1` for stars, `4n` for hubs/random-4, `32n` for random-32,
`4n-6√n+2` for geometric grids, and the shared clustered capacity formula.
In particular, clustered `n=1,024` has 16,143 edges because of that cap;
the two larger clustered cases have `16n+15` edges.
