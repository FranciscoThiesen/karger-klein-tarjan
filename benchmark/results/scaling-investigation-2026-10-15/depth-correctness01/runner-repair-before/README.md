# Preserved first correctness attempt

Root reported that attempt01 stopped at the retention-control main's explicit timing-only compile guard. No success receipt is synthesized. The existing gate, children and logs remain untouched.

The saved `run_correctness.py` is the exact original runner, SHA-256 `f42304ab6b76a03ee613b419b21d82f9165ce173e12780c30d74776aeebc84b7`, checked directly after copying. The repair gives the retention suite uninstrumented production objects **and** an uninstrumented main under both toolchains, preserving its compile guard. The edge-view and focused suites retain work counters. No production source, native test source, or candidate build object is changed by this runner-only repair.
