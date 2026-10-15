#!/usr/bin/env python3
"""Fresh-seed follow-up using the frozen paired-screen implementation unchanged.

Only the declared ten cases, seeds, campaign identity and helper inventory vary.
The native binaries, build records and source inventory must equal the parent
screen's frozen artifacts. Overrides are scoped and restored even after errors;
importing this module cannot change the original screen analyzer's behavior.
CLI is identical to run_multigraph_experiment.py, including --released.
"""
import contextlib
from pathlib import Path

import run_multigraph_experiment as engine

HERE = Path(__file__).resolve()
PARENT_FREEZE = HERE.parent / "results/multigraph-2026-10-14/freeze.json"
PARENT_SHA256 = "7269bc0c92e6decb6355fc8cd1e95f471dcdad2d463cc66a45306ac80d7edc9a"
GRAPH_SEEDS = (3000001, 3000029)
SAMPLING_SEED = 809
EXPECTED_CASES = {
    (family, n, 16, 0) for family in ("leaf_hierarchy4", "leaf_distance4")
    for n in (65536, 262144, 2097152)
} | {("gnm_random", n, 16, 0) for n in (4096, 1048576)} \
  | {("gnm_random", n, 128, 0) for n in (4096, 262144)}
IDENTITY = {
    "campaign": "multigraph_fresh_seed_followup_v1",
    "parent_screen_freeze_sha256": PARENT_SHA256,
    "selection": "Prospective follow-up selected after the pilot screen; fresh graph and sampling seeds, declared larger sizes and small controls. Every new observation remains separate from the pilot; no historical timing is pooled or replaced.",
    "native_changes_since_screen": "None: exact same two binaries, build records, native sources and Makefile.",
}
SEMANTICS = {**engine.SEMANTICS, "followup": IDENTITY}

BASE_HELPERS = engine.helpers
BASE_PREFLIGHT = engine.preflight
BASE_CHECK_FREEZE = engine.check_freeze
BASE_ANALYZE = engine.analyze


def parent_freeze():
    engine.analysis.hash_check(PARENT_FREEZE, PARENT_SHA256)
    value = engine.analysis.read_json(PARENT_FREEZE)
    engine.analysis.equal(value, "schema", "multigraph_experiment_freeze_v1", "parent screen")
    return value


def helpers():
    # The JSON parent is separately hash-bound in semantics and checked here;
    # the Python inventory remains an inventory of actual Python helpers.
    parent = parent_freeze()
    base = BASE_HELPERS()
    engine.analysis.equal(parent, "python_source_sha256", base, "unchanged parent helper inventory")
    return {**base, str(HERE): engine.native.sha(HERE)}


def check_shared(frozen):
    parent = parent_freeze()
    for field in ("variants", "source_sha256", "build_recipe_sha256"):
        engine.analysis.equal(frozen, field, parent[field], "unchanged follow-up native provenance")


def check_freeze(path, verify_current=True):
    result = BASE_CHECK_FREEZE(path, verify_current=verify_current)
    check_shared(result[0])
    return result


def prepare(args):
    parent = parent_freeze()
    engine.require(args.manifest.resolve() != Path(parent["manifest"]), "follow-up needs its own manifest")
    engine.require(args.protocol.resolve() != Path(parent["protocol"]), "follow-up needs its own prospective protocol")
    engine.analysis.equal(parent, "source_sha256", engine.native.source_inventory(Path.cwd()), "unchanged native sources")
    engine.analysis.equal(parent, "build_recipe_sha256", {"Makefile": engine.native.sha(Path.cwd() / "Makefile")}, "unchanged Makefile")
    for variant in engine.VARIANTS:
        binary = getattr(args, variant + "_binary").resolve(strict=True)
        build = getattr(args, variant + "_build_record").resolve(strict=True)
        engine.analysis.equal(parent["variants"][variant], "binary", str(binary), "same screen binary")
        engine.analysis.hash_check(binary, parent["variants"][variant]["binary_sha256"])
        engine.analysis.equal(parent["variants"][variant]["build"], "path", str(build), "same screen build record")
        engine.analysis.hash_check(build, parent["variants"][variant]["build"]["sha256"])
    BASE_PREFLIGHT(args)
    check_freeze(args.freeze)


def label_analysis(args):
    BASE_ANALYZE(args)
    output = args.output_dir.resolve()
    provenance = engine.analysis.read_json(output / "provenance.json")
    provenance["followup_identity"] = IDENTITY
    provenance["input_sha256"][str(PARENT_FREEZE.resolve())] = PARENT_SHA256
    engine.write_json(output / "provenance.json", provenance)
    report = output / "README.md"
    text = report.read_text()
    heading, body = text.split("\n", 1)
    engine.require(heading == "# Paired KKT multigraph-contraction screen", "unexpected base report format")
    report.write_text("# Fresh-seed KKT multigraph-contraction follow-up\n\n"
                      "This separately declared follow-up reuses the pilot's exact binaries and native sources. "
                      "It uses graph seeds 3000001/3000029 and starting KKT seed 809 on ten declared cases. "
                      "Its 1,200 solver outputs are additional observations; pilot measurements are not pooled.\n" + body)


@contextlib.contextmanager
def configured():
    replacements = {"GRAPH_SEEDS": GRAPH_SEEDS, "SAMPLING_SEED": SAMPLING_SEED,
                    "EXPECTED_CASES": EXPECTED_CASES, "SEMANTICS": SEMANTICS,
                    "helpers": helpers, "preflight": prepare, "check_freeze": check_freeze,
                    "analyze": label_analysis}
    previous = {key: getattr(engine, key) for key in replacements}
    try:
        for key, value in replacements.items():
            setattr(engine, key, value)
        yield
    finally:
        for key, value in previous.items():
            setattr(engine, key, value)


def preflight(args):
    with configured():
        return prepare(args)


def capture(args, **kwargs):
    with configured():
        return engine.capture(args, **kwargs)


def load(path):
    with configured():
        return engine.load(path)


def analyze(args):
    with configured():
        return label_analysis(args)


def main():
    with configured():
        engine.main()


if __name__ == "__main__":
    main()
