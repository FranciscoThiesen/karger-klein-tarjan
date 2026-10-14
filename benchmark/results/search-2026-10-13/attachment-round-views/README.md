# Actual compacting Borůvka round illustrations

These are small, separately exported graphs: n=1,024, d=2, graph seed 17 and sampling seed 0. They are not downsampled timing inputs. Layout coordinates and contracted centroids are illustrative, not geometry or edge weights.

The slider reconstructs minimum-edge contractions from actual endpoints and costs. It displays the compacting Borůvka continuation; only the first two rounds are shared with KKT. KKT sampling, filtering and recursion are not shown. Every chosen original ID belongs to the independently cycle-certified MST, and the terminal ledger equals that entire MST.

The independent Python gate matched all 99 native stages across these 16 exports: input/output vertex and edge counts, selected-edge counts, logical component counts, squared component sizes and maximum sizes. It does not assert native edge-vector ordering or component-label identity. See [validation](../validation/attachment_rounds_validation.json) and [QA status](QA.md).

| Endpoint mode | Hierarchy | Distance | Shuffled core | Global random |
|---|---|---|---|---|
| leaf, b=4 | [hierarchy](leaf_hierarchy4.html) | [distance](leaf_distance4.html) | [shuffled](leaf_shuffled4.html) | [random](leaf_random4.html) |
| leaf, b=16 | [hierarchy](leaf_hierarchy16.html) | [distance](leaf_distance16.html) | [shuffled](leaf_shuffled16.html) | [random](leaf_random16.html) |
| community, b=4 | [hierarchy](community_hierarchy4.html) | [distance](community_distance4.html) | [shuffled](community_shuffled4.html) | [random](community_random4.html) |
| community, b=16 | [hierarchy](community_hierarchy16.html) | [distance](community_distance16.html) | [shuffled](community_shuffled16.html) | [random](community_random16.html) |

The selected-density examples are [separate d=16 views](../attachment-views-d16/README.md).
