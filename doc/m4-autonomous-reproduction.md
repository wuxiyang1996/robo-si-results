# M4 autonomous extension

This is a development candidate, with `admitted=false`. The six preconnected M4 references remain separate. Cargo is supported by the platform/ground; M2 hand-supported lifted carrying is outside this task family.

The verified positive scope is physical pin/eye connection, guide extraction, loaded retention, unloading, unlocking and separation. The frozen v3e extraction controller has three same-seed successful cycles. Single-Go2 tool trials use independent resets: the standard tool completes a measured pull and release, the small aperture is rejected, and the long-tool physical failure is excluded by the selector. These independent-reset trials are not continuous discovery or whole-transport witnesses. New continuous-scene attempts use `--continuous-discovery`; only a separately rejudged `continuous_discovery_success=true` counts as a choice/use component witness. a46 is the first such witness: 82.635 s, one continuous scene, rejected small aperture, release/navigation, standard-tool capture, 4.10 cm probe, selected use and final release. It still does not combine tool discovery with complete corridor delivery.

## Evidence and verdicts

- `ledger.json` identifies every attempt, frozen source, scene friction, precision, integration substeps and Slurm job.
- `runs/<attempt>/` retains high/low plans, phase-to-trajectory correspondence, overview/close-up videos, 50 Hz review trajectories, 200 Hz states and contact records, and world/source hashes.
- `verification.json` is the frozen verifier result. `verification-current.json`, when present, is a separate rejudgment; it never replaces original evidence.
- Verifier `passed` means evidence is coherent. Task/component success is `cycle_success`; physical validity is `physical_checks_passed`; full delivery additionally requires `full_transport_success`. `continuous_discovery_success` additionally checks physical rejection, released dwell, same-scene navigation and subsequent selected-tool use. A coherently recorded failed run can have `passed=true` and both success fields false.
- `design/current-rejudgment.json`, `admission.json` and the public progress page retain failures and incomplete gates. The v3i hardware candidate receives no v3e success credit.

## Local checks

From the repository root with the project Python environment:

```bash
python -m unittest m4_family.test_family m4_family.autonomous.test_contract m4_family.autonomous.test_agent_process m4_family.autonomous.test_agent_evidence
python -m infra.sandbox.records m4_family/autonomous/admission.json
python -m m4_family.autonomous.probe_report \
  m4_family/autonomous/runs/tool-small-bounded-a31 \
  m4_family/autonomous/runs/tool-standard-bounded-a32 \
  m4_family/autonomous/runs/tool-long-bounded-a33 \
  --out /tmp/m4-tool-comparison.json
```

Physical runs use Genesis 1.4.3, the repository Go2 policy/assets, EGL rendering and Slurm. `launch.py` freezes Python sources before submission, records initial-only precision/friction/substep changes, allows one physical job at a time and enforces the declared campaign budget. The exact submitted command and environment are retained in `snapshots/<attempt>/job.sbatch`; every rerun requires a fresh output directory. Do not submit an archived job script unchanged: its output path points at retained evidence. Use a new `launch.py --name` with the frozen `--replay-source`, reviewed campaign declaration and fresh output path. Never edit a frozen snapshot, reuse an output directory or transfer success between hardware revisions.

## Limits and release status

The candidate retains 50 mm stance slip, 400 N rope rating, 150 N connector service load, 20 N pin motor force, 40 mm travel, 40 mm/s pin speed, 0.8 W power and 0.8 J stroke work limits. Pin opening requires ten complete low-load control intervals. No runtime attachment changes, pose resets or external payload forces are allowed.

The namespace-isolated capability component does not establish isolation of the full planner/simulator interface. Formal admission also needs representative full transport, repeated continuous discovery, sealed grading, exploit controls, signed human video/stage review and second-person reproduction. `design/human-review-packet.json` leaves signatures empty until those reviews actually occur.

The public website is a development-evidence publication. Original raw records and frozen code are retained in the private dataset identified by `design/raw-archive*-receipt.json`; these archives are not formal benchmark releases.

Run `python -m m4_family.autonomous.release_gate --out /tmp/m4-readiness.json` to check formal-release readiness. Exit code 2 means blocked; the admission schema validator returning 0 alone does not authorize a formal release.

The v3j layout corrects an unused centre-rope snag and replaces floor guide supports with a colliding overhead frame. All declared candidates remain present in tool scenes. a43 reaches the goal but fails during unloading at 137.305 s; it is not a full success. `design/goal-handoff-review.json` declares the subsequent unloading correction without changing final dwell or physical limits.

From a43 onward, `runtime-provenance-initial.json` records runtime versions and Genesis Python-source hashes; successful runs must match the final snapshot. This does not pin native binaries or a complete container image.

The installed Genesis contact rule uses the larger of the two geom friction coefficients. The recorded Go2 feet have coefficient 1.0, so both floor 0.3 and floor 0.8 yield effective foot-ground friction 1.0. Those earlier floor variations affect other contact pairs and do not establish lower foot traction. See `design/friction-combination-audit.json`. a45 failed at 83.455 s during the turn before the revised unload branch; a43 reaching the goal is not robust delivery evidence.

