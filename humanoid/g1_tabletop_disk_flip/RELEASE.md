# G1 gentle disk flip · 0.1.0-rc1

Reference release candidate, 2026-10-26. Six fresh complete executions (three each
at two declared configurations) and two independent video replays passed.
The robot gently slides the disk to the table edge, pinches with both hands,
lifts and inverts it, then transfers support to the table and releases it.

The hierarchical addendum packet is
`g1-disk-flip-0.1.0-rc1-hierarchical.tar.gz`. It includes the original complete
measurement records, 26/27 low-level segments, frozen generating sources and
the interactive plan-to-trajectory page. The earlier `0.1.0-rc1` archive remains
immutable. No new physical success or formal admission is claimed by this addendum.

This is a fixed-pelvis reference implementation. Human video review is unsigned,
isolated sandbox integration is unverified, and formal admission remains false.
The two observed configurations do not certify a continuous skill range.

## Open the offline packet

Extract the hierarchical addendum packet. Inside the extracted directory, open:

`workspace/humanoid/g1_tabletop_disk_flip/validation/hierarchical/index.html`

Both videos, phase controls, measured skill states, six trajectories and two
replay trajectories are local. The packet includes frozen execution sources,
current reproduction tools, robot meshes with the Unitree license, and all 61
completed development-attempt summaries plus 107 checkpoint-fragment summaries.
The two mapped complete measurement traces are included as gzip files. Other
raw development traces remain in the original workspace; fragment successes
never count as complete task evidence. The six selected final-policy runs are
identified explicitly in `validation/representative_plan.json`.

Before extraction, check the archive with its neighboring `.sha256` file. After
extraction, verify every packet file from the extracted directory:

```bash
sha256sum -c SHA256SUMS
cd workspace
```

## Reproduce

Use Python 3.12.14 with Genesis 1.4.3, PyTorch 2.11.0+cu128, NumPy 2.5.3,
MuJoCo 3.14.0 and SciPy 1.18.1. Start with `requirements-genesis.txt`; install the
recorded PyTorch CUDA build and SciPy version. The CPU physics path was tested.
Runtime mismatches remain explicit unknowns in evidence-backed screening.

```bash
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 PYTHONPATH=.
export PYOPENGL_PLATFORM=egl  # headless video rendering
python -m humanoid.g1_tabletop_disk_flip.solution.run \
  --config humanoid/g1_tabletop_disk_flip/validation/configs/nominal.json \
  --seed 0 --output my-fresh-nominal
python -m humanoid.g1_tabletop_disk_flip.solution.run \
  --replay humanoid/g1_tabletop_disk_flip/validation/release/nominal/repeat-1/trajectory.npz \
  --video --output my-independent-replay
python -m humanoid.g1_tabletop_disk_flip.solution.oracle \
  --count 10 --seed 0 --output my-screening.json
python -m unittest tests.test_tabletop_disk_flip tests.test_disk_flip_oracle
python -m humanoid.g1_tabletop_disk_flip.solution.hierarchy --verify
```

All output paths must be new. The offset case uses `configs/offset_y_003.json`
and seed 1. Fresh success takes 457.305 or 478.925 simulated seconds; wall time
depends on CPU and rendering. No precomputed trajectory is required by the
fresh controller or by per-instance screening.

The default oracle returns plans, skill constraints, key states and checks.
The ten recorded development draws passed screening only. The four-status
contract fixture includes an exact execution witness, a new draw at the same
configuration, an unvalidated offset, and a necessary weight-limit failure;
all four are retained. It is not an external benchmark score.

## Build another packet from the source workspace

```bash
python -m humanoid.g1_tabletop_disk_flip.solution.package_release \
  --output humanoid/g1_tabletop_disk_flip/solution/runs/g1-disk-flip-0.1.0-rc1-hierarchical
```

The packager verifies the evidence, source identities, robot assets and runtime
before copying only this task and its dependencies. It writes a file manifest,
checksums and a compressed archive. It neither publishes remotely nor grants
formal admission.
