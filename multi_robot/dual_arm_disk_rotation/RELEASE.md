# Reproduce the approved 0.1.0 native reference

Version 0.1.0 is the user-approved stable reference release. Consult
`validation/release-readiness.json` for the measured cohort, replay checks,
representation mappings, tests and remaining formal gates. The explicit approval is recorded in `validation/release-approval.json`.
The original 0.1.0-rc1 archive is promoted without changing its verified bytes;
archived unsigned/unpublished fields are historical. Independent-person
reproduction remains unperformed.

The recorded runtime is Python 3.12.14, Genesis 1.4.3, PyTorch 2.11.0+cu128,
NumPy 2.5.3, SciPy 1.18.1 and MuJoCo 3.14.0. Physics and rendering run on
Gamma NVIDIA GPUs. The engine's model-bias accessor is version-specific and is
covered by source/runtime identity checks. The simulator requires its normal
NVIDIA driver, CUDA and headless OpenGL/EGL dependencies. On Gamma the tested
interpreter is `/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python`.

From a fresh Python 3.12 environment with the corresponding CUDA driver:

```bash
python -m pip install torch==2.11.0+cu128 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r multi_robot/dual_arm_disk_rotation/requirements.txt
```

For an unpacked archive, first enter its top directory and run
`sha256sum -c SHA256SUMS`, then `cd workspace`. The two task pages are
`infra/task-disk-rotation-zh.html` and `infra/task-disk-rotation-en.html`.
Media paths are relative and can be opened offline.

```bash
python -m unittest discover -s tests -p test_disk_rotation.py

python -m multi_robot.dual_arm_disk_rotation.solution.run \
  --config multi_robot/dual_arm_disk_rotation/validation/configs/nominal_ccw.json \
  --output /tmp/disk-rotation-fresh --video
python -m multi_robot.dual_arm_disk_rotation.solution.verify /tmp/disk-rotation-fresh

python -m multi_robot.dual_arm_disk_rotation.solution.run \
  --replay multi_robot/dual_arm_disk_rotation/validation/release-0.1.0-rc1/nominal_ccw/repeat-1/trajectory.npz \
  --output /tmp/disk-rotation-independent-replay --video
python -m multi_robot.dual_arm_disk_rotation.solution.verify /tmp/disk-rotation-independent-replay
```

Repeat the commands with `wrap_cw` to test the negative rotation crossing the
wrapped heading boundary. Each new output must be absent before execution.
Archive replays reproduce the recorded commands, not a new feedback-planning
decision; fresh expert runs test the controller separately.

The first asset generation is already included. Regenerating with
`python -m multi_robot.dual_arm_disk_rotation.assets` should produce the same
URDF/OBJ bytes; edited assets cannot inherit old witness certificates.

Representative selections and ablations are recorded before execution in
`validation/representative_plan.json`. All development attempts and ablations
are retained in `validation/attempts.json`; development probes with incomplete
provenance are explicitly excluded from release witness counts.

The user explicitly approved the scoped reference and publication materials.
No independent-person reproduction or secure evaluation container is inferred
from this approval. Isolated-agent benchmark admission remains a separate
technical scope.

## Git checkout and full evidence

Git contains the executable reference and compact audit metadata. Raw trajectories,
contacts, recordings and execution snapshots are in the release archive. A source-only
checkout runs 18 tests and explicitly skips two full-witness tamper tests. Unpack the
reference archive to run all 20 checks and audit recorded trajectories. The archive is
an immutable packaging-time snapshot; its unpublished flags are historical. Consult
the current `delivery.json` and GitHub release for remote publication status.
