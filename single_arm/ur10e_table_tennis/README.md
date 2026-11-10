# UR10e table-tennis reference

[Owner-approved publication](PUBLICATION.md) · [Download release](https://github.com/wuxiyang1996/robo-si/releases/tag/table-tennis-0.1.0)

Version: **0.1.0-rc1**. A fixed-base, six-joint UR10e returns one incoming ball
through physical racket contact, lands it inside a target disk on the opposite
half, and returns to its ready posture. This release implements a hierarchical
state expert, independently computed stage scores, and continuous physical
trajectory evidence.

The declared release scope is **single arm, single return, gravity-only flight,
frictionless ball/table and ball/racket contacts, privileged simulator state**.
The contact model is numerically checked, not calibrated to a real ball. This is
not an A3/G1 controller, doubles system, visual policy, or real-time deployment.
It is an owner-approved published reference outside the historical 14-task inventory.

## Measured release evidence

The frozen campaign in `acceptance/reference-v1/` contains:

- Four exact configurations (`nominal`, `left`, `right`, `fast`), three independent
  resets per configuration: **12/12 full successes**, each stage score 100.
- All 12 runs pass high-level → low-level → measured-trajectory consistency checks.
- Four fresh-scene **torque replays** reproduce recorded states and outcomes.
  These are new physics executions, not state restoration or video playback.
- A stationary-arm control scores **25/100**, full success false. An invalid
  wide feed scores **0/100**, no executed trajectory; it remains in the ledger.
- Numerical impact checks at 1, 3.4 and 5 m/s, at 0.5 and 0.25 ms timesteps:
  no normal energy gain; maximum restitution change is about 0.0202.
- Changed-summary and resealed-false-summary counterexamples are rejected.

These deterministic repeats establish the four configurations only. They are
not twelve random seeds or a success-rate estimate over unseen distributions.
All prescribed reference/control attempts and the earlier development failure
are retained. See `acceptance/reference-v1/campaign.json`, `attempts.json`,
`replays.json` and `development/README.md`.

Gamma execution used an NVIDIA RTX A4000 on `gammagpu05`, Slurm job 8023930.
**PyTorch CUDA scores 28,033 outgoing-shot candidates; MuJoCo runs articulated
and contact dynamics on CPU; EGL renders videos on GPU.** GPU physics or RL
training is not claimed. Planning occurs before the simulation clock advances;
the expert is not a measured real-time controller.

## Install and run

Use Python 3.12 and the pinned packages in `requirements.txt`. Robot meshes and
the unmodified upstream model are included; no Google Drive USD download is
required. Installing Python dependencies requires a package index or a local
wheel cache. The source/evidence archive is not an offline wheel distribution.

```bash
python -m pip install -r single_arm/ur10e_table_tennis/requirements.txt
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
python -m single_arm.ur10e_table_tennis.run --case nominal --device cuda \
  --video --output /tmp/tt-example
python -m single_arm.ur10e_table_tennis.verify /tmp/tt-example
python -m single_arm.ur10e_table_tennis.run --device cuda \
  --replay /tmp/tt-example --output /tmp/tt-replay
```

Output directories must not already exist. CUDA requests fail explicitly if no
CUDA device is available. For CPU-only development, use `--device cpu` and omit
`--video`; GPU and CPU results remain separately identified in run manifests.
The CLI returns nonzero on infrastructure/planning errors, but a fully executed
unsuccessful episode is a valid recorded result; inspect `summary.json`.

To run on Gamma from the repository root:

```bash
sbatch --export=ALL,TT_OUTPUT=/absolute/new/evidence-directory \
  single_arm/ur10e_table_tennis/scripts/run_gamma.sh
```

The script requests account/partition `gamma`, one GPU, four CPU cores, and
16 GiB memory. Override `TT_PYTHON` with a compatible Python interpreter.
Resources and elapsed limits are explicit in the script.

## Expert and trajectory refinement

`expert.py` consumes current ball and joint state. A one-bounce ballistic model
predicts the contact window. The GPU search chooses a legal outgoing flight,
target, racket normal and normal velocity. Separate scratch-state IK resolves
contact/preparation/follow-through poses. Piecewise quintic joint curves satisfy
the contact velocity and are screened against joint limits and sampled robot
collisions. Inverse-dynamics feedforward plus bounded PD torques tracks them.

| High-level goal | Ordered low-level actions | Physical evidence |
|---|---|---|
| Prepare interception | approach | Measured joint entry/exit states and bounded trajectory |
| Return to target | strike, follow_through | Actual racket contact, outgoing net crossing, first landing |
| Recover ready | recover, hold | Final joint position/speed and continuous hold duration |

`expert_contract.json` records entry/exit predicates and failure exits. Every
segment has a plan/subgoal ID, half-open command range, measured entry/exit state,
and its generating polynomial. The auditor checks full contiguous command
coverage, regenerated command targets, physical constraints and independent
task outcomes. Sampled preflight collision checking is not a continuous collision
certificate; actual execution is monitored at every 0.5 ms physics step.

No ball pose, velocity, joint state, weld, or external-force writes occur after
reset. All execution enters through six bounded joint motor torques. Initial IK
and planning use scratch data; they never advance or overwrite the live world.
The task has no checkpoint stitching or task-object teleportation.

## Scoring

This task follows the repository's **stage-scoring/1** contract. The formal
normalized `score` equals `stage_score / 100`; full `success` is separate.

| Stage | Points | Mode | Trusted predicate |
|---|---:|---|---|
| legal_racket_contact | 25 | once | One own-half bounce, then a valid racket impact |
| net_clearance | 25 | once | Valid struck ball crosses the net plane above the net and inside its lateral bounds |
| opponent_table_landing | 20 | once | The first post-strike landing is on the opponent half |
| target_landing | 15 | once | That landing lies within the visible 0.30 m target disk |
| recovered_ready | 15 | live | After a valid target return, final joints within 0.035 rad of ready and speeds below 0.08 rad/s for 0.12 s |

The recovery credit can be fractional over the hold interval and resets when
its physical conditions are lost. A passive incoming bounce earns no points.
Repeated milestones cannot add points. A double hit, net/illegal-body contact,
arm collision, excessive joint speed/position or ball impact force prevents
full success. Already valid milestone credit is retained for physical failure;
integrity failure/truncation produces VOID and clears every awarded stage.
Tracking error is a reference-quality diagnostic, not an agent score criterion.

Planned-but-unexecuted candidates have unknown physical feasibility and no
execution success evidence. A prescribed campaign episode that never executes
contributes zero to aggregate scores. The wide-feed control demonstrates this.
`success_score` is a separate binary diagnostic, not the primary score.

## Reproduce the campaign and checks

```bash
python -m unittest discover -s tests -p test_table_tennis.py -v
python -m single_arm.ur10e_table_tennis.physics_checks
python -m single_arm.ur10e_table_tennis.campaign \
  --device cuda --output /tmp/tt-full-campaign
python -m single_arm.ur10e_table_tennis.package \
  --evidence /tmp/tt-full-campaign --output /tmp/ur10e-table-tennis.zip
```

The campaign freezes its prescribed cases before execution, retains failures,
regrades every recording, performs four torque replays, and exercises artifact
tampering counterexamples. `campaign.json` contains the actual readiness verdict.
Packaging verifies every run, archives the source, meshes, docs, evidence and
videos, and writes SHA-256 checksums. It does not publish anything.

## Data and release boundaries

See [DATA_CARD.md](DATA_CARD.md), [task.toml](task.toml),
[admission.json](admission.json), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md),
and the [English task page](../../infra/task-table-tennis-en.html).

The owner has approved publication after the recorded engineering gates passed.
Independent-person reproduction, isolated untrusted-agent integration, camera
perception, spin, continuous rallies and humanoid doubles remain outside this
physical validation scope. Do not label it a formally admitted task
or use public reference cases as a confidential held-out evaluation set.

## Extension task and metric design

[Interception, relocation and rally metrics](../../infra/planning/table-tennis/extensions/README.md) cover G1 stepping, fixed-arm wide interception, powered-rail movement and continuous rallies. This is a proposed evaluation design; current reference results do not validate these extensions.
