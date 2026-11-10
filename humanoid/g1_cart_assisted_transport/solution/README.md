# H2 expert-reference attempts

**Status 2026-10-21: redesigned scene (rails dock, `FEASIBILITY_CONDITIONS.md`
"Redesign: difficulty off the push") passes with `floor_push/run_grasp_push.py`
(`floor_push/runs/rails-v10` 77.8 s; then `rails-v14` 94.6 s, `rails-v15` 75.4 s, `rails-v16` 70.1 s, `rails-v18` 70.0 s, `rails-v19` 82.2 s, 5 passes in the last 6 runs; audits passed; repeats in
`expert_progress.json`, `rails_dock_redesign`). In the previous wedge scene
(`CART_DOCK=wedge`) the same expert passed in `cart-v109` 75.7 s, `cart-v112`
69.5 s and `cart-v114` 84.5 s.** The paragraph below describes the wedge scene.
The G1 pushes two slotted handles on the crate's pushed faces with its fists
(the end posts lock the hands sideways; a hook that could pull is unusable
because the lower-body policy freezes under arm tension), loads the crate onto
the floor-level tray dolly over a fixed wedge (13.6 s) and delivers it ON the
dolly through both offset passages. The scorer requires the cargo supported
on the cart at delivery (`task_spec`: `supported = on_cart`). Conditions:
0.70 x 0.70 x 0.90 m, 10 kg crate (friction 0.12, `box_handles` True) starting
on the floor at (2.00, -0.80); tray dolly (asset v10, `wheel_frictionloss`
0.01) parked on the first passage lane at (3.81, -0.80); fixed wedge, funnel
lips and guide curb; ground friction 0.03; passage 1.5 m; 180 s. The earlier
open-hand pass (`cart-v54`, `run_cart_push.py`, now the base class) did not
repeat (0 of 22). See `floor_push/README.md` and `FEASIBILITY_CONDITIONS.md`
("Cart-required revision" through "Grasp instead of push"). The earlier floor-only pass (`trial-v23`, 95 s, 25 kg, cart unused)
is historical, as is everything below this paragraph about the original
cart route under the original conditions.

These are physical candidate rollouts, **not successful expert demonstrations**.
Asset revision 2 adds the user-requested physical U handle (1 kg) to the cart.
Payload, actuator limits, joint-action interface and termination rules are unchanged.
No loading, passage negotiation or delivery has been certified.

Current progress is recorded in [expert_progress.json](expert_progress.json).
The revised handle has passed URDF/USD structural checks and a Genesis contact
fixture: [report](runs/handle-asset-smoke-v2/report.json) and
[close-up](runs/handle-asset-smoke-v2/handle_closeup.png). That fixture is an asset
test, not a robot grasp. `runs/cart-handle-approach-v6` now completes the actual
original-reset approach and unloaded handle pregrip in 76.857 s, including two
seconds of observed stability. Its fresh actual-source path passed 194 poses,
772 dense geometry/static samples and 70 native-drive checks. See the
[physical pregrip audit](runs/cart-handle-approach-v6/pregrip_execution_audit.json).
Sustained grasp, revised-cart docking and transport remain unvalidated.

`runs/cart-handle-approach-v7` reached real finger/handle contact, but proximal
finger contact on the top of the bar produced opposing friction. The cart moved
only 0.132 mm; the run did not complete release or traction. A new offline
approach raises the wrists by 1 mm and reserves 0.8 mm clearance for non-hook
links. The faster timing trial `cart-handle-approach-v8` stopped before contact
because its finger reference exceeded the controller's tracking speed. These
results are failures to improve from, not successful cart maneuvers.

`runs/cart-handle-approach-v9` physically pulled the revised cart 11.116 mm,
released the handle and held a measured quiet, separated state for two seconds.
Its [physical audit](runs/cart-handle-approach-v9/traction_execution_audit.json)
passed the original action, actuator and task checks. Continuous bilateral
contact lasted only 0.10 s, below the required 0.20 s, so this is not a passed
short-traction primitive. A new observer records object contact vectors at all
four original 5 ms physics steps to improve the force governor.

`runs/ground-loading-v5-direct-finish` completes original-reset unloaded ground
hand entry at 25.939 s. Its [independent physical audit](runs/ground-loading-v5-direct-finish/physical_ground_entry_audit.json)
reconstructs 2.42 s of consecutive stable samples, positive measured hand/box
clearance and zero object contact. This is a loading preparation pose; the box
has not been loaded. The reference sweep requires 0.3 mm clearance; actual
terminal gaps are separately measured at 0.236 and 0.317 mm.

