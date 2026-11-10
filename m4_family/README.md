# M4 family development references

Six embodiments share ground-supported towing through an L corridor. This package contains privileged expert candidates, not admitted benchmark agents. Cargo stays on the platform; lifted hand-supported carrying remains M2.

## Run and inspect

Use the existing Genesis 1.4.3 / Torch 2.11 environment. Each attempt requires a new output directory. Rendering uses EGL; simulation uses CPU. Do not run physics on the login node.

```bash
python -m m4_family.launch --tasks M4-02 --attempt new-attempt --seconds 120 --mass 5 --ctl '{"v_pull":0.25,"delta":0.20}'
# On an allocated compute node, without Slurm submission:
python -m m4_family.run --task M4-02 --out /absolute/new/run --seconds 120 --mass 5 --video --ctl '{"v_pull":0.25,"delta":0.20}'
python -m m4_family.verify /absolute/new/run
python -m unittest m4_family.test_family -v
python -m m4_family.report
python -m m4_family.sync_docs
# Fresh physics execution of the exact reference scene, with declared XY jitter:
python -m m4_family.recheck m4_family/runs/M4-04-load15-a04 --attempt repeat-new --seed 7 --jitter .02
```

`launch.py` freezes the family Python source before submission. It declares the repository path through `M4_REPO_ROOT`; policy weights and shared dependencies are recorded in each source manifest. Original M4 source, thresholds and historical evidence are retained. Restored visual assets come from the locally archived M4 reference release; see `asset-restoration.json`.

