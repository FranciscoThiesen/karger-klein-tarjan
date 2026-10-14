# Interrupted-prefix power correlation

1800 native calls retained; 1 overlap a nominal logged Sleep–Wake/DarkWake interval; 149 carry clock flags. These counts include checked warmups. Original B remains failed. No performance observation is adjusted or removed.

Timestamp correlation only; no call excluded or corrected. The failed wrapper interval includes a post-native sampler stall and is not solver elapsed time. Sleep-to-first-Wake/DarkWake intervals are logged transitions, not measured CPU inactivity. One-second timestamp resolution, missing/reversed records and UTC reversals limit attribution. Absence of events does not prove stable frequency, no contention or a quiet host. Sleep inhibition was not verified; retained caffeinate failure records remain applicable.

The full machine power history and complete event inventory remain local and ignored. Published audit.json scopes events to these calls and their enclosing sleep intervals; it retains full-source hashes.