`runs/ground-loading-v6-short-push` independently repeated stable unloaded entry,
then rejected two native-drive QPs before issuing any push action. Its
[physical audit](runs/ground-loading-v6-short-push/physical_ground_short_audit.json)
records zero loading controls and zero box advance. Independent optimization of
those exact QPs found solutions to the unchanged objective and constraints;
a failure-only numerical fallback then passed all 57 native checks.

`runs/ground-loading-v7-certified-qp` physically advanced the original box
3.979 mm, released contact and held a measured quiet state for 2.02 s. The
[independent audit](runs/ground-loading-v7-certified-qp/physical_ground_short_audit.json)
passed the original action, actuator, task and source-integrity checks. The
controller released early to preserve its foot-drift reserve, so the 10 mm
short-push criterion and complete loading remain unmet.

The current experiments use the following commands from the repository root.
Each output directory must be new. Both start from the original reset, record
all 43 actions and retain the original 120 s clock. They test individual
primitives; neither command implements complete delivery.

```powershell
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
& D:\rsi_vla\genesis_env\Scripts\python.exe humanoid/g1_cart_assisted_transport/solution/new_strategy/cart_handle_approach.py --out humanoid/g1_cart_assisted_transport/solution/runs/handle-window-trial --seconds 120 --approach-x 3.48 --pregrip --traction --mixed-pregrip --window-traction --agile-finger-pregrasp --snapshots
& D:\rsi_vla\genesis_env\Scripts\python.exe humanoid/g1_cart_assisted_transport/solution/new_strategy/run_ground_loading.py --out humanoid/g1_cart_assisted_transport/solution/runs/ground-window-trial --hand-cartesian --measured-foot-finish --short-push --window-short-push --snapshots
```

The historical runs below used the previous cart without the physical handle.
In particular, `runs/cart-dock-v23-momentum-forecast` completed empty-cart
docking in 79.28 s, and `runs/pallet-ascent-v60-fast-reserve-release` advanced
the box 25.02 mm before an unsettled release. Neither validates the revised
handle cart or a complete loading sequence.

A historical complete short cargo primitive is `runs/wbc-cargo-v6`: from the original
reset, push the original 25 kg cargo forward 8.59 mm, withdraw both hands,
re-center COM, and stand with a verified two-second settled endpoint. It took
61.32 simulated seconds, with neither original task failure nor task success.
This is a single physical primitive, not a complete expert transport solution.

`run_candidate.py` combines the existing H1 Agile lower-body policy with the H5
arm Jacobian IK. Only `env.step()` joint targets affect the simulation. MuJoCo is
used for arm forward kinematics/Jacobians, not to replace the Genesis rollout.
The runner stops on original task termination, unreachable arm targets, or a
bounded probe duration. It does not implement the later loading/transport stages.

## Initial experiments

- `runs/cargo-v1`: original 25 kg cargo, 569 control steps / 11.38 seconds.
  The original task reported failure. Peak sampled non-foot impact was 1175.82 N
  (limit 800 N). Cargo horizontal displacement was only 0.33 mm; this is not
  useful pushing or loading. The crouch phase stayed at 0.720–0.723 m root height
  despite the 0.55 m command. The peak arm IK residual was 0.209 m.
- `runs/cart-v1`: 1465 control steps / 29.30 seconds; reached the rear approach
  position, then stopped with `arm_reach_unreachable`. Peak IK residual was
  0.421 m. No robot-cart contact or horizontal cart displacement was measured.
  Minimum root height was 0.713 m; neither task success nor task failure fired.
  Both saved rollouts passed the record-integrity audit.

Each run contains an actual rendered `motion.mp4` when `--video` is used,
`trace.json` (states, commands, contact-force magnitudes and task flags),
`rollout.npz` (pre-action observations, actions, final observation and joint order),
and `result.json` with source hashes. `controller.py.txt` snapshots the runner.
Contact magnitudes include any robot link, not just the hands. Reported forces
are sampled after a control step; the task checks every physics substep.

`audit.py` checks record consistency, shapes, finiteness, action bounds and time
alignment. Passing this audit **does not mean task success or independent replay**.
The task's nine existing regression tests pass.

## Reproduce from the repository root

Use a new output directory each time:

```powershell
& ../genesis_env/Scripts/python.exe humanoid/g1_cart_assisted_transport/solution/run_candidate.py --mode cart --seconds 45 --video --out humanoid/g1_cart_assisted_transport/solution/runs/cart-new
& ../genesis_env/Scripts/python.exe humanoid/g1_cart_assisted_transport/solution/run_candidate.py --mode cargo --seconds 30 --video --out humanoid/g1_cart_assisted_transport/solution/runs/cargo-new
& ../genesis_env/Scripts/python.exe humanoid/g1_cart_assisted_transport/solution/audit.py humanoid/g1_cart_assisted_transport/solution/runs/cart-new
```

