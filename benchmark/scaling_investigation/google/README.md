# Execution handoff: fresh Google comparison

Source preparation only. Do not execute until root releases the relevant phase.
No installed library download or rebuild is needed. Use fresh destinations;
retain any failed attempt and increment its suffix rather than overwriting it.

Focused mocked gates (six groups, no native execution):

```sh
/usr/bin/python3 -B benchmark/scaling_investigation/google/test_run_google.py
```

Build the common main and two executables after the checked candidate build:

```sh
/usr/bin/python3 -B benchmark/scaling_investigation/google/run_google.py build \
  .build/scaling-investigation/depth-google-build01 \
  --candidate-build .build/scaling-investigation/depth-build01/build.json --released
```

Then, only after the three actual gates and a quiet performance release:

```sh
/usr/bin/python3 -B benchmark/scaling_investigation/google/run_google.py capture \
  benchmark/results/scaling-investigation-2026-10-15/depth-google01 \
  --build .build/scaling-investigation/depth-google-build01/build.json \
  --gate benchmark/results/scaling-investigation-2026-10-15/depth-smoke01/capture.json \
  --gate benchmark/results/scaling-investigation-2026-10-15/depth-work01/capture.json \
  --gate benchmark/results/scaling-investigation-2026-10-15/depth-correctness01/gate.json \
  --released
```

The correctness gate path must name its actual successful attempt if its suffix
differs. The runner rejects different candidate-build identities. Root archives
the controller's real tool exit as well as every owned child receipt; an empty
controller process group alone is not proof of detached child exit.

Strict reanalysis, which performs no solver calls:

```sh
/usr/bin/python3 -B benchmark/scaling_investigation/google/run_google.py check \
  benchmark/results/scaling-investigation-2026-10-15/depth-google01/capture.json
```

`load(path)` returns `(info, rows, bound_sha256)`. `rows` retains all 594 raw calls
with an added policy; raw native files remain unchanged. Each `info.captures`
entry retains the exact library `BigO` and `RMS` rows plus every native clock
diagnostic and certificate. There is no trimming or historical-time pooling.
The library schema is checked against the real previously validated v1.5.2
schema on every new curve; unsupported output fails the attempt.

The existing library/driver evidence is copied nowhere and altered nowhere.
The new runner validates the original immutable full proof inventory from its
known completed capture, then binds fresh candidate objects/main/binaries and
new command receipts. This deliberately does not call the old collector's
restricted `load()` on new binaries or alter its fixed schedule/flags/globals.
