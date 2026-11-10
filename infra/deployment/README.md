# Windows / Linux deployment kit

[中文说明](README-zh.md)

Pinned downloads, integrity checks, environment installation and separate runtime plans for **10 full archives covering 11 published tasks**. H1 is excluded. The kit targets x86-64 Windows and Linux with NVIDIA GPUs, using **Python 3.12.7** and separate hashed dependency locks. [validation.json](validation.json) records measured results, including failures. Original task completion scopes are unchanged.

`check` verifies sources, assets and imports. `run` executes physics. Successful process exit alone does not certify task success: inspect the verdict, alarms, stages and recording. Fresh environments on the author's computer do not constitute independent-machine or second-person acceptance.

## Install and run

Both GitHub and Hugging Face sources are private; the deployment account needs access to both. Authenticate GitHub CLI with `gh auth login`; set `HF_TOKEN` or use HF's saved token. Credentials are not logged or forwarded across domains.

Windows needs the x64 [Microsoft Visual C++ v14 runtime](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist), which [PyTorch's Windows guidance](https://docs.pytorch.org/docs/main/notes/windows.html) identifies as a system dependency. The tested host has v14.51.36247.00. GPU containers on Windows use [Docker Desktop's WSL2 backend](https://docs.docker.com/desktop/features/gpu/); native Linux Docker needs the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). Install these host prerequisites before the Python bootstrap. Host drivers, Docker and system runtimes are separate from the Python locks.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) **0.12.5**. Full archives total approximately **6.25 GB**; reserve at least 60 GB for extraction, dependencies and recordings, plus additional Docker storage. [catalog.json](catalog.json) pins archive URLs, sizes and SHA-256 values. Review-only archives cannot replace full archives.

Without an existing Python installation:

```powershell
./bootstrap.ps1 -Action install -RootPath C:/rs
./bootstrap.ps1 -Action prepare -RootPath C:/rs -Task all
./bootstrap.ps1 -Action check -RootPath C:/rs -Task all
./bootstrap.ps1 -Action run -RootPath C:/rs -Task M2 -RunName test-01
```

```sh
bash bootstrap.sh install --root /data/rs
bash bootstrap.sh prepare --root /data/rs --task all
bash bootstrap.sh check --root /data/rs --task all
bash bootstrap.sh run --root /data/rs --task M2 --run-name test-01
```

With Python 3.12+ available, call `python deploy.py ACTION` with the same `--root`, `--task` and `--run-name` arguments. `list` lists archives; `plan` prints exact commands. To use a downloaded ZIP, add `--archive PATH` to `prepare --task TASK`; size/hash checks remain. Existing package and run directories are preserved: use new roots or run names.

On shared computers, pass `--queue PATH` to `run`, using the existing resource queue adapter accepting `-- COMMAND`; keep its capacity unchanged. Dedicated machines can omit it. `check` does not run physics.

Windows should use a short root such as `C:/rs`. Linux needs glibc 2.35+, compatible NVIDIA drivers and EGL/OpenGL libraries; the Dockerfile lists the tested libraries. Do not replace drivers on an existing shared workstation during installation.

For a native Ubuntu 22.04 / Debian 12 installation, install the system libraries before `check`:

```sh
sudo apt-get update
sudo apt-get install -y ca-certificates libegl1 libgl1 libglib2.0-0 libgomp1 libxrender1 libxext6 libsm6 libopengl0 libglx0 fonts-dejavu-core ffmpeg
```

For M1 and M2 RPC, `docker info --format '{{.OSType}}'` must return `linux`. On Windows, start Docker Desktop with its WSL2 Linux engine; on native Linux use the host Docker service. The launcher checks this before starting physics.

## Linux container

The Dockerfile pins the official Python 3.12.7 / Debian 12 image by digest and installs the Linux lock plus rendering libraries. The host needs GPU-enabled Docker / NVIDIA Container Toolkit; Windows Docker Desktop uses its WSL2 Linux engine. Tokens, task archives and historical simulation caches are not embedded.

```sh
docker build -t robo-si-deployment:portable-20261025 .
# Prepare /data/rs first; replace /path/to/deployment with this kit directory.
docker run --rm --gpus all --shm-size 2g \
  -v /path/to/deployment:/kit:ro -v /data/rs:/work \
  robo-si-deployment:portable-20261025 \
  python /kit/deploy.py check --root /work --python /opt/venv/bin/python --task all
docker run --rm --gpus all --shm-size 2g \
  -v /path/to/deployment:/kit:ro -v /data/rs:/work \
  robo-si-deployment:portable-20261025 \
  python /kit/runtime_probe.py --physics --out /work/linux-physics.json
```

On Windows use absolute Windows paths on the left side of mounts. The probe checks CUDA, 100 physics steps and one actual rendered frame; it does not certify a task. To execute a reference in the container, replace `check` with `run --run-name test-01`.

**M1's sandbox and M2's RPC replay need the host Docker service. Run them in the locked Windows/Linux host venv; do not mount the Docker socket into the reference container.** M2 privileged capture can run directly in the runtime container.

On Linux, the kit connects the existing socat forwarder through a local Unix socket to the unchanged loopback-only worker. Only the forwarder receives that socket mount. The agent retains its private internal network, token authentication and original restrictions. The forwarder image is pinned by digest on both OSes. Runtime kernel caches are kept under the selected deployment root.

## Repairs and retained limits

| Task | Repair | Scope |
| --- | --- | --- |
| M1 | Windows/Linux and agent-image dependency locks; frozen source checks | CPU, privileged layer 1 reference; no automatic human signatures. |
| M2 | Portable root/interpreter; 211 source + 2 delivery files and 3 solver hashes checked; missing materials restored | Fixed 0.25 kg object / 1.8 m corridor. The 9 kg task is unfinished. Capture and RPC remain separate evidence. |
| Hanoi / Assembly | Seven shared metadata files restored; Assembly uses the published first-layer scene and `closed_loop:run` qualification entry | Separate frozen runtimes remain separate. Legacy nominal trajectory replay is not the first-layer deployment entry. |
| H4 | Missing video writer, asset generator and licensed assets supplied; current publication sources bound to new runs | Seven of 12 differing historical source variants recovered; five remain missing. New runs do not reconstruct all historical environments. |
| H2 / H5 / H6 | Nested H2 archive expanded; frozen hashes and representative published commands | Original layer, development mechanism and fixed-parameter restrictions remain; not every coverage case is rerun. |
| H3 | Frozen runtime; no-prop and heavy-prop references plus independent rejudging; Linux heavy-prop uses deterministic strict math | Native privileged reference; no isolated dual-agent interface. Original Linux heavy-prop drift failure retained; controller, timestep and limits unchanged. |
| M3 | Windows keeps its published entry; Linux uses a validated portable feedback/return adapter with four licensed WBC files and source hashes | hooks-v0.1, shelf-supported retrieval, privileged reference; no fully airborne retrieval or ordinary RPC claim. |
| M4 | Source/assets checked; Linux base uses the existing public controller option `--ctl '{"v_arc": 0.10}'` instead of 0.15; Windows base and both hard presets retain published controls | Original Linux base failed the 50 mm slip limit. The slower turn is a separately recorded deployment configuration; limits/scoring are unchanged. Autonomous docking remains unfinished. |

Linux M3 uses feedback walking, measured torso/payload-relative arm targets and a collision-aware whole-body return path. The eight-second swing leaves time for the unchanged floor-release and goal-settling checks within the original 420-second limit. The full run starts from the normal initial scene with no state restoration, scores 1.0 and completes with no alarms. This is a headless full physical reference; the original Windows video remains available, but a new successful full Linux recording is not certified. `m3-runtime-provenance.json` binds the portable entry and helpers byte-for-byte to the validated run; `supplements/m3-wbc/manifest.json` records the model files and license. Checkpoint diagnostics, including a score-1.0 run that timed out before controller completion, remain excluded from full-task counts.

Provenance and hashes are in `m2-adapter-provenance.json` and `supplements/*-manifest.json`. Original ZIPs and historical verdicts remain unchanged. H4 recovery is documented in `h4-source-recovery.json`.

Linux Hanoi uses the published qualification scenes and controller for 3, 4 and 5 disks, with Genesis deterministic algorithms and debug strict math enabled. The qualifier evaluates the new run and its local action replay. This numerical runtime profile changes neither the integration timestep nor task limits; it does not assert bitwise equivalence to Windows history. The original Linux trajectory comparisons and NaN failure are retained. Windows keeps its passing strict reference entry. Consult `validation.json` for the qualification results actually completed.

Linux H3's heavy-prop profile completed in 169.66 s and passed the independent delivery and support-route audit. `h3-runtime-provenance.json` binds the deployed adapter to that run; only its module description differs from the validated wrapper, with an identical executable AST. Windows H3 and Linux no-prop retain their original runtime profiles.

Linux H6 also uses deterministic strict math with its original controller. Its full physical reference passed at **585.87 s, score 1.0**, non-VOID, with no alarms or privileged state writes: all 20 route checks, placement, release and standing hold completed. The default Linux entry uses the original `--no-video` option; this result does **not** certify a new full Linux recording. Windows retains its validated recorded entry. `h6-runtime-provenance.json` binds the portable wrapper to the tested numerical initialization and verification functions. To request a new Linux recording, use the command from `plan` and omit `--no-video`; that optional recording still needs validation. The existing development-handles task scope and 600 s limit remain unchanged.

H5's video adapter continuously drains FFmpeg stderr, which the original writer read only after closing. WSL2 containers may use software EGL even when CUDA is available. The original, single-thread and no-shadow recordings stalled and are retained. A separate headless diagnostic completed all five scoring stages with score 1.0 at 150.92 s, non-VOID; this isolates the remaining issue to the video/render path and is excluded from the complete recorded-reference pass count. The official Debian Bookworm Mesa 25.0.7 backport completed the full textured recording: score 1.0, 150.94 s, all five stages, non-VOID and no alarms. The Dockerfile pins that backport. Native Linux software-EGL installations should use Mesa 25.0.7 or later; the pinned container is the tested option. This does not change the host GPU driver. Frozen task sources, controls and scoring remain unchanged.

M1 `run` selects the fully locked agent image. M2 `run` performs privileged capture. Generate commands in the **same target environment** before its separate RPC flow: replaying Windows-captured commands on Linux completed the interface exchange but scored only 0.3. The original payload is retained for historical comparison.

```powershell
# First complete deploy.py run --task M2 --run-name test-01 on this environment.
# On shared hosts append --queue PATH to both commands.
C:/rs/venv/Scripts/python.exe replay_capture.py --runtime C:/rs/runtimes/m2 --capture C:/rs/runs/m2-test-01 --name rpc-local-01
```

On Linux use `/data/rs/venv/bin/python` and corresponding paths. The helper requires a successful, RPC-initialized capture, verifies the commands and replay client, and delivers only those two files. It checks the new RPC verdict separately. This remains an open-loop interface comparison, not a sensor-only solution. The locked Dockerfile creates a new content-addressed image tag without replacing historical images. Root dependency versions are retained; transitive dependencies are locked. Optional LLM CLIs are excluded. Original runtime network, privilege, resource and action constraints remain.

## Acceptance on another machine

Run `check --task all`, the physics/render probe and each reference through the host's resource queue. Preserve `checks/`, `logs/`, `runs/` and installation receipts. Record OS, GPU, driver, Docker version and lock hashes. Review actual verdicts, alarms, stages and videos, then complete the original repeat, coverage, manual review and independent-reproduction gates. Preserve failed attempts and retry with new names.