## Remaining work

Validate repeated controlled cart strokes, docking and transfer from the 0.23 m
pallet. Only after loading is physical should the controller tackle both offset
passages and the final 2 second dwell. Direct-lift infeasibility also remains
unproven. These candidates do not prove that the task itself is impossible.
Isaac execution and multiple-seed validation remain open.

## Whole-body continuation

`whole_body_plan.py` retargets the measured stance with fixed feet and a supported
centre of mass. `run_whole_body.py` uses contact inverse dynamics for the legs,
converts torques to the original motor's joint-position targets, and executes
only `env.step()`. It retains the default initial state and the original
environment `advance`, limits, physics and task scoring.

`runs/wbc-cart-v2` completed 44.42 s without task failure. Actual root height
reached 0.4945 m, the cart moved 0.0922 m along x, maximum sampled robot/cart
contact was 65.0 N and non-foot impact was 33.0 N. Foot drift stayed below
0.744 mm. This is a physical crouch/contact/push milestone, **not delivery**.
The saved `execution_audit.json` details the measured support and actuator checks.

The original v2 geometric clearance certificate is invalid: relocating a static
MuJoCo deck proxy left stale collision acceleration data, hiding finger/deck
penetration in the requested reference. The physical scene still enforced all
collisions; measured hand tracking error grew to 0.1105 m on contact. The current
planner disables that problematic optimization, checks interpolated poses, and
uses wider hand spacing with thumb clearance before intentional contact.

Replaying v2's recorded actions open loop failed during walking at 4.96 s,
before the WBC phase. See `replay.json`. Do not distribute this as a reliably
playable motion sequence; measured observations and feedback are necessary.
The cause of replay divergence has not been established.

`runs/wbc-cart-v3` completed the corrected feedback cycle in 79.90 s without
task failure: approach, crouch, an 8 cm hand stroke, release, and return to a
0.722 m root height. The cart stayed still until the push phase; hand/wrist
contact peaked at 4.41 N. Cart travel was 9.01 cm by the end of that phase and
13.15 cm after passive coasting. Maximum measured hand tracking error was
1.19 cm. This demonstrates hand-induced cart movement and posture recovery;
it does not demonstrate accurate cart position control, docking or loading.
See `execution_audit.json`, `phase_contact_audit.json`, and `coast_fit.json`.

Front-side trials revealed a learned near-zero-speed turning region. Maintaining
small planar steps while correcting heading resolved that navigation issue.
The resulting staggered foot stance needs a higher palm target (0.31 m instead
of 0.21 m) to avoid a discontinuous IK branch; this was screened using measured
state before attempting physical execution.

```powershell
& ../genesis_env/Scripts/python.exe humanoid/g1_cart_assisted_transport/solution/run_whole_body.py --video --push-distance .08 --recover --out humanoid/g1_cart_assisted_transport/solution/runs/wbc-new
& ../genesis_env/Scripts/python.exe humanoid/g1_cart_assisted_transport/solution/run_whole_body.py --side front --reach-height .31 --duration 12 --stroke-duration 1 --push-distance .12 --recover --seconds 115 --video --out humanoid/g1_cart_assisted_transport/solution/runs/front-new
& ../genesis_env/Scripts/python.exe humanoid/g1_cart_assisted_transport/solution/replay.py humanoid/g1_cart_assisted_transport/solution/runs/wbc-new --out humanoid/g1_cart_assisted_transport/solution/runs/wbc-new/replay.json
```

`geometry_notes.json` records a provisional north-side docking layout and its
clearances. It is a geometric candidate and has not been physically executed.

## Front push and measured reaction feedback

`runs/wbc-cart-front-fast-v3` completed approach, a 12 cm / 1 s hand reference,
release, and standing recovery in 73.04 simulated seconds. The empty cart moved
44.50 cm west; neither original task failure nor task success occurred. Measured
hand/wrist contact lasted approximately 0.24 s and peaked at 138.68 N. Only
1.95 cm of cart travel had occurred by the last contact sample; another 42.54 cm
came from coasting. This is not a controlled docking result.

The independent saved-state audit found foot drift below 1.63 mm and one frame
of right-ankle position-target clipping (0.1063 rad, reducing the requested
negative torque by 2.13 Nm). Original motor and joint limits remained enforced.
See `execution_audit.json` and the two `execution-audit-*.png` frames in the run.