a47 is the first independently rejudged full two-Go2 autonomous corridor witness: 153.20 s, maximum stance slide 46.66 mm, rope tension 104.60 N, released goal dwell 2.005 s. The rope-heading controller keeps the receiver aligned with towing. Frozen repeats are declared in `design/corridor-repeat-plan.json`. This episode does not also perform continuous tool discovery; a46 remains a separate component witness.

`draw()` retains legacy reference IDs for exact physical reproduction. `draw_for_grading()` uses fresh private-key HMAC handles; only `public_catalog` may cross an agent boundary. The trusted key, roles and seed stay private. The factory closes a demonstrated bounded seed-enumeration route, but is not yet integrated into a complete sealed grading runner. See `design/identifier-shortcut-audit.json`.

The predeclared a47–a49 full-corridor cohort passed 3/3: 153.20, 153.20, 152.29 s (0.91 s range). This is same-start controller repeatability only. See `design/corridor-repeat-cohort.json`; the retained failures are not replaced by this cohort.

The formal release check additionally requires `integrated_discovery_delivery_witnesses`: discovery and full delivery must both be independently verified in the same recorded episode. Separate successful components cannot satisfy that condition. Contract tests cover this failure mode.

The continuous tool component frozen cohort a46/a50/a51 passed 3/3, each at 82.635 s. It remains separate from the three corridor references. Twelve overview/close-up video files across these six runs passed decode/frame-clock checks; identical encoded files reuse the corresponding SHA-256 decode evidence. Original attempts 50–51 and their frozen source are archived with 302 per-file hashes in `design/raw-archive-tool-repeat-receipt.json`. These checks are not signed human review.

The first integrated candidate was predeclared in `design/integrated-delivery-plan.json`: one Go2 keeps the selected tool attached after the measured three-second use and continues onto the original platform route. a52 passed the integrated sequence and full dense physics/goal/release checks at 171.175 s; the original incorrect insertion-clearance verdict remains beside the corrected rejudgment. The loaded-retention audit checks shaft/ring linking without changing physical limits. Maximum stance slide was 49.52 mm, near 50 mm; two same-source repetitions are declared in `design/integrated-repeat-plan.json`. Unselected tools remain physical objects throughout. No success is inferred from the dry run or earlier separate references.

`agent_process.py` provides a persistent sealed-program namespace boundary with a fresh scratch workspace, read-only delivery, bounded velocity/pin actions, input/output timeouts and a hash-chained exchange log. `agent_evidence.py` binds these requests to executed velocity/pin records. The current physical integration is deliberately restricted to an eight-second no-op calibration (`--mode standstill --agent-delivery ...`); it uses a declared proprioception-only observation subset. This is not the final public sensor suite, a positive isolated expert, or full sealed grading. The trusted executor supplies the existing Go2 gait and local pin interlock; the external program supplies every requested body velocity and pin action.

The program boundary uses a read-only sandbox root and device directory, a nonroot capability-free agent, a 32-process rlimit, per-process CPU/address-space limits and a per-file write limit. A private mount namespace now provides a shared 16 MiB/256-inode scratch filesystem for `/tmp` and `/workspace`; exhaustion and remount escape tests pass. These local controls postdate a53. Aggregate process-tree CPU/memory accounting and a complete native image lock remain unvalidated. See `design/agent-resource-audit.json`.

The sealed a53 calibration completed 1,600 physical steps / 400 bound program exchanges, with clean physics, zero task success and no agent void. Its overview and coupler videos decode and match the clock. This eight-second observation subset remains separate from full-duration sealed grading. Original a52–a53 evidence and frozen source are archived with 326 per-file hash checks in `design/raw-archive-integrated-receipt.json`.

The shared CPU pipeline is `python -m infra.sandbox.pipeline m4_family/autonomous --tier cpu`. Its JSON receipt under `acceptance/pipeline/` records exact source digests. The `sandbox/` directory holds only pipeline configuration; the existing `sandbox.py` remains the isolated capability component. CPU pipeline success is not a GPU/container grading pass.

The predeclared integrated cohort a52/a54/a55 completed with 3/3 independently rejudged successes. Completion times: 171.175 s, 170.600 s, 170.600 s. Maximum stance slides: 49.521 mm, 48.563 mm, 48.563 mm. See `design/integrated-repeat-cohort.json`. This is same-start, same-catalog repeatability, with original frozen insertion-clearance verdicts retained; it is not a held-out success rate or a formal admission decision.

The four new episodes a52–a55 have eight overview/coupler files with successful decode and frame-clock checks. a54–a55 raw records and frozen source are archived with 312 file hashes in `design/raw-archive-integrated-repeat-receipt.json`; earlier a52–a53 use a separate 326-file archive. Complete-assembly signed force diagnostics are retained for all three integrated successes.
