#!/usr/bin/env python3
"""Validate the tiny production-trace export and embed it in a standalone view."""
import argparse
import json
from pathlib import Path

FAMILIES = {
    "hierarchical_path", "distance_path", "low_path", "random_path",
    "hierarchical_tree", "distance_tree", "random_tree",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(data):
    require(data.get("schema") == 1, "unsupported graph schema")
    fixtures = data["fixtures"]
    require(len(fixtures) == 7 and {f["family"] for f in fixtures} == FAMILIES,
            "expected exactly seven unique families")
    for fixture in fixtures:
        family = fixture["family"]
        require((fixture["n"], fixture["m"], fixture["density"], fixture["graph_seed"]) ==
                (64, 256, 4, 17), f"wrong dimensions: {family}")
        require(fixture["validation"] == fixture["kkt_seed0_validation"] == "pass", "failed certificate")
        source = fixture["source_edges"]
        require(len(source) == 256 and all(len(edge) == 7 for edge in source), "wrong source edges")
        require(sorted(fixture["original_to_label"]) == list(range(64)), "invalid original labels")
        require(sorted(fixture["input_order"]) == list(range(256)), "invalid input edge order")
        require(fixture["backbone_ids"] == list(range(63)), "invalid backbone IDs")
        require(sorted(edge[2] for edge in source) == list(range(1, 257)), "weights are not unique ranks")
        require(len({tuple(sorted(edge[:2])) for edge in source}) == 256, "duplicate input pairs")
        for i, (u, v, weight, edge_id, level, backbone, mst) in enumerate(source):
            require(0 <= u < 64 and 0 <= v < 64 and u != v and edge_id == i, "invalid source tuple")
            require(level == (u ^ v).bit_length() - 1, "invalid source level")
            require(backbone == int(i < 63) and mst in (0, 1), "invalid edge classification")
        mst_ids = {edge[3] for edge in source if edge[6]}
        require(len(mst_ids) == 63, "wrong MST cardinality")
        require(fixture["mst_backbone_count"] == len(mst_ids.intersection(range(63))), "wrong overlap")
        stages = fixture["stages"]
        require(len(stages) >= 2, "missing contraction stages")
        selected_total = set()
        for r, stage in enumerate(stages):
            require(stage["round"] == r and stage["selected_total"] == len(selected_total), "round accounting")
            vertices, edges = stage["vertices"], stage["edges"]
            if vertices:
                require(sorted(v for members in vertices for v in members) == list(range(64)), "partition lost vertices")
                require(all(members and members == sorted(members) for members in vertices), "invalid component members")
            else:
                require(not edges and r == len(stages)-1 and selected_total == mst_ids, "invalid terminal stage")
                require(not stage["selected_next"], "terminal selections")
                continue
            require(len({tuple(sorted(edge[:2])) for edge in edges}) == len(edges), "parallel stage edges")
            incident_min = {}
            for u, v, edge_id in edges:
                require(0 <= u < len(vertices) and 0 <= v < len(vertices) and u != v, "invalid stage endpoint")
                a, b = source[edge_id][:2]
                require((a in vertices[u] and b in vertices[v]) or
                        (b in vertices[u] and a in vertices[v]), "stage edge has wrong members")
                for endpoint in (u, v):
                    candidate = (source[edge_id][2], edge_id)
                    incident_min[endpoint] = min(incident_min.get(endpoint, candidate), candidate)
            expected_selected = {value[1] for value in incident_min.values()}
            actual_selected = set(stage["selected_next"])
            require(len(actual_selected) == len(stage["selected_next"]) and actual_selected == expected_selected,
                    "wrong minimum-edge selections")
            require(actual_selected <= mst_ids and not actual_selected.intersection(selected_total), "wrong MST selections")
            selected_total.update(actual_selected)
            require(r+1 < len(stages), "nonterminal graph has no next stage")
            after = stages[r+1]
            require(len(edges) == len(after["edges"]) + after["loops_removed"] + after["parallels_removed"],
                    "edge removal accounting")
            if family.startswith(("hierarchical_", "distance_")):
                expected = 64 >> r
                require(len(vertices) == expected, "hierarchical trace did not halve")
        require(not stages[-1]["vertices"] and selected_total == mst_ids, "unfinished trace")
        if family.startswith("distance_"):
            levels = [edge[4] for edge in sorted(source, key=lambda edge: edge[2])]
            require(levels == sorted(levels), "distance ordering broken")
    for shape in ("path", "tree"):
        group = [f for f in fixtures if f["family"].endswith("_"+shape)]
        reference = group[0]
        for fixture in group[1:]:
            require(fixture["original_to_label"] == reference["original_to_label"] and
                    fixture["input_order"] == reference["input_order"], "paired labels/order changed")
            require([edge[:2]+edge[3:6] for edge in fixture["source_edges"]] ==
                    [edge[:2]+edge[3:6] for edge in reference["source_edges"]], "paired topology changed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("index.html"))
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    validate(data)
    template = Path(__file__).with_name("index.template.html").read_text()
    require(template.count("__FIXTURE_DATA__") == 1, "template marker count")
    encoded = json.dumps(data, separators=(",", ":")).replace("<", "\\u003c")
    args.output.write_text(template.replace("__FIXTURE_DATA__", encoded))
    print(f"Validated seven complete fixture traces; wrote {args.output}")


if __name__ == "__main__":
    main()