```powershell
& ../genesis_env/Scripts/python.exe humanoid/g1_cart_assisted_transport/solution/run_whole_body.py --side front --reach-height .31 --duration 12 --stroke-duration 1 --push-distance .12 --contact-force-limit 300 --recover --seconds 115 --video --out humanoid/g1_cart_assisted_transport/solution/runs/front-new
```

`contact_feedback.py` maps measured object forces on robot links to generalized
forces with point Jacobians. `--measured-contact-wrench` passes these observations
to leg inverse dynamics; it does not apply a force to the simulator. Logged
`contact_feedback_pre_step` uses the state before the recorded action, while
the ordinary contact magnitudes use the state after that action.

`runs/wbc-cart-front-feedback-v1` completed the same stage sequence in 73.58 s
without task failure, with measured reaction feedback enabled. Cart travel was
15.88 cm west, peak robot/cart contact 241.79 N, and maximum hand tracking error
5.93 cm. This is not evidence of improved control: the measured stance differed,
contact included substantial vertical force and later braking, and more ankle
targets hit their limits. `feedback_audit.json` records the force reconstruction
and native-PD limitations. The force mapping itself was independently checked
against MuJoCo's wrench mapping.

North-side lateral pushing was screened offline in `runs/north-plan-force-probe`.
The tested poses could not statically sustain the assumed 82 N wheel-skidding
reaction within the original waist torque limit. A successful accelerating WBC
QP was explicitly not counted as static equilibrium. This rejects those poses,
not all possible cart-repositioning strategies.

`cargo_plan.py` screens both the actual cargo and the loading pallet. Its
`success` flag covers geometry and unloaded support; the separate `force_147N`
diagnostic reports whether an assumed horizontal cargo reaction is feasible.
Neither flag certifies physical cargo motion. `direct_box_push_analysis.json`
records why a short contact/slide probe is needed before attempting pallet
unloading or the long delivery route.

A second MuJoCo cache issue was found during cargo development: `geom_sameframe`
could cause runtime proxy quaternion changes to be ignored. Moving proxies now
explicitly disable that shortcut, as well as the earlier midphase issue. Saved
world reach references for `wbc-cart-v3` and `wbc-cart-front-fast-v3` were
re-screened with corrected geometry: 801 samples each, no penetration above the
2 mm tolerance. See their `reach_world_geometry_audit.json`; this excludes the
intentional contact stroke, wheels, cargo and pallet. Old local planning reports
alone must not be treated as collision certificates. This
affects the reference model, not the original Genesis physics or recorded task
outcomes. Frame-invariance audits are saved with the offline cargo probes.

Contact-stroke planning now uses the measured mean foot yaw instead of torso
yaw. This avoids accidentally commanding a foot rotation when the torso turns
during a crouch. The cargo pallet and cargo proxy use the same planning frame.

The default runner now uses `bounded_wbc.py`, a local H2 adaptation that includes
the leg native-PD target bounds inside the QP. The shared H1 implementation is
unchanged; `--legacy-wbc` selects it for comparison. Offline re-solving of 29
previously clipped control steps produced feasible targets without clipping.
Twenty-five static samples from the high-palm cargo reach also passed. Neither
check proves successful dynamic pushing.

`runs/wbc-cargo-v1` is an interrupted diagnostic, not a completed rollout. Its
full trace was not saved and the interrupted MP4 is not playable; see
`interrupted.json`. The saved world reach was re-screened, but that does not
certify its physical execution. The video writer now suppresses FFmpeg progress
output to avoid filling an unread stderr pipe during lengthy planning pauses.

## Heavy-cargo contact probe

`runs/wbc-cargo-v2` used the original 25 kg cargo, a 0.55 m palm target,
0.60 m crouch target, 0.08 m forward COM shift, measured reaction feedback,
and the bounded WBC. In 32.84 simulated seconds it moved the cargo 20.94 mm
forward on the pallet. Original task failure and success both remained false;
the cart stayed parked and the cargo was not loaded or delivered.

The controller stopped when hand tracking error reached 60 mm, before release
or standing recovery. Maximum sampled box contact was 113.28 N, entirely at the
two thumb links; robot-pallet contact was zero. The saved-state audit found
backward sole motion of about 16 mm left and 42 mm right during pushing.
Leg position targets no longer clipped, but bounded torque feasibility did not
prevent this support drift. The maximum recorded QP bound residual was
1.05e-6 Nm. See `execution_audit.json` and `execution-audit-*.png`.

