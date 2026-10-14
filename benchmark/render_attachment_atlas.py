#!/usr/bin/env python3
"""SOURCE-ONLY DRAFT: render four existing small certified graph exports.

Do not import or execute until all native timing has ended and root releases
postprocessing. No solvers run. This is graph anatomy, not performance data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import math
from pathlib import Path
import shutil
import sys


FAMILIES = ("leaf_hierarchy4", "leaf_distance4", "leaf_shuffled4", "leaf_random4")
TITLES = ("Hierarchy: prescribed backbone MST", "Dyadic distance: shortcuts are eligible",
          "Control: shuffled core costs", "Control: globally shuffled costs")
CONTEXT_COUNT = 192
CONTEXT_SALT = "attachment-atlas-context-v1:"
YAW, PITCH, CAMERA = .65, -.38, 4.5


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(token):
        raise ValueError("nonfinite JSON token: " + token)
    return json.loads(path.read_text(), object_pairs_hook=pairs, parse_constant=invalid)


def load_inputs(repo, folder):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo / "benchmark"))
    validator = importlib.import_module("render_attachment_view")
    require(Path(validator.__file__).resolve() == repo / "benchmark/render_attachment_view.py",
            "validator was imported from a different repository")
    manifest_path, prior_path = folder / "exports.json", folder / "render_validation.json"
    manifest, prior = strict_json(manifest_path), strict_json(prior_path)
    require(manifest.get("validation") == "pass", "native export provenance is not successful")
    require(prior["validation"] == "pass" and
            prior["native_exports_provenance_sha256"] == sha(manifest_path),
            "prior certificate record does not bind native export provenance")
    require(len(manifest["records"]) == len(prior["records"]) == 4, "expected four archived exports")
    prior_by_family = {row["family"]: row for row in prior["records"]}
    require(set(prior_by_family) == set(FAMILIES), "archived family set differs")
    inputs = {str(path.resolve()): sha(path) for path in
              (Path(__file__), Path(validator.__file__), manifest_path, prior_path)}
    datasets, summaries = [], []
    for family in FAMILIES:
        path = folder / (family + ".json")
        data, digest = strict_json(path), sha(path)
        summary = validator.validate_export(data)  # Independent Python cycle certificate.
        require(data["family"] == family and data["n"] == 1024 and data["m"] == 16384
                and data["density"] == 16 and data["block_size"] == 4
                and data["graph_seed"] == 5009 and data["kkt_seed"] == 149,
                "atlas requires the archived n1024/d16/g5009/s149 leaf exports")
        require(prior_by_family[family]["input_sha256"] == digest, "export changed after prior validation")
        matches = [row for row in manifest["records"] if row["stdout_sha256"] == digest]
        require(len(matches) == 1 and matches[0]["exit_status"] == 0,
                "export is not bound to one successful native export")
        command = matches[0]["command"]
        require(len(command) == 11 and command[1:] == ["--family", family, "--n", "1024",
                "--density", "16", "--graph-seed", "5009", "--kkt-seed", "149"],
                "native export command differs from requested atlas input")
        inputs[str(path.resolve())] = digest
        datasets.append(data); summaries.append(summary)
    first = datasets[0]
    topology = lambda data: [(edge["from"], edge["to"], edge["id"]) for edge in data["edges"]]
    for data in datasets[1:]:
        require(data["original_to_label"] == first["original_to_label"]
                and topology(data) == topology(first), "paired labels, topology or edge order differ")
    return datasets, summaries, inputs


def coordinates(data):
    """Same illustrative dyadic/star construction and camera as the HTML view.

    Coordinates are generated from original block IDs, not inferred from costs.
    There is no physical geometry in the native export.
    """
    n, b, q = data["n"], data["block_size"], data["core_vertices"]
    levels = q.bit_length() - 1
    star_radius = .70 * .57 ** max(0, levels - 1)
    golden = math.pi * (3 - math.sqrt(5))
    positions = [None] * n
    for core in range(q):
        center = [0., 0., 0.]
        for level in range(levels):
            sign = 1 if (core >> (levels - level - 1)) & 1 else -1
            center[level % 3] += sign * .57 ** level
        for clone in range(b):
            point = list(center)
            if clone:
                z = 1 - 2 * (clone - .5) / (b - 1)
                radial, angle = math.sqrt(max(0, 1-z*z)), clone * golden
                point[0] += star_radius * radial * math.cos(angle)
                point[1] += star_radius * radial * math.sin(angle)
                point[2] += star_radius * z
            positions[data["original_to_label"][core*b+clone]] = point
    radius = max(math.hypot(*point) for point in positions)
    positions = [[value / radius for value in point] for point in positions]
    projected = []
    cy, sy, cp, sp = math.cos(YAW), math.sin(YAW), math.cos(PITCH), math.sin(PITCH)
    for x, y, z in positions:
        rx, rz = cy*x+sy*z, -sy*x+cy*z
        ry, depth = cp*y-sp*rz, sp*y+cp*rz
        factor = CAMERA / (CAMERA-depth)
        projected.append((rx*factor, ry*factor))
    return positions, projected


def csv_file(path, rows):
    require(bool(rows), "empty ledger")
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def context_ids(data):
    """One fixed core-edge visibility set; independent of weights and MST."""
    external_ids = [edge["id"] for edge in data["edges"] if edge["id"] >= data["local_star_edges"]]
    result = set(sorted(external_ids, key=lambda edge_id:
                 (hashlib.sha256((CONTEXT_SALT+str(edge_id)).encode()).digest(), edge_id))[:CONTEXT_COUNT])
    require(len(result) == CONTEXT_COUNT, "not enough core edges for fixed context count")
    return result


def visible_partition(data, context):
    """Sets consumed by the actual renderer and visibility ledger."""
    all_ids = {edge["id"] for edge in data["edges"]}
    require(context <= all_ids, "context contains an invented edge ID")
    local = data["local_star_edges"]
    require(all(edge_id >= local for edge_id in context), "context contains a local edge")
    mst = set(data["certified_mst_ids"])
    require(mst <= all_ids and set(range(local)) <= mst,
            "certified MST is missing a pendant edge or has an invented ID")
    return {"mst":mst,"local_mst":mst & set(range(local)),"core_mst":mst - set(range(local)),
            "extra":context - mst,"visible":mst | context,"hidden":all_ids - (mst | context)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        repo, folder = args.repo_root.resolve(strict=True), args.input_dir.resolve(strict=True)
        require(not args.output_dir.exists(), "refusing to replace existing atlas evidence")
        datasets, certificates, inputs = load_inputs(repo, folder)
        first = datasets[0]
        positions, projected = coordinates(first)
        local = first["local_star_edges"]
        # Select identical core IDs for all panels, independently of weights,
        # MST membership, family and observed performance.
        context = context_ids(first)
        original = [0] * first["n"]
        for vertex, label in enumerate(first["original_to_label"]):
            original[label] = vertex
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        from matplotlib.lines import Line2D
        plt.rcParams.update({"font.family":"sans-serif", "font.size":10, "svg.fonttype":"none"})
        fig, axes = plt.subplots(2,2,figsize=(14,12))
        fig.subplots_adjust(left=.035,right=.985,top=.87,bottom=.12,wspace=.08,hspace=.19)
        fig.suptitle("Certified MSTs on the same graph topology",x=.04,ha="left",y=.975,fontsize=19)
        fig.text(.04,.94,"Four separate small exports: n = 1,024, m = 16,384, b = 4, d = 16, graph seed = 5009",fontsize=11)
        fig.text(.04,.909,"Illustrative coordinates and fixed camera; edge length is not cost. No timing or KKT filtering is depicted.",fontsize=10.5)
        xvalues,yvalues = [p[0] for p in projected],[p[1] for p in projected]
        center_labels = [label for label in range(first["n"]) if original[label] % 4 == 0]
        leaves = [label for label in range(first["n"]) if original[label] % 4 != 0]
        records, ledger = [], []
        for panel,(data,title) in enumerate(zip(datasets,TITLES)):
            axis = axes.flat[panel]
            by_id = {edge["id"]:edge for edge in data["edges"]}
            partition = visible_partition(data, context)
            mst,local_mst,core_mst,extra = (partition[name] for name in ("mst","local_mst","core_mst","extra"))
            def lines(edge_ids,color,width,alpha,zorder):
                segments = [(projected[by_id[i]["from"]],projected[by_id[i]["to"]]) for i in sorted(edge_ids)]
                axis.add_collection(LineCollection(segments,colors=color,linewidths=width,alpha=alpha,zorder=zorder))
            lines(context,"#65768A",.45,.15,1)
            lines(local_mst,"#009E73",.85,.75,2)
            lines(core_mst,"#D55E00",1.05,.82,3)
            axis.scatter([xvalues[i] for i in leaves],[yvalues[i] for i in leaves],s=1.5,color="#6F8597",alpha=.7,zorder=4,linewidths=0)
            axis.scatter([xvalues[i] for i in center_labels],[yvalues[i] for i in center_labels],s=4,color="#263847",alpha=.9,zorder=5,linewidths=0)
            axis.set_xlim(min(xvalues)-.035,max(xvalues)+.035); axis.set_ylim(min(yvalues)-.035,max(yvalues)+.035)
            axis.set_aspect("equal"); axis.axis("off")
            axis.set_title(title,loc="left",fontsize=12,pad=12)
            visible = partition["visible"]
            shortcut_mst = sum(i >= local + data["core_vertices"]-1 for i in core_mst)
            axis.text(0,-.03,f"{data['family']} · all {len(mst):,} MST edges + {len(extra):,} other edges visible\n"
                      f"{data['m']-len(visible):,} input edges hidden · {shortcut_mst:,}/255 core MST edges are non-backbone",
                      transform=axis.transAxes,fontsize=8.5,va="top",color="#394650")
            records.append({"family":data["family"],"n":data["n"],"m":data["m"],
                            "mst_edges":len(mst),"local_mst_edges":len(local_mst),"core_mst_edges":len(core_mst),
                            "context_ids":len(context),"context_already_in_mst":len(context & mst),
                            "additional_context_edges":len(extra),"visible_unique_edges":len(visible),
                            "hidden_edges":data["m"]-len(visible),"nonbackbone_core_mst_edges":shortcut_mst,
                            "input_fingerprint":data["input_fingerprint"]})
            ledger.extend({"family":data["family"],**by_id[i],"mst":i in mst,"context":i in context,
                           "local":i < local} for i in sorted(visible))
        handles = [Line2D([0],[0],color=color,lw=2,label=label) for color,label in
                   (("#009E73","All 768 pendant MST edges"),("#D55E00","All 255 core MST edges"),
                    ("#65768A","Same 192 core context edges; MST overlaps drawn in color"))]
        fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.5,.048),ncol=2,frameon=False,fontsize=10)
        fig.text(.04,.024,"Every connection drawn is an actual exported edge. Context selection uses only edge ID; omitted edges remain in full copied inputs.",fontsize=9)
        output = args.output_dir.resolve(); output.mkdir(parents=True,exist_ok=False)
        for suffix in ("png","svg","pdf"):
            fig.savefig(output / ("actual_graph_atlas."+suffix),dpi=180,facecolor="white")
        plt.close(fig)
        csv_file(output/"visible_edges.csv",ledger); csv_file(output/"panel_counts.csv",records)
        csv_file(output/"illustrative_coordinates.csv",[{"label":label,"original_vertex":original[label],
                 "x":p[0],"y":p[1],"z":p[2],"projected_x":projected[label][0],"projected_y":projected[label][1]}
                 for label,p in enumerate(positions)])
        (output/"inputs").mkdir()
        for name in [family+".json" for family in FAMILIES]+["exports.json","render_validation.json"]:
            shutil.copyfile(folder/name,output/"inputs"/name)
        (output/"README.md").write_text("# Actual small-graph atlas\n\n"
            "![Certified MSTs and fixed sparse context](actual_graph_atlas.png)\n\n"
            "These are separately generated n1024/d16/g5009/s149 illustrations, not timed graphs or downsampled large inputs. "
            "The complete topology, IDs, labels and input order are identical across the four exports; only ranks change. "
            "Every certified MST edge is visible. A fixed set of 192 actual core-edge IDs supplies context independently of weights or MST membership. "
            "Some context edges are already MST edges, so the number of additional visible edges varies by panel. "
            "Exact visibility counts and IDs are in panel_counts.csv and visible_edges.csv; no omitted edge is removed from the copied inputs.\n\n"
            "The dyadic/star positions and fixed camera use the same construction as the interactive viewer. They are illustrative, not physical geometry; "
            "edge length is not weight. No contractions, sampling, filtering, runtime or large-input behavior are shown.\n\n"
            "All four inputs were independently cycle-certified again by the existing Python validator before plotting. "
            "Native export provenance is copied; original native source/binary hashes are retained from that archive, not reverified here. "
            "This renderer does not execute native solvers.\n\n"
            "Visual QA remains pending. Keep this optional figure only if all four panels are readable at report width. "
            "It complements the interactive views and work traces; it cannot replace them as a mechanism demonstration.\n")
        for path,digest in inputs.items():
            require(sha(Path(path)) == digest, "input changed while rendering: "+path)
        provenance = {"schema":"attachment_graph_atlas_v1","validation":"pass","visual_qa":"pending",
            "input_sha256":inputs,"certificates":certificates,"panels":records,
            "context_selection":{"method":"lowest SHA256(salt + decimal edge ID), tie by ID",
                "salt":CONTEXT_SALT,"count":CONTEXT_COUNT,"edge_ids":sorted(context),"same_in_all_panels":True},
            "coordinates":"illustrative dyadic/star construction copied from interactive viewer",
            "camera":{"yaw":YAW,"pitch":PITCH,"distance":CAMERA},"matplotlib_version":matplotlib.__version__,
            "no_native_solver_execution":True,"performance_evidence":False,
            "artifact_sha256":{str(p.relative_to(output)):sha(p) for p in sorted(output.rglob("*")) if p.is_file()}}
        (output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
        print(json.dumps({"validation":"pass","panels":4,"visual_qa":"pending","output_dir":str(output)}))
    except (OSError,ValueError,KeyError,TypeError,ImportError) as error:
        parser.exit(2,"attachment atlas: "+str(error)+"\n")


if __name__ == "__main__":
    main()
