#!/usr/bin/env python3
"""Prepared synthetic collector gates; no native or library launches.

The full parent/build/smoke proof is mocked only in lifecycle fixtures. Actual
library schemas and numerical models have an independent analyzer suite and a
mandatory future real linked smoke; these mocks cannot substitute for either.
"""
import argparse
import contextlib
import copy
import csv
import json
from pathlib import Path
import signal
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import collect as target


def declared_schedule():
    result = []
    for family in ("leaf_hierarchy4", "leaf_shuffled4", "gnm_random"):
        for gi, graph in enumerate((19000013, 19000043)):
            for si, sampler in enumerate((3001, 3011)):
                names = ("kkt", "multigraph_boruvka") if gi == si else ("multigraph_boruvka", "kkt")
                for algorithm in names:
                    result.append(dict(family=family, algorithm=algorithm, graph_seed=graph,
                                       sampling_seed=sampler, size_order="ascending" if gi == 0 else "descending"))
    return result


def raw_rows(spec):
    values = []; cpu = 1000; utc = 1_000_000_000
    sizes = (1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576)
    if spec["size_order"] == "descending": sizes = sizes[::-1]
    for n in sizes:
        graph = spec["graph_seed"]
        base = n + graph * 100
        m = n * (16 if spec["family"] == "gnm_random" else 32)
        family_slot = ("leaf_hierarchy4", "leaf_shuffled4", "gnm_random").index(spec["family"])
        for invocation in (0,1,2):
            for phase, iteration in (("warmup",0),("timed",0),("timed",1)):
                elapsed = 100 + invocation * 10 + iteration
                values.append(dict(spec, n=n, m=m, N=n+m, input_fingerprint=base+family_slot,
                    topology_fingerprint=base+(100 if family_slot==2 else 0), invocation=invocation,
                    phase=phase, iteration=iteration, elapsed_ns=elapsed, utc_start_ns=utc,
                    utc_end_ns=utc+elapsed, process_cpu_start_ns=cpu, process_cpu_end_ns=cpu+elapsed,
                    process_cpu_elapsed_ns=elapsed, validation="pass"))
                cpu += elapsed+10; utc += elapsed+10
    return values


def write_rows(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=target.FIELDS)
        writer.writeheader(); writer.writerows(rows)


def certificate_text(rows):
    return "".join("complexity_certificate_v1 " + json.dumps({key: row[key] for key in target.CERTIFICATE_FIELDS}) + "\n"
                   for row in rows if row["phase"] == "warmup")


class Process:
    def __init__(self, pid, status=0): self.pid, self.status, self.returncode = pid, status, None
    def wait(self, timeout=None): self.returncode = self.status; return self.returncode
    def poll(self): return self.returncode


class Factory:
    def __init__(self, mutation=None, status=0): self.children=[]; self.mutation=mutation; self.status=status
    def __call__(self, argv, **kwargs):
        assert argv[:2] == ["/usr/bin/arch", "-arm64"] and kwargs["start_new_session"] is True
        spec = dict(family=argv[3], algorithm=argv[4], graph_seed=int(argv[5]), sampling_seed=int(argv[6]), size_order=argv[7])
        rows = raw_rows(spec)
        kwargs["stderr"].write(certificate_text(rows))
        if self.mutation: self.mutation(rows)
        write_rows(Path(argv[8]), rows)
        Path(argv[9]).write_text('{"synthetic_library_schema_not_validated":true}\n')
        process = Process(61000+len(self.children), self.status); self.children.append(process)
        return process


@contextlib.contextmanager
def fixture(factory=None):
    factory = factory or Factory()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder).resolve(); freeze = root / "freeze.json"; output = root / "capture.json"
        frozen = dict(binary="/synthetic/never-launched", working_directory=str(root),
                      bound_sha256={}, source_sha256={}, parent_helpers={})
        freeze.write_text(json.dumps(frozen))
        analyzer = SimpleNamespace(validate_curve_library=lambda document,spec,rows: None)
        def provider(group):
            process = next(item for item in factory.children if item.pid == group)
            members = [] if process.returncode is not None else [dict(pid=group, rss_kib=100, command="mock-native")]
            return dict(process_group=group, members=members)
        sampler = target.monitor.BoundedSampler(provider, .1)
        with mock.patch.object(target, "check_freeze", return_value=frozen), mock.patch.object(target, "module", return_value=analyzer):
            yield root, argparse.Namespace(freeze=freeze, output=output, released=True), factory, sampler