Measured upward force on the box can partly reduce pallet loading. It does not
by itself explain motion below an ideal horizontal-only 147 N friction estimate:
box-pallet forces and the complete 200 Hz contact history were not recorded,
and the unchanged simulator's contact/friction regularization may contribute.
The observation establishes a short physical slide, not a measured breakaway
force or sustained pushing capability.

An independent world-frame reach audit checked 2,401 reference samples against
robot self-collision, cargo, pallet and floor geometry. No penetration exceeded
the 2 mm screening tolerance. This does not certify the intentional contact
stroke, physical replay, or the full task.

`--recover-on-contact-stop --recover` reverses only the reached stroke prefix
when the push tracking/contact guard fires, then reverses the reach trajectory.
It avoids starting release at the unexecuted full-stroke endpoint. Original task
failure and actuator limits continue to apply; recovery remains a behavior to
verify in each physical run, not a guarantee from the reference geometry.

`runs/wbc-cargo-v3` tested that reversal with the hand-error guard reduced to
45 mm. It failed the original robot-tilt condition at 43.08 s: root upright
score 0.49875, below 0.5. The box moved 22.41 mm, but hand contact persisted
through release and the attempted recovery. At release end the modeled heel
corners were approximately 55 mm above the floor. The WBC's reference-based
flat-foot support assumption therefore did not describe actual support. This
is a failed recovery, not a completed manipulation primitive.

`--measured-release` instead replans an 8 cm backward hand motion from the
measured pose at a contact stop. The offline check in
`runs/cargo-v3-measured-release` passed geometry and unloaded static support at
41 poses, ending with approximately 79 mm hand/cargo clearance. Those checks
do not establish physical withdrawal or standing recovery. In particular,
returning to the old reach path after foot motion is still a separate issue.

`runs/wbc-cargo-v4` physically verified measured-pose withdrawal: hand contact
cleared during release and stayed zero through its end, with about 1.2 mm final
hand tracking error. The cargo moved 10.98 mm. Switching to the old reversed
reach then caused an approximately 49 mm hand-error jump, renewed box contact,
and ultimately the original tilt failure at 42.14 s. Robot-pallet contact also
occurred during this failed recovery. Withdrawal alone is not standing recovery.

`recovery_plan.py` instead aligns the old reach targets to the current stance
and re-solves IK with the current feet fixed, including a continuous hand/COM
transition. `--measured-recovery` enables this optional cargo path and refuses
standing while sampled box contact exceeds 1 N. The planner rejects initial
heel/toe corners more than 3 mm from the floor, and retains the 2 mm collision
screen and 90% unloaded static effort check. An offline retract endpoint passed;
the actual raised-heel state from v3 was rejected. Dynamic execution and the
native-PD constraints still need validation in each run.

The actual v4 release endpoint also passed the new recovery screen after
increasing reference sampling: 141 poses and 1,401 dense world samples, maximum
adjacent joint change 0.10837 rad, final root height 0.72172 m. The earlier
coarser sample was rejected at 0.16095 rad; its report is retained in
`runs/cargo-v4-measured-recovery`, and the accepted one is in its `stride2`
subdirectory. No acceptance threshold was relaxed.

To run the cargo contact/release/recovery candidate from the original reset:

```powershell
& ../genesis_env/Scripts/python.exe humanoid/g1_cart_assisted_transport/solution/run_whole_body.py --object cargo --approach-x .99 --seconds 85 --duration 20 --reach-height .55 --crouch-height .60 --com-forward-shift .08 --samples-per-stage 60 --stroke-duration 6 --contact-force-limit 300 --tracking-error-limit .045 --measured-contact-wrench --video --push-distance .10 --recover --recover-on-contact-stop --measured-release --measured-recovery --center-com-before-recovery --out humanoid/g1_cart_assisted_transport/solution/runs/cargo-new
```

The requested 10 cm is a hand-reference stroke, not a promised cargo distance;
the tracking/contact guard can end it early. Inspect `result.json`, the phase
reports and video before treating any run as an executed primitive.

`runs/wbc-cargo-v5` executed all scheduled phases for 61.90 s without original
task failure, but **did not achieve a valid recovery**. After approximately
2.5 cm of controlled cargo motion and a clean withdrawal, recovery tracking
degraded around 50.5--52 s. It subsequently contacted the cargo and pallet again.
The final 5.95 cm cargo displacement includes that unwanted motion; final hand
error was approximately 30 cm. Its historical `probe_complete_after_contact_stop`
reason means the timer expired, not that the robot recovered successfully.

