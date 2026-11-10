# G1 table-tennis reference data card

Version: 0.1.0-rc1. Publication: owner-approved table-tennis-0.1.0; formal benchmark admission remains false.

## Collection and population

The frozen cohort contains four exact public configurations (`nominal`, `left`, `right`, `fast`), each repeated three times from a stationary normal reset. Results: 12/12 complete successes, 100/100 stage score for every reference, and 12/12 high/low/trajectory design witnesses. Deterministic repeats do not measure distributional robustness. The left/right feeds shift ball y from -0.22 m to -0.25/-0.19 m and target y to +0.12/-0.12 m. The fast feed changes x velocity from -3.2 to -3.3 m/s. All other frozen settings are in `task.py` and each run's `config.json`.

Four fresh torque replays reproduce all recorded root, joint, ball and racket states within the verifier's 1e-9 absolute tolerance. The three controls are retained: zero motor torques fail at 0 points, WBC hold without a strike plan fails at 25, and an invalid wide feed is screened out and counted as a prescribed zero. The seven prior development attempts retain their original scores and source snapshots.

## Physical model and observations

A 29-joint G1 has an unactuated free root and physical feet. The reference maintains stationary double support. The right-wrist racket has mass 0.12 kg and a 0.09 m radius. The ball is 2.7 g with 0.02 m radius. Table top height is 0.76 m; net height is 0.1525 m. Ball/table and ball/racket friction are zero, with no drag or Magnus model. The environment exposes privileged current simulator state. Planning happens before the simulation clock advances, with no latency compensation or real-time claim.

MuJoCo 3.14.0 runs CPU dynamics at 2 kHz. OSQP solves the whole-body controller at 500 Hz. Gamma GPU CUDA evaluates 28,033 outgoing candidates and EGL renders the evidence. The run summaries record host, Slurm ID, GPU identity, package versions, configuration identity and source/asset hashes. The physics checks bound restitution and timestep sensitivity in isolated ball contacts; they are not real-rubber calibration.

## Records and validation

Every executed episode stores all physics substeps in `trajectory.npz`, with 43 qpos values (floating robot, 29 joints, free ball), 41 qvel values and 29 motor torques. Additional arrays record target/derivatives, racket pose and velocity, contact categories, force, COM, support force and slip. Action boundaries and polynomial coefficients are in `segments.json`; plans, independent contact events and summaries are separate files. SHA-256 manifests cover each run. `verify.py` regrades physical observations and checks the three mappings; torque replay separately verifies dynamics. Resealed false score summaries are rejected by independent regrading.

Balance statistics for the four distinct references are in `acceptance/reference-v1/balance-metrics.json`. The 31 regression tests cover temporal ball rules, stage-credit semantics, missing evidence, falling after landing, slipping, lost support and the free-root/no-weld/no-root-actuator model contract.

## Limitations and use

This supports one stationary, state-based return and recovery. It does not establish stepping, large reach envelopes, unseen feed robustness, visual ball estimation, spin handling, continuous rallies, multi-robot collaboration, hardware safety or learned skill composition. A passive rigid wrist attachment avoids a separate grasp-learning task. There is no imported G1 table-tennis policy or pretrained balance network.

The source/assets/evidence archive is intended for reproducible task review. Owner publication approval is recorded in PUBLICATION.md. Independent-person reproduction and integration into an isolated untrusted-agent runtime remain pending. The benchmark's existing inventory and formal admission counts are unchanged. License details are in `THIRD_PARTY_NOTICES.md`.
