# Small contraction explorer

This source-only view is separate from the frozen timing harness. It depicts
seven complete `n=64, m=256`, seed-17 instances, with no runtime claim:
hierarchical, distance-order and random-weight path/tree variants, plus the
cheap shuffled path. All panels show actual production Borůvka stages, including
random controls; no random control is assigned an artificial dyadic schedule.

`export.cpp` generates the fixtures, certifies Kruskal's MST independently,
checks KKT seed 0 against it, then calls the unchanged production
`boruvka_step` until completion. Every selected set is checked with a separate
incident-minimum scan. A separate DSU and ordered pair map verify component
memberships and minimum parallel edges. The union of selected IDs must equal
the certified MST. JSON includes original labels, input ordering, backbone IDs,
all-edge dyadic levels, exact stage edges, selected IDs and removal accounting.

The exporter was compiled with `/usr/bin/clang++` and the matching Apple SDK,
linking the existing native, uninstrumented production objects. With those Make
objects already built, reproduce from the repository root:

```sh
kkt_view_dir=benchmark/results/continuation-2026-10-12/visualization
kkt_view_sdk=$(xcrun --show-sdk-path)
/usr/bin/clang++ -std=c++17 -O2 -Wall -Wextra \
  -isysroot "$kkt_view_sdk" -I. "$kkt_view_dir/export.cpp" \
  .build/boruvka/boruvka.o .build/kruskal/kruskal.o .build/prim/prim.o \
  .build/lca/lca.o .build/union_find/union_find.o .build/graph_utils/graph_utils.o \
  .build/verifier/verifier_v2.o .build/kkt/kkt.o \
  -L"$kkt_view_sdk/usr/lib" -o /tmp/kkt_continuation_graph_export
/tmp/kkt_continuation_graph_export > "$kkt_view_dir/graphs.json"
python3 "$kkt_view_dir/build_view.py" "$kkt_view_dir/graphs.json" \
  --output "$kkt_view_dir/index.html"
node "$kkt_view_dir/validate_view.js"
```

`build_view.py` validates dimensions, paired topology, labels, unique ranks,
minimum selections, stage accounting, certified MST membership and exact
halving where applicable before embedding the JSON. The resulting `index.html`
is self-contained and needs no server, network access or JavaScript dependency.
Use its slider, weight controls, hover details and SVG export button. The
template alone is not a generated viewer.

Original vertices occupy an 8×8 Morton grid. Supervertices sit at the centroid
of their original members; positions are schematic and can overlap. Screen
distances are unrelated to weight ranks. The terminal empty graph is displayed
as completed, matching production's removal of the final isolated component.
Changing display filters never changes the reported full-graph counts.

Small graphs deduplicate sooner than the much larger measured inputs. This
illustration explains how contraction retains or removes shortcut edges; it
does not depict KKT sampling, verify a runtime crossover, or establish that
these engineered constructions represent application workloads.

Compilation, generation and the JSON/JavaScript checks completed while no timed
algorithm process was active. The generated [index.html](index.html) embeds all
data. `export.log` records seven certified fixtures; `javascript_validation.json`
records 492 control combinations and 984 panel states passing exact SVG
edge/node-count, next-selection and visibility-label checks. The JavaScript test
uses a minimal DOM and does not establish browser layout or download behavior.

Browser visual inspection remains incomplete. The installed Chrome headless
process exited with status 134 and no diagnostic output. A subsequent CUA
browser request rejected local `file://` navigation under its URL security
policy and explicitly prohibited workarounds; browser attempts then stopped.
No screenshot, layout inspection or actual SVG download is claimed.