The saved reference remained statically feasible with native-PD leg bounds,
but the difficult section had only about 1.25 Nm common positive ankle margin.
The actual 50.5 s state had about 0.96 Nm margin; by 51.5 s the measured posture
was statically infeasible, before renewed box contact. The reference retained
about 80 mm of forward COM shift until late in the rise. These diagnostics are
in `recovery_native_pd_*_audit.json`; they do not establish global infeasibility.

The current runner stops recovery on excessive tracking error or renewed object
contact. It also requires a two-second settled endpoint with low root speeds,
upright posture, root-height agreement, hand error below 20 mm and object
contact below 1 N. Saved-state regression checks reject the v5 endpoint and
accept the earlier cart-v3 endpoint (`runs/recovery_endpoint_validation.json`).

Subsequent review fixes execute the new recovery start on the transition step
and bound the planner's initial foot-pose correction to 3 mm / 0.02 rad.
The v4 stance still passes, while a flat-foot test with split foot yaw is rejected.
Earlier run snapshots retain their original implementations.

`--center-com-before-recovery`, used with `--measured-recovery`, first returns
COM to the stance-aligned standing target during the low-pose transition, then
holds it there while rising. The v5 measured withdrawal endpoint passed this
variant's geometry and unloaded support screen. Physical outcomes must still
be inspected separately.

## Completed short cargo primitive

`runs/wbc-cargo-v6` used the centered-COM recovery and the current reviewed
controller. In 3,066 control steps / 61.32 s, the cargo moved 8.588 mm forward
and 1.196 mm laterally. Peak sampled robot/cargo force was 111.79 N. The original
task reported neither failure nor success, and the cargo remained on its pallet.

Withdrawal and standing recovery completed with no object contact during the
final two seconds. All endpoint checks passed: upright posture, root height,
low linear/angular velocity, hand tracking, absence of object contact and
absence of original task failure. Maximum hand error over that final window
was 0.741 mm. The data-integrity audit also passed; it is not a physics replay.
The run includes video, observations/actions, states, phase planning reports,
and snapshots of all local controller/planner modules used in that execution.
The independent `execution_audit.json` also confirms flat-foot support in the
final window, recovery-phase foot drift below 0.20 mm, no robot-pallet contact,
and no meaningful leg-target clipping. Its three extracted video frames were
visually checked. All six current local controller/planner source files match
the snapshots saved by v6.

This result establishes a short push/release/stand sequence in one default-start
run. Earlier attempts obtained larger cargo displacements but did not complete
a valid recovery. Sustained pushing, pallet unloading, cart docking/loading,
passage transport, independent replay and multiple-start validation remain open.

## Standing foot push: completed empty-cart primitive

`runs/foot-cart-v5` completed a different default-start primitive: navigate to
the rear of the empty cart, transfer weight to the left foot, push the deck
with the raised right foot, withdraw, land in a narrower stance, and recover.
The cart moved **0.603907 m**, including its passive coast, in **42.92 s / 2,146
control steps**. Peak sampled robot/cart force was **39.33 N**. The final cart
speed was 0.00591 m/s. Cargo was untouched; original task success and failure
were both false. This is an empty-cart motion primitive, not a full H2 solution.

The runner uses the original joint-action interface and original motor gains,
limits, scene, masses and friction. `new_strategy/foot_wbc.py` adds a measured
horizontal COM tracking cost to the bounded WBC; its hard constraints remain
the same. The right foot physically lands at a 0.20 m stance width. At touchdown,
the controller holds the last single-support reference until all measured sole
corners satisfy the existing 3 mm floor-height check, with a two-second timeout.
This run waited approximately 0.28 s before switching to double support.

The final two-second window passed all checks. Independent post-step inspection
found maximum foot-reference error 1.50 mm, sole-height error 0.222 mm, root
linear speed 0.000223 m/s and angular speed 0.000949 rad/s, with no cart contact.
During single support, the left foot drifted at most 1.44 mm and lateral COM
offset was below 1.00 mm. Original leg PD targets stayed within their limits.
`audit.json` checks data integrity; `independent_foot_audit.json` checks the saved
execution. Neither is an independent physics replay. Contact and final video
frames were also visually inspected.

To run the current candidate from the original reset, use a new output folder:

```powershell
& ../genesis_env/Scripts/python.exe humanoid/g1_cart_assisted_transport/solution/new_strategy/run_foot_push.py --video --lift-duration 3 --press-duration 2 --retract-duration 1.6 --landing-width .20 --landing-wait 2 --com-task-weight 1000 --support-com-limit .04 --out humanoid/g1_cart_assisted_transport/solution/runs/foot-cart-new
```