class CollectorTests(unittest.TestCase):
    def test_literal_schedule_rows_certificates_and_twins(self):
        self.assertEqual(target.schedule(), declared_schedule())
        all_rows=[]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for index,spec in enumerate(declared_schedule()):
                rows=raw_rows(spec); raw=root/f"{index}.csv"; log=root/f"{index}.log"
                write_rows(raw,rows); log.write_text(certificate_text(rows))
                actual,flags=target.check_rows(raw,spec)
                self.assertEqual(actual,rows); self.assertEqual(len(target.certificates(log,actual)),33)
                self.assertEqual(len(flags),99); self.assertFalse(any(item["diagnostic_flags"] for item in flags))
                all_rows.extend(actual)
            target.fingerprint_matrix(all_rows,complete=True)
            self.assertEqual(len(all_rows),2376)
            changed=copy.deepcopy(all_rows); changed[0]["input_fingerprint"]+=1
            with self.assertRaises(ValueError): target.fingerprint_matrix(changed,complete=True)

    def test_native_missing_duplicate_reordered_domain_and_certificate_negatives(self):
        spec=declared_schedule()[0]
        mutations=(lambda rows: rows.pop(), lambda rows: rows.__setitem__(1,dict(rows[0])),
                   lambda rows: rows.reverse(), lambda rows: rows[0].update(n=True),
                   lambda rows: rows[0].update(elapsed_ns=0), lambda rows: rows[0].update(N=0),
                   lambda rows: rows[0].update(process_cpu_elapsed_ns=2**63),
                   lambda rows: rows[0].update(sampling_seed=3011))
        with tempfile.TemporaryDirectory() as folder:
            raw=Path(folder)/"raw.csv"; log=Path(folder)/"log"
            for mutation in mutations:
                rows=raw_rows(spec); mutation(rows); write_rows(raw,rows)
                with self.assertRaises(ValueError): target.check_rows(raw,spec)
            rows=raw_rows(spec); valid=certificate_text(rows)
            bads=(valid+"complexity_certificate_v2 {}\n",valid+"prefix complexity_certificate_v2 {}\n",valid.replace("_v1 ","_v2 ",1),
                  valid.replace('"n": 1024','"n": 1024.0',1),"\n".join(valid.splitlines()[1:]))
            for bad in bads:
                log.write_text(bad)
                with self.assertRaises(ValueError): target.certificates(log,rows)
            with self.assertRaises(ValueError): target.strict_json('{"x":1,"x":2}')
            with self.assertRaises(ValueError): target.strict_json('{"x":NaN}')
            with self.assertRaises(ValueError): target.strict_json('{"x":1e999}')
            with self.assertRaises(ValueError): target.exact({"x":[1]}, {"x":[True]}, "typed nested metadata")

    def test_complete_mock_capture_reload_and_artifact_drift(self):
        with fixture() as (root,args,factory,sampler):
            target.capture(args,sampler=sampler,popen=factory)
            info,curves,bound=target.load(args.output)
            self.assertEqual((len(factory.children),len(curves),info["checked_raw_rows"]),(24,24,2376))
            self.assertTrue(all(process.returncode == 0 for process in factory.children))
            self.assertTrue(all(item["group_exit_verification"]["members"] == [] for item in curves))
            self.assertFalse(info["native_process_may_still_be_running"])
            original=Path(curves[0]["raw_csv"]).read_text()
            Path(curves[0]["raw_csv"]).write_text(original+"\n")
            with self.assertRaises(ValueError): target.load(args.output)
            Path(curves[0]["raw_csv"]).write_text(original)
            info["captures"][1]["spec"]=info["captures"][0]["spec"]
            args.output.write_text(json.dumps(info))
            with self.assertRaises(ValueError): target.load(args.output)

    def test_bad_native_output_stops_after_one_and_final_reload_records_failure(self):
        with fixture(Factory(lambda rows: rows.pop())) as (root,args,factory,sampler):
            with self.assertRaises(ValueError): target.capture(args,sampler=sampler,popen=factory)
            failed=target.read_json(args.output)
            self.assertEqual(failed["validation"],"failed"); self.assertEqual(len(factory.children),1)
            self.assertEqual(failed["captures"][0]["group_exit_verification"]["members"],[])
        with fixture() as (root,args,factory,sampler):
            with mock.patch.object(target,"load",side_effect=ValueError("synthetic terminal rejection")):
                with self.assertRaises(ValueError): target.capture(args,sampler=sampler,popen=factory)
            failed=target.read_json(args.output)
            self.assertEqual(failed["validation"],"failed"); self.assertIn("terminal rejection",failed["error"])

    def test_deadline_rejects_successful_late_exit_and_reload(self):
        with fixture() as (root,args,factory,sampler):
            with mock.patch.object(target,"DEADLINE_SECONDS",-1),mock.patch.object(target.monitor,"bounded_terminate",return_value=dict(
                    native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)):
                with self.assertRaises(ValueError): target.capture(args,sampler=sampler,popen=factory)
            self.assertEqual(len(factory.children),1)
        with fixture() as (root,args,factory,sampler):
            real_now=target.time.monotonic_ns
            def late_clock():
                exited=bool(factory.children and factory.children[0].returncode is not None)
                return real_now()+(3_601_000_000_000 if exited else 0)
            with mock.patch.object(target.time,"monotonic_ns",side_effect=late_clock),mock.patch.object(target.monitor,"bounded_terminate",return_value=dict(
                    native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)):
                with self.assertRaisesRegex(ValueError,"beyond deadline"): target.capture(args,sampler=sampler,popen=factory)
            failed=target.read_json(args.output)
            self.assertEqual(len(factory.children),1); self.assertEqual(failed["validation"],"failed")
        item=dict(process_group=1,started_monotonic_ns=10,finished_monotonic_ns=3_600_000_000_030,
                  wrapper_exit_monotonic_ns=3_600_000_000_011,rss_log="/unused")
        observation=dict(process_group=1,monotonic_ns=3_600_000_000_020,validation="pass",members=[])
        item["group_exit_verification"]=observation
        with mock.patch.object(target.analysis,"check_rss",return_value=[observation]),mock.patch.object(target.monitor,"validate_monitor"):
            with self.assertRaisesRegex(ValueError,"deadline"): target.resources(item)

    def test_guarded_cleanup_repeated_signal_and_unknown_are_preserved(self):
        original=signal.getsignal(signal.SIGTERM)
        for known in (False,True):
            info=dict(cleanup=[],native_process_may_still_be_running=False)
            def cleanup(process,sampler):
                self.assertEqual(signal.getsignal(signal.SIGTERM),signal.SIG_IGN)
                if not known: raise KeyboardInterrupt("synthetic interrupted cleanup")
                return dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)
            with mock.patch.object(target.monitor,"bounded_terminate",side_effect=cleanup):
                target.cleanup_owned_group(None,None,info)
            self.assertEqual(info["native_process_may_still_be_running"],not known)
            self.assertEqual(signal.getsignal(signal.SIGTERM),original)
        info=dict(cleanup=[],native_process_may_still_be_running=True)
        with mock.patch.object(target.monitor,"bounded_terminate",return_value=dict(
                native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)):
            target.cleanup_owned_group(None,None,info)
        self.assertTrue(info["native_process_may_still_be_running"])

    def test_flags_are_retained_and_missing_real_build_gate_fails(self):
        spec=declared_schedule()[0]; rows=raw_rows(spec)
        rows[0]["utc_end_ns"]=rows[0]["utc_start_ns"]-1
        rows[1]["elapsed_ns"]+=3_000_000_000
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); raw=root/"raw.csv"; write_rows(raw,rows)
            actual,flags=target.check_rows(raw,spec)
            self.assertEqual(len(actual),99); self.assertTrue(any(row["diagnostic_flags"] for row in flags))
            self.assertTrue(all(row["excluded"] is False for row in flags))
            for name in ("collect.py","current_complexity.cpp","PROTOCOL.md","analyze_complexity.py"):
                (root/name).write_text("synthetic source\n")
            with mock.patch.object(target,"HERE",root):
                with self.assertRaisesRegex(ValueError,"validate_build.py"): target.source_inventory()


if __name__ == "__main__": unittest.main()
