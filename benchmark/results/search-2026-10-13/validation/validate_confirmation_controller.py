#!/usr/bin/env python3
"""Execution-free confirmation-controller gates; never launch native solvers."""
import argparse
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
from unittest import mock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        raise ValueError("refusing to overwrite validation evidence")
    folder = root / "benchmark/results/search-2026-10-13"
    source = folder / "run_attachment_confirmation.py"
    compile(source.read_text(), str(source), "exec")
    spec = importlib.util.spec_from_file_location("confirmation_controller", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    raw = folder / "attachment-large-timing.csv"
    metadata = raw.with_suffix(".json")
    analysis = folder / "attachment-large-analysis"
    provenance_path = analysis / "provenance.json"
    original_info = json.loads(metadata.read_text())
    original_provenance = json.loads(provenance_path.read_text())
    read_text = Path.read_text
    positives, negatives = [], []
    children_launched = []
    actual_popen = module.subprocess.Popen

    def only_git(command, *a, **kw):
        if command[:2] != ["git", "show"]:
            children_launched.append(command)
            raise AssertionError("prohibited process in execution-free validation")
        return actual_popen(command, *a, **kw)

    def reject(name, fn):
        try:
            fn()
        except (ValueError, FileNotFoundError, SystemExit) as error:
            negatives.append({"name": name, "rejection": str(error)})
        else:
            raise AssertionError("malformed input accepted: " + name)

    def prior_variant(mutate, *, sync_snapshot=True):
        info, provenance = copy.deepcopy(original_info), copy.deepcopy(original_provenance)
        mutate(info, provenance)
        if sync_snapshot:
            provenance["capture_metadata"] = {**info, "raw_csv": str(raw),
                "raw_csv_link": "../attachment-large-timing.csv"}
        def patched_read(path, *a, **kw):
            if path == metadata:
                return json.dumps(info)
            if path == provenance_path:
                return json.dumps(provenance)
            return read_text(path, *a, **kw)
        with mock.patch.object(Path, "read_text", patched_read):
            return module.validated_prior(root, raw, analysis, 10, [5009], [149])

    def cli(campaign="a", released=False):
        argv = [str(source), "--repo", str(root), "--campaign", campaign]
        argv += ["--released"] if released else ["--preflight-only"]
        stream = io.StringIO()
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stream):
            module.main()
        return json.loads(stream.getvalue())

    with mock.patch.object(module.subprocess, "Popen", only_git):
        info, bound = module.validated_prior(root, raw, analysis, 10, [5009], [149])
        assert info["validation"] == "pass" and bound
        positives.append("actual completed large capture and strict analysis with complete hashes")
        result = cli()
        assert result["validation"] == "pass" and result["native_capture_started"] is False
        assert result["campaign_files_created"] is False
        positives.append("actual A preflight, frozen declarations, no native launch or campaign file creation")
        variants = [
            ("failed prior capture", lambda i,p: i.update(validation="failed")),
            ("missing checked calls", lambda i,p: i.pop("checked_rows")),
            ("timed count incomplete", lambda i,p: i.update(checked_timed_rows=249)),
            ("wrong seed bank", lambda i,p: i.update(graph_seeds=[5008])),
            ("adjusted raw observations", lambda i,p: i.update(rows_adjusted=1)),
            ("missing child", lambda i,p: i["captures"].pop()),
            ("unknown child exit", lambda i,p: i["captures"][0].update(exit_status=None)),
            ("boolean child exit", lambda i,p: i["captures"][0].update(exit_status=False)),
            ("nonzero child exit", lambda i,p: i["captures"][0].update(exit_status=1)),
            ("interrupted child", lambda i,p: i["captures"][0].update(interruption="signal")),
            ("failed strict analysis", lambda i,p: p.update(validation="failed")),
            ("strict analysis missing case", lambda i,p: p.update(cases=9)),
            ("altered C++ inventory", lambda i,p: i["source_sha256"].update({next(iter(i["source_sha256"])): "0"*64})),
            ("altered helper inventory", lambda i,p: i["python_source_sha256"].update({next(iter(i["python_source_sha256"])): "0"*64})),
            ("altered Makefile", lambda i,p: i.update(build_recipe_sha256={"Makefile": "0"*64})),
            ("altered binary hash", lambda i,p: i.update(binary_sha256="0"*64)),
            ("wrong stack profile", lambda i,p: i["binary_profile"].update(main_stack_bytes=0)),
            ("missing derived inventory", lambda i,p: p.update(derived_sha256={})),
            ("altered derived artifact", lambda i,p: p["derived_sha256"].update({next(iter(p["derived_sha256"])): "0"*64})),
        ]
        for name, mutate in variants:
            reject(name, lambda mutate=mutate: prior_variant(mutate))
        reject("analysis/capture snapshot mismatch", lambda: prior_variant(
            lambda i,p: p["capture_metadata"].update(validation="failed"), sync_snapshot=False))
        reject("B without completed A", lambda: cli("b"))
        actual_sha = module.sha
        for name in ("ATTACHMENT_CONFIRMATION.md", "attachment-confirmation-a.csv", "attachment-confirmation-b.csv"):
            with mock.patch.object(module, "sha", lambda path, name=name: "0"*64 if Path(path).name == name else actual_sha(path)):
                reject("frozen declaration rejects altered " + name, lambda: module.frozen_declaration(root, folder))
        actual_exists = Path.exists
        with mock.patch.object(Path, "exists", lambda p: True if p == folder / "attachment-confirmation-a-timing.csv" else actual_exists(p)):
            reject("existing capture path cannot be overwritten", cli)

        # Exercise every B controller gate while reusing the real successful
        # large provenance. The synthetic A artifacts exist only in memory;
        # this does not claim the reserved matrix has been measured.
        a_controller_path = folder / "attachment-confirmation-a-controller.json"
        a_audit_path = folder / "attachment-confirmation-a-power-audit/audit.json"
        synthetic_a = {"schema": "attachment_confirmation_controller_v1", "validation": "pass",
            "campaign": "attachment-confirmation-a", "capture_exit_status": 0,
            "analysis_exit_status": 0, "power_audit_exit_status": 0, "power_audit_validation": "pass",
            "controller_sha256": module.sha(source), "retained_artifact_sha256": {str(source): module.sha(source)}}
        synthetic_audit = {"validation": "pass", "checked_calls": 2160,
            "input_sha256": {str(source): module.sha(source)}}
        original_sha = module.sha
        original_validated = module.validated_prior
        def b_variant(mutate=None):
            controller, audit = copy.deepcopy(synthetic_a), copy.deepcopy(synthetic_audit)
            if mutate:
                mutate(controller, audit)
            def b_read(path, *a, **kw):
                if path == a_controller_path:
                    return json.dumps(controller)
                if path == a_audit_path:
                    return json.dumps(audit)
                return read_text(path, *a, **kw)
            def b_prior(*a):
                if a[1].name == "attachment-confirmation-a-timing.csv":
                    return copy.deepcopy(original_info), {}
                return original_validated(*a)
            def b_sha(path):
                if Path(path) in (a_controller_path, a_audit_path):
                    return "a"*64
                return original_sha(path)
            with mock.patch.object(Path, "read_text", b_read), mock.patch.object(module, "validated_prior", b_prior), \
                 mock.patch.object(module, "sha", b_sha):
                return cli("b")
        assert b_variant()["validation"] == "pass"
        positives.append("synthetic completed A permits B preflight only; no reserved data generated")
        for field in ("validation", "capture_exit_status", "analysis_exit_status", "power_audit_exit_status",
                      "power_audit_validation", "controller_sha256"):
            reject("B rejects invalid A " + field, lambda field=field: b_variant(lambda c,a: c.update({field: None})))
        reject("B rejects possible active A process", lambda: b_variant(lambda c,a: c.update(native_process_may_still_be_running=True)))
        reject("B rejects A cleanup timeout", lambda: b_variant(lambda c,a: c.update(termination_warning="may still be running")))
        reject("B rejects mutated A artifact", lambda: b_variant(lambda c,a: c.update(retained_artifact_sha256={str(source): "0"*64})))
        reject("B rejects incomplete A audit", lambda: b_variant(lambda c,a: a.update(checked_calls=2159)))
        reject("B rejects failed A audit", lambda: b_variant(lambda c,a: a.update(validation="incomplete")))

    assert not children_launched
    assert not (folder / "attachment-confirmation-a-timing.csv").exists()
    assert not (folder / "attachment-confirmation-b-timing.csv").exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"validation": "pass", "controller_sha256": module.sha(source),
        "test_source_sha256": module.sha(__file__), "native_processes_launched": 0,
        "positive_checks": positives, "negative_checks": negatives,
        "method": "Actual completed-large preflight plus in-memory semantic mutations; snapshots are synchronized where appropriate so negative checks reach semantics rather than merely stale metadata hashes."}, indent=2) + "\n")
    print(f"PASS: {len(positives)} positive, {len(negatives)} negative gates; zero native launches")


if __name__ == "__main__":
    main()