The run includes `motion.mp4`, `rollout.npz` (actions and observations),
`trace.json`, measured-start and planned-reference NPZs, result/audit JSONs,
source snapshots, and hashes of the unchanged environment sources. Feedback
and fresh measured-state planning are required; the recorded action sequence
is not a certified open-loop replay policy.

The intermediate attempts explain the changes:

| Run | Measured cart motion | Outcome |
| --- | ---: | --- |
| foot-cart-v1 | 0.243 m | Lateral balance deteriorated during withdrawal. |
| foot-cart-v2 | Not a complete data record | Reached recovery in the log, but result serialization failed; excluded from validated references. |
| foot-cart-v3 | 0.415 m | COM stayed stable; the returning right ankle reached its roll limit. |
| foot-cart-v4 | 0.537 m | Narrow landing fixed withdrawal; the floor-height gate stopped before the heel finished settling. |
| foot-cart-v5 | 0.604 m | Withdrawal, measured landing and settled recovery passed. |

The original wheel inertia matters. Native readback confirms each wheel has
armature **0.1 kg m^2** and damping **0.03 N m s/rad**. Including armature, the
approximate rolling effective mass is **77.5 kg**, rather than the earlier
15 kg estimate that omitted it. The resulting predicted coast decay agrees
with measured decay within about 0.15%. This explains why the initial 0.8 s
foot stroke produced much more force than the preliminary 12 N estimate.
`new_strategy/cart_rolling_inertia_audit.json` preserves the source evidence,
model limitations and native readback. The current stroke takes two seconds.

Further unloading screens are recorded in `runs/cargo-strategy-v6/summary.json`,
`runs/new-strategy-alternatives-summary.json`, and the `new-strategy-knee*` run
directories. These are geometric/static hypotheses, not physical cargo runs.
Lower hand pushes, ground side grasps and several pallet poses did not yield
a validated unloading action. Full cart docking, unloading/loading, loaded
steering through both passages and delivery remain unverified.

The latest unloading hypothesis is more promising than the low hand pushes:
stand on the pallet's rear strip and use both knees against the cargo rear face.
`runs/new-strategy-knee-tall-summary.json` describes two collision-free endpoints
with root height 0.95 m and feet at x=1.22 m, y=+/-0.14 m, sole height 0.23 m.
Under assumed horizontal knee reaction, original native-PD limits and 90% rated
effort, the COM-x=1.27 m endpoint supports 0--98.23 N and the COM-x=1.34 m
endpoint supports 29.87--166.92 N. The latter passes the 147.15 N pallet-friction
hypothesis with 19.77 N reserve. Raising the body reduced waist gravity torque;
the knee reaction itself does not pass through the waist joints.

These are static endpoints with a 0.5 mm precontact gap, not an executed push.
Their force intervals overlap, but that does not prove a continuous contact
transition. A collision-free climb onto the pallet, contact establishment,
gradual loading, sustained cargo motion and recovery still require planning
and original-environment execution before this can become an expert reference.

## Cart-following traction and fast-ramp floor push (2026-10-19, late)

Two candidates were added after v10 (handle) and v8 (floor push) finished.
Both keep every original guard; both are physically executed and both still
fail their own probe gates. Nothing here is an expert certificate.

**Handle: `new_strategy/cart_handle_follow_control.py`, runner flag
`--follow-traction` (requires `--window-traction`).** v10 showed the cause of
the empty traction phase: the cart coasted at 2.6 mm/s while the seek-phase
*world* wrist reference cap was the 2.5 mm/s probe value, so the hands fell
behind the bar and a single common offset grew at most 0.3 mm/s; only the
right hand ever touched (peak 0.42 N, bilateral dwell 0 s). The follow
controller raises the seek-phase world cap to 20 mm/s and governs the axial
offset per hand from the real 5 ms window side sums (0.25 N per hand,
1.5 mm/s relative cap, unchanged 1.5 mm offset and -1.5 mm geometry floor).
Run `runs/cart-handle-approach-v11-follow-b` (the first `v11-follow` died on
an import-cache error before traction): pregrip complete 65.24 s, both hands
in contact from 65.60 s, hand error 0.1 mm while the reference followed the
cart at up to 3.1 mm/s, 28 of 38 contact windows bilateral above 0.05 N with
window axial above 0.2 N. The contact chatters between hands at the sub-newton
level, so 40 consecutive good 5 ms samples never occurred, and the unchanged
3 mm/s envelope released at 66.34 s. Released advance 12.1 mm, 2 s quiet coast,
`short_traction_success` false. The reference-lag cause is fixed; the remaining
blocker is the gate itself: with the cart's ~80 kg effective inertia and
free rolling, 0.2 s of continuous bilateral 5 ms contact at >=0.2 N axial must
be accumulated from rest before 3 mm/s, which chattering finger/bar contact
does not deliver.

