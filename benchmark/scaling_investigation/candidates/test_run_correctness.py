#!/usr/bin/env python3
"""Parser regressions from preserved native outputs; never launches a child."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('depth_correctness_parser', HERE/'run_correctness.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
ACTUAL = runner.ROOT/'benchmark/results/scaling-investigation-2026-10-15/depth-correctness02/native'
HASHES = {
    'positive-depth.stdout': '9db50808f7afc5b0c35e0be791fb032f502d257243db497ab26c6c238bd6c82c',
    'positive-depth.stderr': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'positive-edge_verifier_view_test.stdout': '9857cb77da439131b0bded0544652d6757c153f697e2ff2edc25ba63dcfcb708',
    'positive-edge_verifier_view_test.stderr': '3c849bfdd4f9dd7ef1cbdf8178aa97569f7dbf9f295a03769cd1ad6b3b15afa1',
    'positive-retention_control_test.stdout': 'c78a19429e336daea96bb1b58a22d01debc03646d8990bf98e560bf3cea765bf',
    'positive-retention_control_test.stderr': '40a49d6baa7e54af623b4503a0e28ae43814a6bd6bb7a578ef033175feb3e7d0',
}


class ParserTests(unittest.TestCase):
    def actual(self, name):
        result = []
        for suffix in ('stdout', 'stderr'):
            key = 'positive-'+name+'.'+suffix
            data = (ACTUAL/key).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), HASHES[key])
            result.append(data.decode('utf-8'))
        return result

    def test_all_preserved_actual_positive_outputs(self):
        runner.check_focused(*self.actual('depth'))
        for name in ('edge_verifier_view_test', 'retention_control_test'):
            runner.check_suite(name, *self.actual(name))

    def test_each_retention_count_is_required(self):
        stdout, stderr = self.actual('retention_control_test')
        for field, value in (('simple_cases',28), ('solver_outputs',819), ('raw_cases',35),
                             ('exhaustive_cases',35), ('rejected_trees',140), ('rejected_options',10)):
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, 'retention suite did not complete'):
                runner.check_suite('retention_control_test',
                                   stdout.replace(field+'='+str(value), field+'='+str(value+1)), stderr)

    def test_only_exact_known_retention_stderr_is_accepted(self):
        stdout, stderr = self.actual('retention_control_test')
        altered = ('', stderr.splitlines(keepends=True)[0], stderr+stderr,
                   stderr.replace('=1', '=2', 1), stderr+'unexpected diagnostic\n',
                   'unexpected diagnostic\n'+stderr, stderr.rstrip('\n'), stderr+'\n')
        for value in altered:
            with self.subTest(stderr=value), self.assertRaisesRegex(RuntimeError, 'retention suite did not complete'):
                runner.check_suite('retention_control_test', stdout, value)

    def test_extra_stdout_and_other_suite_diagnostics_are_rejected(self):
        stdout, stderr = self.actual('retention_control_test')
        with self.assertRaisesRegex(RuntimeError, 'retention suite did not complete'):
            runner.check_suite('retention_control_test', stdout+'unexpected\n', stderr)
        stdout, stderr = self.actual('depth')
        with self.assertRaisesRegex(RuntimeError, 'focused positive output mismatch'):
            runner.check_focused(stdout, stderr+'unexpected\n')
        stdout, stderr = self.actual('edge_verifier_view_test')
        with self.assertRaisesRegex(RuntimeError, 'edge/full-KKT suite did not complete'):
            runner.check_suite('edge_verifier_view_test', stdout, stderr+'unexpected\n')


if __name__ == '__main__':
    unittest.main()