`recheck` copies the exact recorded scene parameters into a new run through `--task-file`; it does not regenerate wall geometry from a width label. It reuses accepted controller arguments and recorded G1 command settings, then executes the current frozen family source. A nonzero `--jitter` independently perturbs each initial robot X/Y coordinate within the declared range and rebuilds the preconnected ropes before monitoring begins. The RNG seed identifies this initial-pose perturbation, not broad simulator randomization. The parent scene hash, perturbation and all new outcomes are retained. Failures count in the [re-execution ledger](https://github.com/wuxiyang1996/robo-si-review-assets/releases/download/m4-autonomous-20261029/m4-569686a3bcce13e27921bb69-validation-campaign.json).

G1 development parameters `max_forward`, `height` and `pitch` are policy inputs, not external forces or changed motor limits. The decoupled policy's seven command entries are velocity, height and RPY, following the [pinned upstream implementation](https://github.com/NVlabs/GR00T-WholeBodyControl/blob/45c03facbf848e0c743091b7d9c17952096ff908/decoupled_wbc/sim2mujoco/scripts/run_mujoco_gear_wbc.py). Forward pitch is ramped over a 0.5 s response and returns toward zero when towing stops. Each scene stores its exact command parameters; default settings preserve earlier references.

The optional `ankle_pitch_bias` is an expert adaptation applied to both ankle-pitch joint targets, with the same smooth activation/decay. It is capped at 0.25 rad, then passes through the unchanged joint-limit projection and actuator torque limits. Raw and applied joint targets are both recorded. It changes the candidate controller, not the physical acceptance thresholds.

## Artifacts for every physical attempt

| Artifact | Meaning |
| --- | --- |
| `task.json`, `controller.json`, `robot-limits.json` | Exact candidate scene, controller settings and read-back motor limits |
| `high-plan.json` | Goals, low-level skills and required guards |
| `low-plan.json`, `geometry-screen.json` | Controller reference route and separate sampled platform-clearance screen |
| `trajectory.json`, `states.npz` | 50 Hz interpreted trace and 200 Hz joint/body states, commands and torques |
| `plan-trajectory.json` | High-stage intervals bound to trace sample indices and times |
| `monitor.json`, `evaluation.json`, `verification.json` | Physical monitors, task evaluator and independent offline rejudgment |
| `motion.mp4`, `first-frame.png` | Rendered actual simulation, with candidate/phase/failure annotations |
| `result.json`, `status.json`, `exception.txt` | Outcome, running progress and errors, including failed attempts |
| `source-manifest.json`, `code/` | Source/weight hashes and code copies; no unverified source revision silently substitutes |

A platform waypoint clearance screen does not prove robot/rope clearance or dynamic feasibility. Stage names locate measured execution; they do not prove independent skill applicability. `reference_success` requires measured delivery, dwell, all checks and unchanged source. Formal admission, independent human reproduction, ordinary-agent performance, grasping and autonomous connection remain separate.

## Monitoring changes and retained failures

The legacy baseline run is retained under `M4-01-a03/a04`; both reached the goal but exceeded 50 mm stance slip. These outcomes are not replaced by later slower-control successes.

The first family instrumentation version also counted pre-projection network outputs as applied joint targets, and tested a 0.5 s contact-force average at the first 5 ms sample. Version 2 makes the joint-limit projection explicit, stores both raw and applied targets, and assesses the first full force window at 0.5 s; cargo support geometry and absence of robot load support are checked from the first step. Early traces/results remain unchanged. Later candidates are rerun; no old failure is relabeled as success.

Limits remain 50 mm stance displacement, 400 N rope rating, 10 mm weld drift, 20 mm dynamic-body penetration, 10 mm rope penetration and the task's original stability/collision/final dwell rules. G1 foot monitoring uses each ankle-roll link's sole-center point `[0.035, 0, -0.03]`, with ground-specific contact load, rather than a Go2 calf offset. G1 pelvis minimum height is 0.48 m; Go2 trunk minimum is 0.14 m. Hand grasp is not implemented: G1 uses a declared fixed pelvis harness.

The first four-Go2 attempt exceeded Genesis's default eight dynamic weld slots. The family scene allocates at least two slots per rope plus one for the platform rim before scene construction. It does not remove constraints or bypass collisions.

Earlier four-Go2 attempts tested a declared 3.6 m corridor and an optional ordered-lane controller. The latter keeps attachment order while aligning each trunk with its own tensile direction. Later 2.6 m candidates use a compact initial formation, earlier turn lookahead and more wall clearance; their own measured executions establish the narrower scope. Wider trials do not substitute for those records. Failed narrower, faster and shared-heading attempts remain in the manifest.

The campaign reports both full configuration history and a post-debug acceptance suite: the selected nominal run plus the latest seed 1 and seed 2 re-executions of that same scene/controller. Grouping reverses only the declared initial XY perturbation and retains load, geometry, tools, locomotion settings and controller parameters. Earlier instrumentation failures, unsuccessful control versions and timeouts remain visible. The acceptance suite is a finite development check, not a held-out success-rate estimate or formal admission.

Current per-task outcomes and exact selected attempt IDs are in [`manifest.json`](https://github.com/wuxiyang1996/robo-si-review-assets/releases/download/m4-autonomous-20261029/m4-66441a7573e1772cf4f6ac02-manifest.json), with videos and evidence packages on the [task page](../infra/task-m4-zh.html#m4-execution). `report` and `sync_docs` update local files; they do not deploy a hosted website.

All monitoring samples are at the 200 Hz outer physics step, not inside Genesis's two internal substeps. The 50 Hz trace aggregates all check failures in each four-step window. Contact-force and foot-point conventions remain simulation approximations, not hardware calibration. The independent offline verifier rechecks dense clocks, actuator targets/efforts, robot stability and the delivery evaluator; contact checks rely on retained runtime monitor evidence.

## Frozen reference release

The six-embodiment preconnected release is documented in [0.1.0-rc1](../doc/m4-family-release-0.1.0-rc1.md). Use the portable `m4_family.release_run` entry from the downloadable runtime; it includes exact task/controller configurations and a source manifest. Final M4-06 control parameters supersede the earlier development selection. All earlier failures remain in the release ledger.
