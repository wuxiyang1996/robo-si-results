# DR native sandbox

See `../../infra/planning/disk-rotation-family/RELEASE-0.2.md` for release scope, commands and limitations.

`launch.py` uses the shared launcher/server/verifier unchanged. `trusted/factory.py` builds the original physical task and adds cameras fixed relative to end-effector frames and the Stretch head optical frame. `world.py` accepts bounded joint targets, records every physical substep and offers no reference-state endpoint. `verify.py` independently recomputes predicates. `bundle.py` enforces an explicit six-file public allowlist.

`runtime.py` provides rootless Podman. `linux_container.py` uses an exported OCI filesystem with Bubblewrap on Linux clusters without subordinate UID mappings. It isolates mount/user/PID/IPC/UTS/network namespaces, drops capabilities, mounts the root and SDK read-only, clears environment variables, exposes only a writable delivery plus authenticated Unix socket, and applies resource/wall-time limits. Agent sessions get no external network or host paths. The actual runtime and rootfs digest are recorded in the run's image identity. Host-wide resource pressure can cause a launch to fail; failures never silently fall back to process evaluation.

The `replay.py` test is a public reference actuator-tape integration witness, not an independent agent baseline. `noop.py` and `escape_probes.py` are interface tests. Planning labels are untrusted agent statements whose exact physical intervals are retained, not automatically interpreted as successful planning.
