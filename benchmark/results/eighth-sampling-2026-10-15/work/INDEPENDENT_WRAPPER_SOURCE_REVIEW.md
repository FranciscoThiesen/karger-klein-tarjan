# Independent outer diagnostic wrapper source review

Status: **PASS, source review only**. No module was imported, no test or native
program was executed, and no partial performance measurements were read.
Installation, actual execution and its completion receipt remain deferred until
root releases the diagnostic after the active timing capture.

Reviewed source SHA-256:

- `run_capture_attempt.py`: `cff7f2cff4e1feb3efcd3bcb5e90a2d06d16b65402b1d005def1bb2167f82b8b`
- Intended eighth `work/collect.py`: `4e3318902ca69e88a3e10098a402531eee1a3dd9d89a291cd4b2bba2a1b1419b`
- Previous spatial wrapper used for comparison: `07bc782b7e2318de53bbc9fbec6797b81b7dc558469029d175e86a4b99698565`

The new wrapper preserves the reviewed outer lifecycle and changes the module,
schema, documentation and completed cardinalities for the eighth study. The
exact `--released` argument and prospective work-freeze proof precede launch;
attempt paths are exclusive and retain stdout, stderr, source digests, invocation
and completion metadata. This is explicitly native diagnostic execution, with
`performance_execution=False`.

The 7,200-second outer deadline uses the remaining budget during waits and
checks the observed completion timestamp after exit. The Python collector is
placed in its own session. Cleanup suppresses SIGTERM only within the bounded
cleanup/proof section, restores the prior handler, and requires affirmative
native-exit, group-exit and no-possible-running-process fields. Cleanup errors
produce a failed receipt. An empty outer group alone cannot set the overall
success flag: `work.load` must also revalidate the complete 48-child capture,
including every detached native group's final empty observation, fixed schedule,
fingerprints, certificates, resource records and counter identities. That
validator returns 48 inputs with three solvers and two comparator replay chains
per input, agreeing with the wrapper's 144-output and 96-chain metadata.

The wrapper and work source/freeze hashes are rechecked before success. Failure
leaves `all_owned_groups_verified_empty=False`; it does not claim that cleanup of
the outer process proved the status of detached native children. No blocking
source defect was found. This review is not a substitute for the future actual
completion and strict diagnostic proof.
