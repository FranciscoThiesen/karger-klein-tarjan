# Independent source review: lower-density work outer controller

Reviewer: `/root/multigraph_design`. Status: source review PASS, 2026-10-15.

Reviewed the prepared `work/run_capture_attempt.py` and
`work/test_run_capture_attempt.py` against the work protocol and collector
interface. The complete schedule is literal and includes both density ladders,
adjacent family twins and the reversed second graph order. Success requires 60
strictly reloaded inputs, 180 solver records, 120 comparator replay chains,
the supplied real freeze digest, unique child groups with affirmative empty
observations and the collector's actual zero exit. A zero exit by itself does
not establish detached-native completion.

The 108,600-second budget is a complete-interval safety ceiling, not a runtime
prediction. It leaves the inherited 1,800-second per-input deadline and 40 GiB
sampled native RSS rule unchanged. The outer watcher bounds the collector; it
does not claim to sample detached native groups' RSS itself. Post-wait and final
interval checks, remaining-budget completion proof, existing-timer rejection,
bounded cleanup and signal-handler restoration remain explicit. Attempts and
evidence paths are exclusive, and failure preserves actual exit status and
uncertain detached-child state.

One source finding was corrected and reread: uncertainty is now set immediately
before `Popen`, so an interruption after a possible spawn or during subsequent
PID metadata access cannot retain a false no-native-process flag. The fifth
prepared mock group covers both interruptions, plus uncertain outer cleanup,
and requires failure, retained uncertainty and no completion proof. The other
groups cover release and identity gates, all counts and groups, actual exit plus
strict proof, late completion, evidence reuse, cleanup failures and timer/signal
restoration. Six groups are prepared in total.

No source blocker remains. No module was imported, no test or subprocess was
launched, no source hash walk was performed and no partial timing output was
read. Hash-bound installation, executed mocked gates, complete diagnostic capture
and actual independent counter audit remain future release gates. This receipt
does not authorize native execution.
