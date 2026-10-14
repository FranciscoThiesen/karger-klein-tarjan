#!/usr/bin/env python3
"""Independent quotient gates and optional archived native-trace comparisons."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from render_attachment_view_test import fixture
from render_attachment_rounds import contraction_rounds, render_rounds_html
from render_attachment_view import InvalidExport


def native_checks(directory, output):
    expected = {f"{endpoint}_{mode}{block}" for endpoint in ("leaf", "community")
                for mode in ("hierarchy", "distance", "shuffled", "random") for block in (4, 16)}
    paths = sorted(directory.glob("*-view.json"))
    assert {path.name.removesuffix("-view.json") for path in paths} == expected
    if output:
        output.mkdir(parents=True, exist_ok=False)
    records = []
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    for path in paths:
        data = json.loads(path.read_text())
        work_path = path.with_name(path.name.replace("-view.json", "-work.json"))
        work = json.loads(work_path.read_text())
        assert work["schema"] == "search_work_v1" and work["validation"] == "pass"
        for key in ("case_id", "family", "n", "m", "density", "graph_seed", "kkt_seed"):
            assert work[key] == data[key]
        for key in ("input_fingerprint", "topology_fingerprint"):
            assert str(work[key]) == data[key]
        result = contraction_rounds(data)
        states = result["rounds"]
        assert len(states) == len(work["trace"]) + 1
        for before, after, native in zip(states, states[1:], work["trace"]):
            sizes = [len(group) for group in after["vertices"]]
            observed = {"round": after["round"], "input_vertices": before["active_vertices"],
                        "input_edges": len(before["edges"]),
                        "selected_edges": len(before["selected_for_next"]),
                        "output_vertices": after["active_vertices"], "output_edges": len(after["edges"]),
                        "component_count": len(sizes), "sum_squared_sizes": sum(size * size for size in sizes),
                        "largest_component": max(sizes)}
            assert observed == native, (path, observed, native)
        record = {"family": data["family"], "input": str(path.resolve()), "input_sha256": sha(path),
                  "work": str(work_path.resolve()), "work_sha256": sha(work_path),
                  "input_fingerprint": data["input_fingerprint"], "matched_native_stages": len(work["trace"])}
        if output:
            html, summary = render_rounds_html(data)
            target = output / (data["family"] + ".html")
            target.write_text(html, encoding="utf-8")
            record.update(output=target.name, output_sha256=sha(target), summary=summary)
        records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    assert not args.output_dir or args.native_dir
    cases = stages = random_nonstar = 0
    for endpoint in ("leaf", "community"):
        for mode in ("hierarchy", "distance", "shuffled", "random"):
            for b in (4, 16):
                data = fixture(endpoint, mode, b)
                result = contraction_rounds(data)
                states = result["rounds"]
                ledger = set()
                for state in states:
                    members = state["vertices"]
                    flat = [label for group in members for label in group]
                    assert sorted(flat) == list(range(data["n"]))
                    owner = {label: index for index, group in enumerate(members) for label in group}
                    # Reconstruct directly from the original graph, without
                    # depending on this driver's previous quotient or DSU.
                    expected = {}
                    for edge in data["edges"]:
                        a, c = sorted((owner[edge["from"]], owner[edge["to"]]))
                        if a != c:
                            value = (edge["weight"], edge["id"])
                            expected[(a, c)] = min(expected.get((a, c), value), value)
                    actual = {(edge["from"], edge["to"]): (edge["weight"], edge["id"])
                              for edge in state["edges"]}
                    # Round zero preserves the original edge orientations.
                    actual = {tuple(sorted(pair)): value for pair, value in actual.items()}
                    assert actual == expected
                    minima = set()
                    if state["edges"]:
                        for vertex in range(len(members)):
                            minima.add(min((edge["weight"], edge["id"])
                                           for edge in state["edges"]
                                           if vertex in (edge["from"], edge["to"]))[1])
                    assert minima == set(state["selected_for_next"])
                    assert not ledger & minima
                    assert state["mst_edges_selected_so_far"] == len(ledger)
                    ledger.update(minima)
                    stages += 1
                assert ledger == set(data["certified_mst_ids"])
                assert states[-1]["component_count"] == 1
                assert states[-1]["active_vertices"] == 0
                assert not states[-1]["edges"]
                first = states[1]
                is_star = (len(first["vertices"]) == data["n"] // b and
                           all(len(group) == b for group in first["vertices"]))
                if mode != "random":
                    assert is_star
                    assert len(first["edges"]) == data["m"] - data["n"] + data["n"] // b
                else:
                    random_nonstar += not is_star
                document, summary = render_rounds_html(data)
                embedded = re.search(r'<script type="application/json" id="contraction-data">(.*?)</script>',
                                     document, flags=re.S)
                assert embedded and json.loads(embedded.group(1)) == result
                assert summary["terminal_selected_edges"] == data["n"] - 1
                assert summary["shows_kkt_sampling_or_filtering"] is False
                assert "__ROUNDS__" not in document
                cases += 1
    malformed = 0
    for mutate in (lambda d: d.update(validation="fail"),
                   lambda d: d.update(input_fingerprint="0"),
                   lambda d: d["certified_mst_ids"].pop(),
                   lambda d: d["edges"][0].update(weight=0)):
        data = fixture("leaf", "hierarchy", 4)
        mutate(data)
        try:
            contraction_rounds(data)
        except InvalidExport:
            malformed += 1
        else:
            raise AssertionError("invalid graph reached contraction rendering")
    records = native_checks(args.native_dir, args.output_dir) if args.native_dir else []
    print(json.dumps({"validation": "pass", "synthetic_family_cases": cases,
                      "independently_reconstructed_quotients": stages,
                      "random_controls_with_nonstar_first_partition": random_nonstar,
                      "malformed_exports_rejected": malformed, "native_exports": records,
                      "native_trace_identity": "counts and partition moments only; physical order not asserted",
                      "browser_rendering": "not tested"}, indent=2))


if __name__ == "__main__":
    main()
