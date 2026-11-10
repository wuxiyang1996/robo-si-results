# G1 gentle tabletop disk flip

The reference controller has completed **6/6 fresh runs** across two declared
configurations, with three repeats per configuration. **2/2 independent action
replays** also pass. The [offline video review](validation/release/review.html)
and [release instructions](RELEASE.md) are ready. Formal benchmark admission
remains **false**; human review is unsigned.

A fixed-pelvis G1 with two Dex3 hands gently pushes an orange-side-up disk to the
table edge, grasps it with both hands, lifts and turns it blue-side up, and places
it fully back on the table. Both hands must release it for two stable seconds.
See the [public Chinese instruction](instruction.zh.md) and
[designer solution](solution/README.md).
Artifact locations and upload status are in [publication notes](PUBLICATION.md).

## Concrete hierarchical witness

The [plan-to-trajectory review](validation/hierarchical/index.html) and
[expanded plan](validation/hierarchical/README.md) reuse the existing nominal and
offset complete executions. Five high-level goals expand into 26 and 27 recorded
low-level segments, including preparation, hand reshaping, support transfer and
release. Each segment binds its frozen generating function, constraints, exact
command slice, timestamps and measured boundary states. The compressed original
traces preserve every measured control step for inspection within segments.

Acceptance here concerns **a plan implemented in a declared concrete case**:
high-level to low-level expansion, low-level to actual trajectory, high-level
goal completion on that trajectory, and one continuous complete expert execution.
The annotation was added retrospectively; the trajectory and controller are
unchanged. Generic rolling planning, arbitrary skill composition and random
robustness are separate extensions, not prerequisites for this witness. The
current controller's one-step planner is an implementation detail.

```bash
python -m humanoid.g1_tabletop_disk_flip.solution.hierarchy --verify
python -m unittest tests.test_disk_flip_hierarchy
```

The mapping is an addendum to the existing `0.1.0-rc1` evidence. It does not change
the earlier archive or grant formal admission. The interactive page uses the
verified independent replay of the same commands for segment playback.

## Declared reference scope

| Case | Disk start and goal XY (m) | Physics seed | Fresh runs | Completion time |
|---|---|---:|---:|---:|
| Nominal | `(0.50, 0)` | 0 | 3/3 | 457.305 s |
| Lateral offset | `(0.50, 0.003)` | 1 | 3/3 | 478.925 s |

The table is 0.86 m high, with its near edge at `x = 0.35 m`. The free disk is
200 mm in diameter, 12 mm thick and 120 g. It has two colored visual faces and one
closed convex 128-sided collision mesh. The controller uses 43 joint targets;
the pelvis is fixed. Whole-body locomotion and an isolated agent sandbox are not
part of this reference scope.

These are **two observed configurations**, not a validated continuous parameter
range. The [representative plan](validation/representative_plan.json) records the
selected cases, repetitions and policy revisions. Failed development attempts,
including the offset-case failures that motivated the last fixes, remain in the
[attempt ledger](validation/candidate_attempts.json). Checkpoint fragments are
listed separately and never count as fresh complete executions.

## Run and reproduce

Use the repository's [Genesis environment](../../requirements-genesis.txt) and
installed G1 assets. Commands run from the repository root and require a new
output directory:

```bash
python -m humanoid.g1_tabletop_disk_flip.solution.run \
  --config humanoid/g1_tabletop_disk_flip/validation/configs/nominal.json \
  --seed 0 --output humanoid/g1_tabletop_disk_flip/solution/runs/my-nominal

python -m humanoid.g1_tabletop_disk_flip.solution.run \
  --config humanoid/g1_tabletop_disk_flip/validation/configs/offset_y_003.json \
  --seed 1 --output humanoid/g1_tabletop_disk_flip/solution/runs/my-offset
```

`--video` records the physical run. Independent action replay constructs a fresh
scene and checks configuration, runtime, model assets, physics sources, command
count, final pose and completion. The release bundle provides trajectories with
their required neighboring metadata:

```bash
python -m humanoid.g1_tabletop_disk_flip.solution.run \
  --replay humanoid/g1_tabletop_disk_flip/validation/release/nominal/repeat-1/trajectory.npz \
  --video --output humanoid/g1_tabletop_disk_flip/solution/runs/my-replay
```

The tested runtime uses Python 3.12.14, Genesis 1.4.3, PyTorch 2.11.0+cu128,
NumPy 2.5.3, MuJoCo 3.14.0 and SciPy 1.18.1, with CPU physics. Recorded versions
and source/asset hashes are part of the evidence. A differing runtime cannot
silently inherit the observed skill certificates.

## Oracle contract

The default product is **a high-level plan, skill choices and constraints, key
states and bounded feasibility results**. The offline adapter does not launch a
simulator or generate a complete trajectory for each sample. At execution time,
`RollingPlanner(horizon=1)` derives each local joint target from measured state.

