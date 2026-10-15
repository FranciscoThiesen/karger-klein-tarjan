# Source-preparation receipt

2026-10-15. This draft was produced by source-text editing only. No project module was imported, no syntax check or test ran, no native binary was launched, and no frozen worktree was modified. This is not a validation or timing receipt.

| Source | SHA-256 |
| --- | --- |
| Reference `/Users/random_person/Desktop/kkt-packed-sampling/benchmark/run_packed_sampling.py` | `7c574c45054544eadfa5f07d0f2806364b7aee9e4c6bdfaf0565224cd87802b4` |
| Reference `/Users/random_person/Desktop/kkt-packed-sampling/benchmark/test_packed_sampling.py` | `683694f1de808a98a530689b956c52cdc09850e51b6890ea595f53cc58a6d534` |
| `run_compressed_queries.py` | `6e822ee7a004e342fd083f65dd4ec8e13f7e2c2695fef5002a6a1a0261ea2c4c` |
| `test_compressed_queries.py` | `8c10e340fe32b3cd2ed496ddb3ddeb7c4a13a9ee401ab7c9d3873d145770d652` |
| `PROTOCOL.md` | `c7ea1854ebe7ee50af792b34c757f2671a066799562810d49e2a447315109bc1` |
| `manifest.csv` | `bf0a9d0c5ff2458d5df952872e02c2f8322dc1ee5c56cb01ae36240f2a9c39d3` |
| `README.md` | `445d4b39ca83b7a056624dd5a0b79e442bb82688f7aaee98ab98ad32fd4fbcf8` |
| `/tmp/kkt-compressed-query-mechanism.md` | `09907bf4d5c5ad471acba79041366426d50d11e915cbebba31ea4a952999ae52` |

Build-record interfaces were coordinated with `/root/experiment_design`: `compressed_query_build_v1`, `reference`/`compressed`, shared seven non-verifier objects including KKT, and `.build/compressed-query` / `bin/compressed-query` paths. That agent independently source-reviewed the collector and found no source blocker, confirming build compatibility, parent/helper scope, monitor and reanalysis semantics, and the one-sampler arithmetic (24 children, 1,008 outputs, 864 timed, 144 warmups, 864 cross-variant clock pairs, 1,440 direct-comparator clock pairs). The agent's requested seed/order-confounding caveat was added to the protocol.

The 13-group mocked suite is prepared but has not been imported or executed. Independent source review requested stronger oracle independence and explicit link expectations; the revised source derives the full pair/group identity sets from raw rows, varies both clocks across all dimensions on an in-memory copy, checks duplicate/missing/opposite-clock corruptions, and spells out both link commands without the collector helper. The revised source has been sent for rereview. Executed validation and the remaining gates listed in README are still required before freeze/release; manual review is not a test result.
