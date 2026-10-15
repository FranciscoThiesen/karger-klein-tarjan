# KKT-only profiling attempt: unavailable thread-state sampling

The released attempt **failed before any KKT calls were started**. Input
generation and its independent certificate passed, then macOS `sample` reported
that it could not obtain the driver's thread state. The sampler exited before
attachment could be confirmed; the controller never sent the release byte.
It terminated the waiting driver and verified both owned process groups empty.
The [failed capture](capture/profile.json), [sampler error](capture/sample.stderr)
and controller log are preserved. No stack-based hotspot or runtime conclusion
can be drawn from this attempt. No permission escalation or retry was made.

The standalone driver compiled and linked successfully from the frozen eight
production objects; `profile-build.json` records native arm64 and a 512 MiB stack.
The new controller passed eight mocked lifecycle scenarios plus a no-release
gate, and independent source review. These checks launched no profiling driver
or sampler. Actual profiling status belongs to the capture's `profile.json`.
This is a diagnostic profile of one implementation and one held-out input,
not a performance comparison.

`kkt_profile.cpp` includes the unchanged six-solver harness with its existing
`KKT_RETENTION_HARNESS_NO_MAIN` switch. It reuses the complete fixture generator,
edge-count checks, input fingerprints, Kruskal reference and independent cycle
certificate. The fixture is `leaf_hierarchy4`, n=2,097,152, m=33,554,432, density
16, intrusion zero, graph seed **6000011**. The planned four KKT calls would use
seed **1423** each; none was released in the failed capture.
There is no unreported warmup, repeated-until-favorable selection, modified
fixture, or substitute solver. The reference oracle runs only before profiling.

The new driver is deeper than the frozen inventory's `*/*.cpp`/`*/*.hpp` patterns.
No production source, generator, certificate, frozen helper or frozen executable
is edited. `prepared-commands.json` contains the exact separate compile and link
argv arrays and the eight existing physical production object paths/digests. It
replaces only the old main object with this new driver object; the Edge-view
`kkt.o` and seven other production objects are reused, never rebuilt. The recipe
keeps Apple Clang 15, explicit `/usr/bin/arch -arm64`, the recorded SDK, C++17,
O3, assertions, and the 512 MiB executable stack. No work counters, sanitizers,
new production debug flags, or solver instrumentation are added.

## Build and execution after explicit release

The prepared controller implements the launch/monitor/cleanup sequence below,
using the unchanged bounded monitor and strict parent-freeze validator. Run it
only during the root-released quiet period, with a fresh output directory:

```text
python3 -B benchmark/results/edge-view-2026-10-15/profile/profile_controller.py --build-record benchmark/results/edge-view-2026-10-15/profile/profile-build.json --output benchmark/results/edge-view-2026-10-15/profile/capture --released
```

It requires a PID-specific `Sampling process <pid>` confirmation before sending
`G`; a missing or different confirmation fails closed. Partial attempts are
retained. Its RSS ceiling is the combined sampled sum of both owned groups.
The build log contains one expected unused-function warning from the included
frozen harness's CLI parser; no frozen source was changed to suppress it.

1. Verify the parent build-record hash, all eight object hashes, driver hash and
   unchanged frozen native sources. Refuse existing driver object/binary/output
   paths; preserve attempts separately. Execute `compile_command`, then
   `link_command` from `prepared-commands.json`, in its `working_directory`,
   keeping argv, exit statuses, logs, compiler identity and final hashes. Inspect
   the final Mach-O for arm64 and `LC_MAIN.stacksize=536870912`. This record is
   a prepared recipe, not evidence that those commands succeeded.
2. Launch the driver as an owned new process group, with a writable stdin pipe,
   persistent stdout/stderr logs, and the existing bounded process-group RSS
   monitor. Poll every two seconds, stop above the existing 40 GiB sampled cap,
   after three unavailable observations, or on a poisoned sampler. Do not use
   an unmonitored background shell launch. Keep the monitor active during graph
   generation and certification as well as profiling. The driver additionally
   limits itself to 600 CPU seconds, 900 wall seconds, and a 60-second release
   wait; these are not substitutes for RSS/lifecycle monitoring.
3. Wait for the flushed `profile_v1` **READY** record; verify its PID, full case,
   seeds, counts and `validation=pass`. No KKT call has started yet. Launch the
   sampler as another owned, bounded process group:

   ```text
   /usr/bin/sample <READY.pid> 60 1 -mayDie -file <profile-directory>/sample.txt
   ```

   Keep the sampler's stdout/stderr and enforce a 90-second tool deadline,
   including report generation. Send the single byte `G` to driver stdin only
   after attachment is confirmed. If attachment is rejected, unsupported, or
   cannot be confirmed, terminate both owned groups with bounded verification,
   preserve the error, and report profiling unavailable. No sudo, permission
   bypass, or fallback that changes the production objects is authorized here.
4. Retain the complete sample report, four `KKT_BEGIN`/`KKT_END` pairs, four
   `VALIDATED` markers and `DONE`, and require driver exit zero. Record sampler
   exit separately. A successful solver run alone is not a successful profile.
   Bound termination/reaping and verify both groups empty on every exit or
   failure; do not launch another child if cleanup cannot be verified. Hash all
   logs, report, resource observations and actual binary/build provenance.

## Boundaries and interpretation

`profile_kkt_public_boundary` includes tuple-to-`problem` conversion, production
KKT, its public unordered-set output construction, and temporary problem
destruction, matching the existing harness's KKT interval. Every result is
compared to the independently certified exact ID set afterward, between
`KKT_END` and `VALIDATED`, and is then released. No four-result accumulation is
introduced. The original input, reference tree and expected ID set remain alive;
the unused tuple-result membership lookup for the other five solvers is omitted.
Consequently this driver is not a reproduction of the six-solver process's
complete memory/cache history, and its elapsed times must not be substituted
for benchmark measurements.

Inspect stacks beneath the named KKT boundary for attribution. Retain and label
blocked handshake, marker I/O, validation, output destruction and final cleanup
stacks; do not silently count them as KKT or delete them from the raw report.
The one-millisecond sample interval can miss short functions. Samples are
periodic stack observations, not exact CPU instruction counts or memory-traffic
measurements. Optimized frozen objects may inline functions and lack source-line
debug information; do not rebuild them merely to obtain more detailed symbols.
Report partial coverage or unresolved frames honestly. Profiling perturbs the
process and provides no solver speedup or crossover evidence by itself.

Usage was checked read-only against the installed Apple manual
`/usr/share/man/man1/sample.1`: duration is seconds, interval is milliseconds,
`-mayDie` captures symbol locations early, and `-file` names the output. Actual
attachment capability remains unverified until the released run.
