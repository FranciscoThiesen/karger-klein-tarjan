#!/usr/bin/env python3
"""Independent parent-proof negative gates using disposable mocked fixtures only."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "benchmark"))
import test_packed_sampling as tests

experiment = tests.experiment


def main():
    rejected = []
    with tests.fixture() as (root, args, parent):
        parent_root = Path(parent["working_directory"])
        assert root.parent == parent_root
        record = parent["variants"]["edge"]["build"]["record"]
        paths = [parent_root / "kkt/kkt.cpp", parent_root / "verifier/verifier_v2.cpp",
                 parent_root / "benchmark/build_edge_verifier.py",
                 Path(record["object_paths"]["kkt/kkt.o"]),
                 Path(record["object_paths"]["verifier/verifier_v2.o"]),
                 Path(record["main_object"]), Path(record["binary"]),
                 Path(parent["variants"]["edge"]["build"]["path"])]
        original_helpers = experiment.parent_engine.helpers
        for path in paths:
            assert path.resolve().is_relative_to(parent_root.resolve())
            before = path.read_bytes()
            try:
                path.write_bytes(before + b"independent temporary parent drift")
                try:
                    experiment.parent_record(args.parent_freeze)
                except ValueError:
                    rejected.append(str(path.relative_to(parent_root)))
                else:
                    raise AssertionError(f"historical native proof was bypassed for {path}")
                assert experiment.parent_engine.helpers is original_helpers
            finally:
                path.write_bytes(before)
            experiment.parent_record(args.parent_freeze)
            assert experiment.parent_engine.helpers is original_helpers
    print(json.dumps({"status": "pass", "rejected_original_parent_drift": rejected,
                      "helper_function_restored_after_each_failure": True,
                      "restored_parent_proof_passed_after_each_failure": True,
                      "native_solver_or_build_executed": False}, indent=2))


if __name__ == "__main__":
    main()
