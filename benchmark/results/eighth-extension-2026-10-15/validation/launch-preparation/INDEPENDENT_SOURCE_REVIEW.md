# Independent launch-helper source review

**SOURCE REVIEW PASS**, 2026-10-15, by `/root/multigraph_candidate`. No imports, syntax checks, tests, native execution or partial timing reads occurred. Runtime release and actual lifecycle proof remain separate.

| Source | SHA-256 |
|---|---|
| `run_capture_attempt.py` | `b324da2ad530e404b74e550579c9bf4e34630cc2281b784a5b94119a6b188116` |
| `machine_power.py` | `be4b52a9401a3d051e78ea9490585f16c21a34594d8bdeeab0a819bdb9ad4ab8` |

The launch wrapper pins the supplied completed source freeze and prospective 28-child declaration, retains exclusive command/stdout/stderr/receipt paths, enforces the 51,000-second outer deadline both while waiting and after observed completion, and invokes full strict reload before accepting all 1,176 outputs (1,008 timed, 168 warmups). It truthfully does not claim an additional per-child deadline. Native children remain under the unchanged collector's own resource/group guards. The outer sampler proves its own cleanup; success requires the inner strict proof for all detached native groups as well.

Repeated SIGTERM is suppressed only during bounded cleanup/final proof, the original handler is restored, and abnormal completion cannot claim all groups empty merely because the outer Python group exited. Complete source/input hashes are rechecked before PASS. Machine metadata has bounded queries, never equates an architecture query about Python with the separately proven solver architecture, and never claims verified sleep inhibition or thermal stability. Full power output is written only after its destination passes the private ignore rule.

One optional robustness suggestion was applied before this final hash receipt: metadata and pmset handlers now catch `OSError` as well as timeout, retaining failure evidence when a tool is unavailable. No further blocker was found in this source scope. The handoff document and future actual machine/capture evidence are outside this receipt's reviewed-source inventory.
