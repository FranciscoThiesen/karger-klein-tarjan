# Actual compacting Borůvka round illustrations

These are small, separately exported graphs: n=1,024, d=2, graph seed 17 and sampling seed 0. They are not downsampled timing inputs. Layout coordinates and contracted centroids are illustrative, not geometry or edge weights.

The slider reconstructs minimum-edge contractions from actual endpoints and costs. It displays the compacting Borůvka continuation; only the first two rounds are shared with KKT. KKT sampling, filtering and recursion are not shown. Every chosen original ID belongs to the independently cycle-certified MST, and the terminal ledger equals that entire MST.

The independent Python gate matched all 99 native stages across these 16 exports: input/output vertex and edge counts, selected-edge counts, logical component counts, squared component sizes and maximum sizes. It does not assert native edge-vector ordering or component-label identity. See [validation](../validation/attachment_rounds_validation.json) and [QA status](QA.md).

These links are the retained JSON inputs. Generated HTML is excluded from Git.

| Endpoint mode | Hierarchy | Distance | Shuffled core | Global random |
|---|---|---|---|---|
| leaf, b=4 | [hierarchy](../validation/attachment-diagnostics/leaf_hierarchy4-view.json) | [distance](../validation/attachment-diagnostics/leaf_distance4-view.json) | [shuffled](../validation/attachment-diagnostics/leaf_shuffled4-view.json) | [random](../validation/attachment-diagnostics/leaf_random4-view.json) |
| leaf, b=16 | [hierarchy](../validation/attachment-diagnostics/leaf_hierarchy16-view.json) | [distance](../validation/attachment-diagnostics/leaf_distance16-view.json) | [shuffled](../validation/attachment-diagnostics/leaf_shuffled16-view.json) | [random](../validation/attachment-diagnostics/leaf_random16-view.json) |
| community, b=4 | [hierarchy](../validation/attachment-diagnostics/community_hierarchy4-view.json) | [distance](../validation/attachment-diagnostics/community_distance4-view.json) | [shuffled](../validation/attachment-diagnostics/community_shuffled4-view.json) | [random](../validation/attachment-diagnostics/community_random4-view.json) |
| community, b=16 | [hierarchy](../validation/attachment-diagnostics/community_hierarchy16-view.json) | [distance](../validation/attachment-diagnostics/community_distance16-view.json) | [shuffled](../validation/attachment-diagnostics/community_shuffled16-view.json) | [random](../validation/attachment-diagnostics/community_random16-view.json) |

The selected-density examples are [separate d=16 views](../attachment-views-d16/README.md).

Rebuild all 16 viewers from the repository root, then open the corresponding
local `.html` files:

```sh
kkt_view_root=benchmark/results/search-2026-10-13
for kkt_view_input in "$kkt_view_root"/validation/attachment-diagnostics/*-view.json; do
  kkt_view_name=${kkt_view_input##*/}
  kkt_view_name=${kkt_view_name%-view.json}
  python3 benchmark/render_attachment_rounds.py "$kkt_view_input" \
    --output "$kkt_view_root/attachment-round-views/$kkt_view_name.html"
done
```

Rendering runs Python validation and does not execute native solvers. The retained
validation hashes and QA notes describe the original capture; rebuilding does
not repeat browser inspection or update those records.
