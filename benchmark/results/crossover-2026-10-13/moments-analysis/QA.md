# Component-moment figure QA

All 12 final PNGs were opened and visually inspected. The independent review covered the eight larger-size plots; the root reviewer inspected the four one-million-vertex plots. No clipping, overlapping labels, unreadable legends, missing glyphs or misleading logarithmic terminal points were found. No rerender was needed.

| Vertices | PNG | Visual reviewer | Result |
|---|---|---|---|
| 1,048,576 | [edge_retention_n1048576_d16_p0.png](edge_retention_n1048576_d16_p0.png) | Root | Pass |
| 1,048,576 | [effective_components_n1048576_d16_p0.png](effective_components_n1048576_d16_p0.png) | Root | Pass |
| 1,048,576 | [component_balance_n1048576_d16_p0.png](component_balance_n1048576_d16_p0.png) | Root | Pass |
| 1,048,576 | [edge_volume_n1048576_d16_p0.png](edge_volume_n1048576_d16_p0.png) | Root | Pass |
| 4,194,304 | [edge_retention_n4194304_d16_p0.png](edge_retention_n4194304_d16_p0.png) | Independent review | Pass |
| 4,194,304 | [effective_components_n4194304_d16_p0.png](effective_components_n4194304_d16_p0.png) | Independent review | Pass |
| 4,194,304 | [component_balance_n4194304_d16_p0.png](component_balance_n4194304_d16_p0.png) | Independent review | Pass |
| 4,194,304 | [edge_volume_n4194304_d16_p0.png](edge_volume_n4194304_d16_p0.png) | Independent review | Pass |
| 8,388,608 | [edge_retention_n8388608_d16_p0.png](edge_retention_n8388608_d16_p0.png) | Independent review | Pass |
| 8,388,608 | [effective_components_n8388608_d16_p0.png](effective_components_n8388608_d16_p0.png) | Independent review | Pass |
| 8,388,608 | [component_balance_n8388608_d16_p0.png](component_balance_n8388608_d16_p0.png) | Independent review | Pass |
| 8,388,608 | [edge_volume_n8388608_d16_p0.png](edge_volume_n8388608_d16_p0.png) | Independent review | Pass |

The actual/effective component plots use positive normalized counts on a logarithmic y-axis and retain the terminal original component at `1/n`. The final production quotient has zero vertices and edges, while the original-vertex partition has one component of size n; captions distinguish these states. The size-balance curves end at one, and edge-retention curves end at zero. Each family panel displays its own complete round range; comparisons of total work should use the volume plot or exact tables rather than horizontal screen distance.

The 4,194,304-vertex hierarchy has 22 rounds, with actual and effective counts coincident. At 8,388,608 vertices, the narrow and wide lines have 10 and 15 rounds respectively. Their displayed contraction volumes round to 5.926 and 5.959; the hierarchy volume rounds to 8.892. These are untimed logical counts for one graph seed, not variability estimates or runtime explanations.

## Independent table and provenance checks

All corresponding CSV files are byte-identical to the successful strict diagnostic analysis. Their SHA-256 values also match its `derived_csv_sha256` registry. Checks cover all ten cases, not only the larger-size plots.

| Moment table | Strict diagnostic table | Rows | SHA-256 |
|---|---|---:|---|
| [component_stages.csv](component_stages.csv) | [component_stages.csv](../diagnostics-analysis/component_stages.csv) | 134 | `d66c1831298943f9de49d61c2b9daea35e9afb78d2a1b2045a459c47c7ea1081` |
| [graph_summary.csv](graph_summary.csv) | [component_graphs.csv](../diagnostics-analysis/component_graphs.csv) | 10 | `1cf1f0f22112e70e537e4b590fca5a7a0a12ca0a7acad0938a41991664b9236f` |
| [case_summary.csv](case_summary.csv) | [component_summary.csv](../diagnostics-analysis/component_summary.csv) | 10 | `e44a36fcea89d0283009add63349d85164a74fe333474a9e3dc02785a6e1111f` |

Both provenance records report 124 actual contraction stages and 134 derived rows including one stage-zero row per graph. Independent endpoint checks confirmed contiguous stage indices, positive actual/effective counts for every logarithmic point, the original n-component initial state, and all ten terminal states described above.

Trace CSV, moment log and manifest records match in both analyses, including resolved paths and hashes. Fresh SHA-256 checks of the raw files agree:

| Raw input | SHA-256 |
|---|---|
| [diagnostics_trace.csv](../diagnostics_trace.csv) | `43b2b979ccef5efa97da286c08acbc8ee5cee3d52d0e9fa8c77ddf35fd064ae1` |
| [diagnostics_trace.log](../diagnostics_trace.log) | `e1376f2fa69723816ee890d8f7d502c3681f54a765eeff6f8aa951d012cfc103` |
| [diagnostics.csv](../diagnostics.csv) | `2bbc7dd0cadfc6cc43ca8d18fd55cf9729b2a18003618c515ee7bafc924107b5` |

Moment provenance: `6984eebc4c36812b74114491805ab6908a1b25ddac6b4e86694d620ef452f83b`. Strict diagnostic provenance: `d2113e7f044adbac4f3f07fe3632cd3b48ebf1b325de24aa53b1f7fd232055d6`.

## Inspected PNG identities

| PNG | SHA-256 |
|---|---|
| edge_retention_n1048576_d16_p0.png | `4042491e6ad41012bf0e45d0997edb3a05f38742a441225acffb9b92029029a0` |
| effective_components_n1048576_d16_p0.png | `cf844917cf5b89f47e2b0ed2644bd6e4f3aa0eae6f1bf1da28eefe0463374a56` |
| component_balance_n1048576_d16_p0.png | `b89c2773d561366d84009aff65de8460e213e2d2ed48508af689e69332c832a8` |
| edge_volume_n1048576_d16_p0.png | `76bab21ce49153b08e5622be65c4e1e1eeb8186181903499c8003b80258de2b1` |
| edge_retention_n4194304_d16_p0.png | `79a50506cee3c0a039a56224ba2402377285aba260e33c5b78043f886d4f90b4` |
| effective_components_n4194304_d16_p0.png | `d8e725299de0bf1279bdb81c6a46c4f8f5117c953fd3f1fbed22e9254ac82590` |
| component_balance_n4194304_d16_p0.png | `58b40ef7c5c435bef8af8b66e6818abc1bf10f685714dfeedfa43ecade02f3e8` |
| edge_volume_n4194304_d16_p0.png | `51da728943bee8326998ab5dfcc28435232eb6833b098c02e5886a021609d264` |
| edge_retention_n8388608_d16_p0.png | `2c0fd0a90365c308b4c7b0e7a9ba37abf29826c16492ffe1f7e7dfb1425db1e0` |
| effective_components_n8388608_d16_p0.png | `9d25a9a578613f0d3984a2c2838c61ba4b8ead7f2e88f114b4f13cb447209a57` |
| component_balance_n8388608_d16_p0.png | `79beea29945e90415cd61020aa907d60264cd3c37b80519fb6676841b58f0d00` |
| edge_volume_n8388608_d16_p0.png | `f28b96898514a83ee16403c5357ac7c1fcbc6e9dbed6040ee792d48aca93c87a` |

No native solver, benchmark, build or export was run for this review. Visual approval covers the PNGs; the SVG/PDF companions were not separately opened in this review.