```bash
python -m humanoid.g1_tabletop_disk_flip.solution.oracle --count 10 --seed 0 \
  --output humanoid/g1_tabletop_disk_flip/solution/runs/screening.json
```

The CLI uses `validation/release` as its optional evidence root. Verified skill
entries match exact configuration parameters, seed, model assets and runtime;
missing or changed evidence remains unknown. Self-generated scenes prefer the
observed points once that bundle exists. Before then they use explicitly labelled
provisional design ranges. Sample extrema never become a certified interval.

For prescribed inputs, use `--instances samples.json --source benchmark_prescribed`.
Every input stays in order, with its own `sample_id`, including repeated equal
configurations, unknowns and failed checks. No replacement sampling occurs.

| Status | Meaning |
|---|---|
| `full_success_evidence` | A complete execution and verification witness is bound to this exact instance |
| `screening_passed` | All performed checks passed; this draw has no complete execution witness |
| `undetermined` | Evidence, applicability, runtime identity or computation budget is insufficient |
| `check_failed` | A checked necessary condition failed, with its reason retained |

The adapter uses [infra/oracle](../../infra/oracle/README.txt). Screening is not
proof of global solvability or formal task admission.

## Physical checks and gentle motion

The evaluator checks every 2.5 ms physics step; joint commands run at 50 Hz.
Double precision, elliptic friction and GJK collision detection are declared
parts of the configuration. Arm/hand proportional gains are 40% of the shared
backend defaults; hardware effort bounds remain enforced.

| Measurement | Limit |
|---|---:|
| Joint-target speed | 0.50 rad/s |
| Disk translation / rotation speed | 0.12 m/s / 0.65 rad/s |
| Sum of robot contact-force magnitudes on disk | 18 N |
| Sum of table contact-force magnitudes on disk | 8 N |
| Final translation / rotation speed | 0.015 m/s / 0.08 rad/s |
| Final tilt / goal-center tolerance | 8 degrees / 45 mm |
| Released stable dwell | 2 s |
| Episode budget | 600 s |

Ordered scoring requires edge support with 55–95 mm overhang, a real bimanual
face grasp, lift clearance, controlled bimanual inversion, then complete released
placement. A 0.10 s grasp loss during lift or inversion fails. The declared
`gentle_placement` phase allows support transfer after inversion while retaining
all global speed, force, drop, timeout and final-state checks.

Policy audits guard object and robot pose/state setters. The reference uses no
welds or attachments. Robot self-contact and robot/environment contact reports
are sampled at 50 Hz; they are not substep geometric collision certificates.
These development API audits do not constitute a hostile-code sandbox.

The [collision diagnostic](validation/collision_diagnostic.json) documents an
installed-engine analytic-cylinder rim anomaly. The single convex mesh avoids
that anomaly, with under 0.031 mm radial approximation error and matching polygon
inertia. The installed engine was not patched. Historical cylinder, pyramidal,
MPR and earlier handoff configurations retain their original recorded semantics.

## Checks and review

```bash
python -m unittest tests.test_tabletop_disk_flip tests.test_disk_flip_oracle
python -m humanoid.g1_tabletop_disk_flip.solution.summarize_attempts
python -m humanoid.g1_tabletop_disk_flip.solution.validate_release
```

The supplied review bundle already exists. To rebuild it, pass a new
`--output` directory to `validate_release`; evidence directories are not overwritten.

Validation passed: 56 disk task/oracle tests, 129 shared tabletop tests (including
the disk evaluator tests), 29 infrastructure oracle tests, and repository checks.
The ten development draws in [the sampling ledger](validation/oracle_batch_summary.json)
are all retained as `screening_passed`, with no new full trajectories generated.
The [four-status integration fixture](validation/screening_contract_report.json)
retains one example of each status in input order. It is a contract test, not an
external benchmark result.

The release validator requires the whole preselected cohort, matching physical
assets and sources, independent video replays and measured final conditions. It
creates a portable review page, observed skill cases, exact-instance witnesses,
coverage records and an **unsigned** human-review form. It cannot grant formal
admission or sign the human checks required by the
[acceptance standard](../../infra/acceptance-zh.html#humancheck).

The [no-op report](validation/no_op.json) confirms a stable two-second scene with
score zero. Synthetic scoring tests establish evaluator behavior, not physical
robot feasibility. This reference is an additional task outside the previously
published 12-task inventory.

<!-- disk-flip-family-index:start -->
## Disk Flip family · 2026-10-29

4 个 task variants、3 种 embodiment、6 个选定 settings，使用 3 类盘体（2 套主要几何）。6 个配置均有候选专家与物理执行；5 个完整成功见证，1 个仍待完成。

[中文设计](../../infra/planning/disk-flip-family/README.md) · [English design](../../infra/planning/disk-flip-family/README-en.md) · [JSON](../../infra/planning/disk-flip-family/task-design.json)

Original evidence and admission remain scoped to DF-01-G.
<!-- disk-flip-family-index:end -->
