"""Scratch-only parser/math checks. Run only after parent permits Python work."""
import copy
import csv
import importlib
import itertools
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
audit = importlib.import_module("analyze_ablation")


def save(path, fields, rows):
    with path.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    cases = audit.dimensions()
    timing = []
    trace = []
    for case, metadata in cases.items():
        n, m = metadata["n"], metadata["m"]
        for g, s, r, a in itertools.product(audit.GRAPH_SEEDS, audit.KKT_SEEDS, range(4), audit.ALGORITHMS):
            timing.append({**metadata, "graph_seed": g, "kkt_seed": s, "repetition": r,
                "order": (audit.ALGORITHMS.index(a) - r - audit.GRAPH_SEEDS.index(g) - audit.KKT_SEEDS.index(s)) % 2,
                "warmups": 1, "algorithm": a, "elapsed_ns": (n + m) * (10 if a == "kkt" else 20), "validation": "pass"})
        for g in audit.GRAPH_SEEDS:
            states = [(n, m), (n // 2, n // 2 - 1), (n // 4, n // 4 - 1), (0, 0)]
            for index, ((ni, mi), (nr, mr)) in enumerate(zip(states, states[1:]), 1):
                trace.append({**metadata, "graph_seed": g, "algorithm": "compacting_boruvka", "round": index,
                    "input_vertices": ni, "input_edges": mi, "selected_edges": ni - (nr or 1),
                    "output_vertices": nr, "output_edges": mr, "total_rounds": 3,
                    "total_selected_edges": n - 1, "input_fingerprint": n * 1000 + g, "validation": "pass"})
    with tempfile.TemporaryDirectory(prefix="kkt-ablation-validation-") as directory:
        path = Path(directory) / "input.csv"
        save(path, audit.TIMING_FIELDS, timing)
        primary = audit.load_timing(path)
        confirmation_rows = copy.deepcopy(timing)
        for row in confirmation_rows:
            row["elapsed_ns"] = row["elapsed_ns"] * 6 // 5
        save(path, audit.TIMING_FIELDS, confirmation_rows)
        confirmation = audit.load_timing(path)
        summaries = audit.summarize({"primary": primary, "confirmation": confirmation})
        assert len(primary) == len(confirmation) == 1440
        assert all(row["paired_runtime_ratio"] == 0.5 and row["kkt_slower_observations"] == 0
                   for row in summaries["paired_summary"])
        assert all(math.isclose(row["confirmation_over_primary"], 1.2) for row in summaries["run_drift"])
        hierarchy = {(g, s, r): [1, 100, 3, 4][r] * [1, 2, 4][si] * (gi + 1)
                     for gi, g in enumerate(audit.GRAPH_SEEDS)
                     for si, s in enumerate(audit.KKT_SEEDS) for r in range(4)}
        assert audit.median_hierarchy(hierarchy)[0] == 14
        save(path, audit.TRACE_FIELDS, trace)
        traces = audit.load_traces(path)
        assert len(traces) == 60
        trace_summary = audit.summarize_traces(traces)
        assert len(trace_summary["round_edge_volumes"]) == 20 * 4
        assert all(row["remaining_fraction_mean"] == 0 for row in trace_summary["round_edge_volumes"]
                   if row["completed_rounds"] == 3)
        rejected = 0

        def reject(rows, fields, loader, label):
            nonlocal rejected
            save(path, fields, rows)
            try:
                loader(path)
            except ValueError:
                rejected += 1
                return
            raise AssertionError("accepted malformed " + label)

        for field, value in [("case_id", "unexpected_n4096"), ("family", "star"), ("n", 4097), ("m", 0),
                             ("graph_seed", 0), ("kkt_seed", 42), ("repetition", 4), ("warmups", 0),
                             ("order", 2), ("elapsed_ns", 0), ("elapsed_ns", -1), ("elapsed_ns", "nan"),
                             ("elapsed_ns", 2**63), ("validation", "fail"), ("algorithm", "boruvka")]:
            rows = copy.deepcopy(timing); rows[0][field] = value
            reject(rows, audit.TIMING_FIELDS, audit.load_timing, "timing " + field)
        reject(timing[:-1], audit.TIMING_FIELDS, audit.load_timing, "missing timing")
        reject(timing + [timing[0]], audit.TIMING_FIELDS, audit.load_timing, "duplicate timing")
        reject([], audit.TIMING_FIELDS, audit.load_timing, "empty timing")

        for field, value in [("case_id", "unexpected_n4096"), ("family", "star"), ("n", 4097), ("m", 0),
                             ("graph_seed", 0), ("algorithm", "kkt"), ("round", 0), ("total_rounds", 0),
                             ("input_fingerprint", 2**64), ("input_vertices", 1), ("input_edges", 1),
                             ("selected_edges", 0), ("output_vertices", 1), ("output_edges", 0),
                             ("total_selected_edges", 1), ("validation", "fail")]:
            rows = copy.deepcopy(trace); rows[0][field] = value
            reject(rows, audit.TRACE_FIELDS, audit.load_traces, "trace " + field)
        reject(trace[1:], audit.TRACE_FIELDS, audit.load_traces, "missing trace round")
        reject(trace[3:], audit.TRACE_FIELDS, audit.load_traces, "missing trace graph")
        reject(trace + [trace[0]], audit.TRACE_FIELDS, audit.load_traces, "duplicate trace round")
        rows = copy.deepcopy(trace); rows[1]["input_fingerprint"] += 1
        reject(rows, audit.TRACE_FIELDS, audit.load_traces, "inconsistent trace fingerprint")
        rows = copy.deepcopy(trace); rows[1]["input_vertices"] -= 1
        reject(rows, audit.TRACE_FIELDS, audit.load_traces, "broken trace chain")
        rows = copy.deepcopy(trace); rows[0]["output_edges"] = rows[0]["input_edges"]
        reject(rows, audit.TRACE_FIELDS, audit.load_traces, "nonshrinking trace")

        # Exercise cross-campaign bridge checks with minimal synthetic work maps;
        # the imported full work validators have separate existing test suites.
        import analyze_common
        import analyze_shapes
        common_rows, shape_rows = {}, {}
        for (case, g), rounds in traces.items():
            destination = shape_rows if rounds[0]["family"] == "small_world" else common_rows
            for s in audit.KKT_SEEDS:
                destination[case, g, s] = {"input_fingerprint": rounds[0]["input_fingerprint"],
                    "root_after_two_vertices": rounds[1]["output_vertices"],
                    "root_after_two_edges": rounds[1]["output_edges"]}
        originals = analyze_common.load_work, analyze_shapes.load_work
        try:
            analyze_common.load_work = lambda *args: common_rows
            analyze_shapes.load_work = lambda *args: shape_rows
            assert len(audit.load_provenance(path, path, traces)) == 60
            first = next(iter(common_rows))
            for field in ("input_fingerprint", "root_after_two_vertices", "root_after_two_edges"):
                common_rows[first][field] += 1
                try:
                    audit.load_provenance(path, path, traces)
                except ValueError:
                    rejected += 1
                else:
                    raise AssertionError("accepted mismatched work " + field)
                common_rows[first][field] -= 1
        finally:
            analyze_common.load_work, analyze_shapes.load_work = originals
        print(f"Accepted complete synthetic matrices and known math; rejected {rejected} malformed cases.")


if __name__ == "__main__":
    main()
