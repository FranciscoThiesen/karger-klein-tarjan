#!/usr/bin/env python3
"""Independent synthetic schema/certificate tests; not native-export provenance."""
from copy import deepcopy
import json
import random
import re
import struct

import render_attachment_view as renderer


def hash_tuples(edges, n, weights):
    values = [n]
    for edge in edges:
        values.extend([edge["from"], edge["to"]])
        if weights:
            values.append(edge["weight"])
        values.append(edge["id"])
    value = 14695981039346656037
    for byte in struct.pack("<" + "I" * len(values), *values):
        value = ((value ^ byte) * 1099511628211) % (1 << 64)
    return str(value)


def fixture(endpoint, mode, b):
    # Small independent path + chord core. Synthetic output is kept in memory:
    # the generated HTML is never published as native KKT evidence.
    n, density, seed = 64, 1, 42
    q, m = n // b, n
    local = n - q
    family = f"{endpoint}_{mode}{b}"
    rng = random.Random(seed)
    labels = list(range(n))
    rng.shuffle(labels)
    pairs = [(u, u + 1) for u in range(q - 1)] + [(0, q - 1)]
    priorities = list(range(len(pairs)))
    rng.shuffle(priorities)
    def tier(i):
        u, v = pairs[i]
        if mode == "distance":
            return (u ^ v).bit_length()
        if mode == "shuffled":
            return 0
        return (v & -v).bit_length() if i < q - 1 else q.bit_length() + 1
    core_order = sorted(range(len(pairs)), key=lambda i: (tier(i), priorities[i]))
    ranks = {edge_id: rank + 1 for rank, edge_id in enumerate(core_order)}
    local_ranks = list(range(1, local + 1))
    rng.shuffle(local_ranks)
    edges, core = [], []
    for edge_id in range(local):
        block, clone = divmod(edge_id, b - 1)
        edges.append(dict(id=edge_id, **{"from": labels[b * block],
                                        "to": labels[b * block + clone + 1],
                                        "weight": local_ranks[edge_id]}))
    for edge_id, (u, v) in enumerate(pairs):
        a, c = (0, 0) if endpoint == "leaf" else (rng.randrange(b), rng.randrange(b))
        edges.append(dict(id=local + edge_id, **{"from": labels[b * u + a],
                                               "to": labels[b * v + c],
                                               "weight": local + ranks[edge_id]}))
        core.append(dict(id=edge_id, **{"from": u, "to": v, "rank": ranks[edge_id],
                                       "original_edge_id": local + edge_id}))
    if mode == "random":
        costs = list(range(1, m + 1))
        rng.shuffle(costs)
        for edge, cost in zip(edges, costs):
            edge["weight"] = cost
    rng.shuffle(edges)
    parent = list(range(n))
    def root(v):
        while parent[v] != v:
            v = parent[v]
        return v
    selected, weight = [], 0
    for edge in sorted(edges, key=lambda edge: edge["weight"]):
        a, c = root(edge["from"]), root(edge["to"])
        if a != c:
            parent[a] = c
            selected.append(edge["id"])
            weight += edge["weight"]
    return dict(schema="attachment_view_v1", case_id=f"{family}_n{n}_d{density}_p0",
                family=family, n=n, m=m, density=density, graph_seed=seed, kkt_seed=149,
                block_size=b, core_vertices=q, local_star_edges=local,
                input_fingerprint=hash_tuples(edges, n, True),
                topology_fingerprint=hash_tuples(edges, n, False), mst_total_weight=weight,
                validation="pass", layout_note="Synthetic schema test; not native solver evidence.",
                core_rank_note="Synthetic schema test.", original_to_label=labels,
                certified_mst_ids=sorted(selected), edges=edges, core_edges=core)


def rejects(data):
    try:
        renderer.validate_export(data)
    except renderer.InvalidExport:
        return
    raise AssertionError("malformed export accepted")


def main():
    cases = 0
    for endpoint in ("leaf", "community"):
        for mode in ("hierarchy", "distance", "shuffled", "random"):
            for b in (4, 16):
                data = fixture(endpoint, mode, b)
                result = renderer.validate_export(data)
                assert result["validation"] == "pass"
                document = renderer.render_html(data)
                embedded = re.search(r'<script type="application/json" id="graph-data">(.*?)</script>',
                                     document, flags=re.S)
                assert embedded and json.loads(embedded.group(1)) == data
                assert "__TITLE__" not in document and "__DATA__" not in document
                assert not re.search(r'<(?:script|link|img)[^>]+(?:src|href)=["\']https?://', document)
                cases += 1
    data = fixture("leaf", "hierarchy", 4)
    mutations = [
        lambda x: x.update(n=True),
        lambda x: x.update(family="leaf_hierarchy8"),
        lambda x: x.update(input_fingerprint="0"),
        lambda x: x.update(topology_fingerprint=1),
        lambda x: x.update(mst_total_weight=x["mst_total_weight"] + 1),
        lambda x: x.update(unexpected="field"),
        lambda x: x.update(validation="fail"),
        lambda x: x["original_to_label"].__setitem__(0, x["original_to_label"][1]),
        lambda x: x["edges"][0].update(id=x["edges"][1]["id"]),
        lambda x: x["edges"][0].update(weight=x["edges"][1]["weight"]),
        lambda x: x["core_edges"][0].update(original_edge_id=0),
        lambda x: x["core_edges"][0].update(rank=0),
        lambda x: x["certified_mst_ids"].__setitem__(0, x["certified_mst_ids"][1]),
        lambda x: x["certified_mst_ids"].pop(),
    ]
    for mutate in mutations:
        changed = deepcopy(data)
        mutate(changed)
        rejects(changed)
    injected = deepcopy(data)
    injected["layout_note"] = '</script><script>alert("never")</script>&'
    document = renderer.render_html(injected)
    assert injected["layout_note"] not in document
    assert r"\u003c/script\u003e" in document
    triangle = [{"from": 0, "to": 1, "weight": 1, "id": 0},
                {"from": 1, "to": 2, "weight": 2, "id": 1},
                {"from": 0, "to": 2, "weight": 3, "id": 2}]
    renderer.certify_mst(triangle, [0, 1], 3, 3)
    cycle_rejected = 0
    for selected, weight in [([0, 2], 4), ([1, 2], 5), ([0, 1, 2], 6), ([0], 1)]:
        try:
            renderer.certify_mst(triangle, selected, 3, weight)
        except renderer.InvalidExport:
            cycle_rejected += 1
        else:
            raise AssertionError("invalid tree/cycle certificate accepted")
    print(json.dumps({"validation": "pass", "synthetic_family_cases": cases,
                      "malformed_exports_rejected": len(mutations),
                      "invalid_mst_certificates_rejected": cycle_rejected,
                      "embedded_json_injection_checks": 1,
                      "browser_rendering": "not tested", "native_exports": "not tested"}, indent=2))


if __name__ == "__main__":
    main()
