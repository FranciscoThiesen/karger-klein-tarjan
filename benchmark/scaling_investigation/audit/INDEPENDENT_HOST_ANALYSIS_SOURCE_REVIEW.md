# Host calibration analyzer: source review

Source review PASS for `analyze_host_memory.py`; no import, native probe, plot or timing-data analysis was executed by this reviewer. Actual execution and visual QA remain separate gates.

Reviewed source SHA-256: `ae6a60b4e53d742b351d5265be50fda26cfee9fa27dd867c3d80863b233531b9`.

The loader reconstructs the seven exact build/inspection commands and two ordered execution commands; checks their receipt identities, complete resource intervals, log digests and required source/compiler/SDK/binary/log bindings; and retains the original run/build inventory. Fixed 224-record identity/clock/result checks are reused from the already reviewed row parser. Cross-order fingerprints and per-mode result positions/checksums are checked across all eight repeats.

The arithmetic keeps all 224 records, including 56 warmups. Its 112 order/footprint/mode/clock summaries each retain the three timed integers plus min/median/max, divided by the fixed 16,777,224 logical-load denominator. No timing from array construction or validation is added. Optional two-panel plotting is guarded by `--plot`, keeps eight series per clock and every timed observation/range, and labels the observed chase loop/position-store overhead. These artificial patterns cannot establish KKT cache misses, pure load latency or runtime attribution. The independent actual-assembly note supplies the machine-code review for build01.