Update 2026-10-20: at the author's request the evidence gate was changed to a
cumulative count (`cumulative_contact_evidence=True`): 0.2 s of real 5 ms
samples with axial > 0.2 N and each hand > 0.05 N accumulated during
seek/traction, consecutive dwell still reported, 10 mm released advance and the
2 s quiet coast unchanged. `runs/cart-handle-approach-v12b-follow-cumulative`
passes the probe: pregrip 62.40 s, evidence latched 63.24 s, the measured cart
velocity servo towed the cart at 2.0-2.3 mm/s with hand error below 0.1 mm,
10 mm advance at 67.70 s, measured release, 2 s coast, runner reason
`measured_handle_short_traction_complete` at 75.72 s (17.1 mm total advance).
`v12-follow-cumulative` before it stopped at 40 s on navigation scatter (10.5 cm
stop error, pregrip IK rejected), not on the gate. This is a 10 mm probe
certificate for the revised cart, not docking.

**Floor push: `new_strategy/ground_loading_fast_plan.py`,
`ground_loading_fast_dynamics.py`, `ground_loading_fast_control.py`, runner
flag `--fast-push` (requires `--window-short-push`).** Parametrised force
hypothesis and rise through the unchanged plan/static/native screens; force
ramp 1000 N/s instead of 250 N/s; 0.06 m/s box speed target. Offline on the v8
source, 140/40 N passes (21 poses, 36 native checks) while 150/43 N and
160/46 N are statically infeasible at reserve 0.9 (capacity 146 N). Run
`runs/ground-loading-v9-fast-ramp`: target 140 N at 27.08 s, measured force
120.7 N at 27.44 s, box 0.69 mm, 4 mm stance reserve released at 28.00 s.

Diagnosis (offline LP on the v7/v8/v9 states, `expert_progress.json`
`ground_capacity_diagnosis`): the live patch-capacity LP is bound by the
**waist pitch PD torque near its -0.52 rad joint limit** (kp 5000, effort
50 N m: 0.9 effort needs 9 mrad of margin; the crouch leaves 10.3 mrad). Under
load the waist sags toward the limit (v9: 10.4 -> 7.8 -> 6.7 mrad as force
reached 100 -> 121 -> 112 N) and the capacity collapses 146 -> 127 -> 94 N, so
the governor lowers its own target below the ~125-130 N breakaway. v7 happened
to keep 11 mrad and reached 124 N for one slip burst (3.98 mm); v8 started at
7 mrad (85 N). A steeper lift does not help in this posture (lift ratio 0.35
gives 130 N, 0.5 gives 106 N at v7's posture). Foot creep is proportional to
horizontal impulse (5.9e-5 m per N s), so the 4 mm reserve is about 45 N s.
The floor push therefore needs a crouch with >=30 mrad waist pitch margin
(for example a higher hand contact around 0.45-0.50 m with an upright torso)
before any further attempt; ramp rate and hypothesis size are exhausted.


## Floor-push expert (passing, 2026-10-20)

See `floor_push/README.md`. First pass `floor_push/runs/trial-v23`
(`task_success` at 95.27 s, hold 2.0 s, cargo at (9.44, 0.69), yaw 0.2 deg;
legs 30 / 12.5 / 23 s; mean push force 26-28 N; lane error < 5 cm). Audit:
`floor_push/audit_floor_push.py <run>` recomputes the success predicate from
the trace. The task defaults in `task_spec.py` were changed to these conditions
(previous values are kept in a comment there); the Isaac backend reads the same
fields but was not run.

## Cart-required expert (passing, 2026-10-20, late)

See `floor_push/README.md`, "Cart-required expert". First pass
`floor_push/runs/cart-v54` (`task_success` at 75.3 s, loaded at 15.5 s, legs end
at 15.5 / 24.2 / 47.9 / 69.7 s, cargo on the dolly at (9.59, 0.66), yaw -0.07
rad, dwell 2.3 s, max impact 230 N). Audit: `floor_push/audit_cart_push.py
<run>` recomputes the on-cart success predicate from the trace. Trials
cart-v1..v54 with one-line outcomes are in `expert_progress.json`
(`cart_required_revision.trials`); the design history is in
`FEASIBILITY_CONDITIONS.md`. The Isaac backend has not been run with this scene
(the fixed wedge, funnel lips and curb exist only in `genesis_env.py`).
