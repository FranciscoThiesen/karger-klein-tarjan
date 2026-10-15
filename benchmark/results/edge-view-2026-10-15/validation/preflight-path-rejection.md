# Rejected preflight path

The first root preflight invocation supplied the copied parent freeze in this worktree. The build record binds the original absolute path in `kkt-retention-control`; preflight correctly rejected the mismatch with `ValueError: timing build: incorrect parent_control_freeze`. No freeze or native execution resulted. The corrected invocation supplied the recorded original path and passed. Neither input hashes nor validation checks were changed.
