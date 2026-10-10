# Provenance of the historical large baseline

The large comparison reuses **all 648 observations** from the
[earlier 18-case sweep](../large-2026-10-10/raw.csv). It does not rerun that
23-minute baseline. The final candidate runs the complete 18-case protocol
again, including Kruskal, Prim, and Borůvka. Final-run winner comparisons
therefore use contemporaneous competitors; before/after improvements use a
clearly identified historical baseline.

The archived run lasted from `2026-10-10T20:54:24.765691+00:00` to
`2026-10-10T21:17:38.502805+00:00`. Its
[metadata](../large-2026-10-10/metadata.json) records algorithm revision
`93406577df5653572c1d795fcf471202145071f1`. The extended harness was committed
after measurement in `5d57f8322041ddcaed49a6cfd5ac3dff7d820667`; its SHA-256
exactly matches the harness hash recorded for that run. Algorithm sources did
not change between those two revisions.

## Source and protocol comparison with 0820435

Read-only comparison against campaign baseline
`082043507ec58548aedb088f24a76ca27664a3cf` established:

- The bodies of `make_graph`, its explicit Fisher–Yates `shuffle`, and `Builder`
  are byte-identical after extraction into `graph_fixtures.hpp`. The namespace,
  `inline` qualifier, and default argument changed; RNG draws and generated
  edge/weight/ID order did not.
- `large_cases`, `options`, `measure`, and `run` have byte-identical bodies.
  Both protocols retain all 18 cases, graph seeds `17,42,999`, sampling seeds
  `0,1,7`, one timed repetition, zero warmups, the same shuffled case order,
  and the same rotating algorithm positions.
- The MST certificate and the Kruskal, Prim, Borůvka, union-find, and graph-utils
  implementation sources are byte-identical. Conversion and temporary-input
  destruction remain timed; certification, checks, and result destruction
  remain outside timing.
- KKT, LCA, verifier, and median-table changes before `0820435` add work-counter
  includes/calls and braces needed to place counters. With
  `KKT_ENABLE_WORK_STATS` undefined, every counter macro expands to `((void)0)`
  and its arguments disappear. The normal Make target does not define that
  flag. No algorithmic work change was found in this diff.
- Normal Make compiler/link commands and flags are unchanged. Both recorded
  environments use Apple clang 15.0.0, arm64, `-std=c++17 -O3 -Wall -Wextra
  -march=native`, the Apple SDK, and enabled assertions. CPU, RAM, macOS, and
  compiler metadata match: Apple M3 Max, 128 GiB, macOS 26.6.2 build 25G83.

SHA-256 values of the identical bodies, including their opening and closing
braces and original whitespace, are:

| Body | SHA-256 in both versions |
| --- | --- |
| `make_graph` | `328251873f40a6fa6fffc863eebb3425ab401643582acbe349f8733f6b841873` |
| `shuffle` | `01833f291a1f53f37a47a9c272f80bb761a5ff0f3b859bc1afd5f35897c11d99` |
| `Builder` | `23605b5046d3303fedbee59e29ab1994d5a7f8960930de6b7dbc851da05d5933` |
| `large_cases` | `4ebeef01711b1ff934638886dde6a3bfcc76d0144f9c6c2a530dd05208734632` |
| `options` | `ae47d16ae885344b7af1d813f999ba52c6719921c9980adc8c50faf77d82d19d` |
| `measure` | `e56dbbc26e395d42a936c32ff729918d539411b2775905f25d76fad38de49c43` |
| `run` | `c03225aa25f6194e654c4079dbb9b02889eb1bd9dd758947655f0481d48654ec` |

The archived CSV hashes to
`1624a9daa2cd7d9d392121f0fd488915a7b5521fff81708a8330eaeec8e838f6`,
matching its recorded hash. The old whole harness hashes to
`8d12902f3deeebc9a63af50b7bbf603b08389c3e10b90b8abe630636707e36f0`;
the extracted `0820435` harness hashes to
`7704262a45cc5cd55af35333be9bbc3e4d71d0789664d0e7192928e7e5156654`.
Its fixture header hashes to
`6d94c080b66b6f2538cbaa1758e82d87de4af25ca1d496ec8b8fed50c41dc98d`.
The certificate hash is unchanged:
`5e9c37e73c6a1bb78f1bfe5dca361abe9a4ddc4ea2e155a323989b6b34838495`.

## What this establishes and what it does not

These checks establish matching fixtures, protocol, compiler configuration,
and uninstrumented algorithm behavior at the source level. The archived run
does not record an executable hash, and this review does not claim identical
machine code. Source movement and assertion locations can change the binary.
Nor does source equivalence reproduce scheduling, cache/allocator state,
temperature, or clock noise from the earlier run.

All historical observations and losses remain in the comparison. Unchanged
competitor timings provide descriptive checks for between-run movement, not
an automatic correction. Large-case improvement ratios must be described as
historical before/after evidence. Claims that final KKT beats a competitor
must use the fresh final run; close races need repeated confirmation rather
than relying on this one-repetition historical pairing.
