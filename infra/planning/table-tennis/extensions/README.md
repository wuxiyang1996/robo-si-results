# Table-tennis task and metric design: interception, relocation and rallies

Version: `table-tennis-extensions/0.1.0`. **Owner-approved task and metric design for publication. Physical implementation remains pending.** No stepping, rail/mobile-arm or rally execution is certified by this document. The existing UR10e and stationary G1 single-return releases retain their original scores, contracts and evidence. Proposed thresholds below require calibration, then freezing before evaluation. [Release](https://github.com/wuxiyang1996/robo-si/releases/tag/table-tennis-0.1.0) · [Approval](../publication/approval.json) · [Machine-readable specification](metrics.json) · [中文任务页](../../../task-table-tennis-metrics-zh.html) · [English task page](../../../task-table-tennis-metrics-en.html).

## 1. Task matrix

| Family | G1 | Fixed-base UR10e | UR10e on a powered rail |
| --- | --- | --- | --- |
| I: single interception | Step toward the assigned interception region, return one ball to target, recover | Move the racket across a wide feasible workspace, return one ball to target, recover | Translate the carriage toward the interception region, return one ball to target, recover |
| R: continuous rally | Stationary stance; repeatedly return the same ball against a frozen physical opponent | Repeatedly return the same ball against that opponent | Carriage locked for this track; repeated returns |
| MR: relocation during rally | Step on designated wide incoming shots while maintaining the rally | Not applicable: arm joint motion is not base relocation | Move the carriage on designated wide shots while maintaining the rally |

An arm on a wheeled base is a separate future profile, not equivalent to a rail: add wheel contact, slip, base tipping, braking and obstacle checks before enabling it. Its controller and certified operating envelope are presently null. For the rail, motion must arise from a bounded actuator on an inertial carriage, with rail travel limits and physical arm/carriage coupling; changing the base transform does not count.

The primary rally horizon is **N = 10 G1/arm legal returns**, not ten combined contacts by both players. Report the same survival curve at 1, 3, 5, 10 and 20; N=20 requires a separately prescribed longer episode. An exchange is completed by a legal subject return landing on the opponent half. A physical opponent must then return that same ball to create the next opportunity. Alternating independent feeds are a useful auxiliary **feed endurance** task, never a continuous-rally result.

## 2. Environment protocol and trusted events

Each episode freezes robot/model/controller versions, observation mode, feed seed, target regions, opponent identity and policy, rail/support configuration, actuator bounds, deadline, thresholds and metric version. The environment creates episode/ball/shot IDs. The controller cannot assign identities, mark a shot legal, declare a step, or write simulator state. Privileged-state and visual-observation tracks have separate results; observation latency and noise are recorded.

For every subject shot, the independent validator checks this sequence: one incoming bounce on the subject half → one racket impact → net clearance within table width and without net contact → first subsequent bounce on the opponent half. Double hits, volleys, wrong-side first bounces, out-of-bounds balls and non-racket ball contacts invalidate that shot. Once the rally first fails, later shots cannot extend its initial consecutive prefix. Contact-event merging uses physical separation and a frozen hysteresis rule, not a long time window that could conceal two impacts. Preserve raw contacts for audit.

No ball reset, replacement, velocity assignment or hidden relaunch is allowed within a rally. The opponent acts through a recorded physical actuator interface, with bounded paddle speed/acceleration and a preregistered return envelope. A cooperative benchmark opponent is evaluated separately from self-play or competition. Its settings must be the same across systems on the common-domain track. An opponent miss terminates the rally; preserve partial credit and mark the cause, without silently replacing the episode or shrinking its denominator. Report opponent fault rates separately. A post-failure diagnostic rollout cannot restart scoring.

Every incoming opportunity has a finite deadline and an allowed flight-time/speed envelope fixed before the run. A first draft uses a 3 s maximum per exchange and a 35 s episode timeout for N=10, including terminal recovery; these are parameters to calibrate, not measured feasibility claims. Failure to progress reaches timeout; waiting or arbitrarily slow lobs cannot earn extra rally length. After the Nth verified landing, the opponent stops striking, while the subject completes a declared 0.25 s recovery dwell within the remaining episode. Normal task terminal conditions are valid early terminations; a crash or missing trace is not.

## 3. Positioning and support contracts

### G1 stepping

A step must occur after reset and before the associated subject strike. It requires measured unloading, sole clearance, a new horizontal foothold and renewed load-bearing contact. Draft thresholds: force-off <2 N, force-on >5 N, sole clearance ≥2 cm, foot displacement ≥8 cm, and renewed load for ≥50 ms. Contact hysteresis must last ≥10 ms. At completion, pelvis distance to the environment's assigned interception region must have decreased by ≥5 cm since opportunity start. A hop in place, dragging a loaded foot, a decorative step after hitting, or repeated relabeling of one step earns no relocation credit. A crossover step is allowed if it meets the same physical constraints.

Interception regions and relocation-required shot IDs come from the frozen task instance, never the expert's chosen plan. In MR the first draft requires **M = 4** relocation opportunities among N=10, with at least one left and one right relocation and a direction reversal. Each has a start event and a pre-strike deadline. Credit at most once per opportunity; extra shuffling earns no points. Missing a required relocation can still yield a legal ball return, but fails the relocation task. Only already-started opportunities can earn movement credit; future slots cannot be pre-completed.

The moving G1 validator permits single-foot support. Do not reuse the stationary controller's requirement that both feet remain loaded at every timestep. Draft gait constraints: no continuous zero-support interval >20 ms, no non-foot ground contact, and no forbidden body/table/self collision. Root height <0.55 m or tilt >35° for >50 ms is a fall; a non-foot ground impact terminates immediately. Stance slip is integrated horizontal sole motion only while that foot is loaded; swing-foot travel is excluded. Report slip per stance and total, with a draft 4 cm maximum per stance. Motor and joint bounds remain model-specific and independently checked. These are simulation task conventions, not hardware safety limits.

### Fixed arm and rail-mounted arm

Fixed UR10e I credit is measured **racket preparation**, not locomotion. The racket enters the environment's ball-intercept preparation region before impact, with a feasible orientation/velocity envelope. Draft minimum: 2 cm Cartesian translation from reset, position error ≤5 cm and normal-angle error ≤15° continuously for 20 ms before the strike. Reference position/normal envelopes are task-defined sets derived from legal return geometry; do not grade similarity to the expert's selected trajectory. Easy feeds already covered at reset are a separate stationary diagnostic, not this wide-interception task.

Rail I/MR credit requires measured carriage displacement ≥8 cm and ≥5 cm reduction in distance to its assigned interception region before the strike. Check rail limits, carriage speed/acceleration/effort, arm limits, pedestal/table collisions and coupled dynamics. Carriage mass, range, actuator and speed limits must be supplied and frozen before any rail run; their values are null in this design. Do not award rail/step metrics to a fixed-base arm, or score its inapplicable fall/foot metrics as perfect results.

### Terminal recovery

Recovery is a live predicate, maintained for ≥0.25 s at the task endpoint. For I it follows a target return and valid positioning; for R it follows N legal consecutive returns; for MR it also requires all M assigned relocations. Require zero fatal violations throughout. G1: both feet loaded, tilt ≤5°, root height ≥0.65 m, base linear speed ≤0.03 m/s and angular speed ≤0.05 rad/s. Rail arm: carriage speed ≤0.02 m/s and position inside the declared recovery region. All profiles: joint speed ≤0.08 rad/s and racket position/normal inside a preregistered ready envelope. Recovery regions may move with the legal final stance/carriage position; do not require returning to the original world pose or reproducing expert joint angles.

## 4. Metrics and denominators

| Metric ID | Exact definition / aggregation | Purpose |
| --- | --- | --- |
| `task_success_rate` | Full physical task successes / all prescribed episodes; report numerator and denominator | Primary endpoint for each profile |
| `legal_return_rate` | Verified legal subject returns / started subject incoming opportunities; also publish counts and per-episode rates | Ball handling; explicitly conditional on opportunities reached |
| `prescribed_return_coverage` | Sum of legal prefix counts / sum of prescribed N across all episodes, with missing episodes contributing zero | Prevent early termination from improving the denominator |
| `target_hit_rate` | Verified target first-landings / legal returns; undefined when no legal return | Precision conditional on legal play |
| `target_coverage` | Target landings in valid prefix / prescribed N | Precision including failures and missing shots |
| `landing_error_m` | XY distance from first legal landing to the announced target center; median and p90 over legal returns, with sample count | Accuracy, alongside coverage; misses do not become zero error |
| `consecutive_returns` | Length C of the initial valid rally prefix; missing, corrupt and unexecuted episodes contribute zero to official aggregation | Continuity; no best-subsequence cherry-picking |
| `survival_at_k` | Episodes with C ≥ k / all prescribed episodes with N ≥ k | Reliability at 1/3/5/10/20 returns |
| `relocation_completion_rate` | Completed assigned relocations / all prescribed relocation slots | Required movement; fixed arm is N/A |
| `racket_preparation_rate` | Completed fixed-arm preparation windows / all prescribed I episodes | Fixed-arm counterpart to positioning |
| `recovery_rate` | Episodes ending in the gated live recovery condition / all prescribed episodes | Continued control after the goal |
| `fall_rate`, `collision_rate`, `limit_violation_rate` | Episodes with each event / all prescribed episodes, with observed-trace coverage | Independent failure reports; fixed-arm fall is N/A |
| `stance_slip_m` | Integrated horizontal sole motion during each loaded stance; p95 and max | G1 contact quality; no swing penalty |
| `carriage_tracking_and_limits` | Carriage motion, max speed/acceleration, end-stop contacts and limit violations | Rail validity, separate from arm motion |
| `energy_J_per_legal_return` | Integral sum_j |tau_j * qdot_j| dt, including rail drive power / legal returns; null if none | Secondary efficiency, not reward for doing nothing |
| `replanning_latency_ms` | Measured perception-to-command p50/p95 and missed-deadline fraction on declared hardware | Deployment diagnostic; pre-clock planning cannot claim real time |

G1 COM/support-polygon margin may be a diagnostic but is not an exclusive dynamic-balance criterion: during a valid step COM projection can leave the instantaneous support polygon. Falling, support loss, contact violations and recovery are evaluated from physical state. Do not compare raw joint effort, foot path or energy across different embodiments as if they were an identical capability.

## 5. Stage scores, success and failure

All scores use the repository's `stage-scoring/1` semantics: once-only milestones retain previously valid credit, live endpoints can lose credit, and integrity failures zero every awarded stage. API `score = stage_score / 100`. A physical failure ends the scored episode and prevents further credit; a valid terminal record preserves earlier valid stages. Missing prescribed episodes, crashes and untrustworthy/incomplete records contribute zero. Diagnostics from invalid data remain non-awarded fields.

**I, 100 points:** positioning 10 + legal racket impact 25 + net clearance 20 + opponent first landing 20 + target landing 15 + live recovery 10. Ball-stage dependencies remain ordered; positioning credit must precede the strike, but valid ball progress is still visible if the positioning objective is missed. Full success requires all six predicates and no fatal violation.

**R, 100 points:** `80*C/N + 10*H/N + 10*R_end`. Here C is capped at N, H is target landings within that valid prefix, and `R_end` is the gated binary terminal recovery predicate. Full rally success requires C=N, recovery and no fatal violation; precision is reported independently. Thus a legal but inaccurate complete rally may succeed below 100 points. `precision_success` additionally requires H/N ≥0.8, a draft quality threshold. Each indexed return and target landing can contribute only once.

**MR, 100 points:** `60*C/N + 20*P/M + 10*H/N + 10*R_end`, where P is completed assigned relocation slots, capped at M. Full success requires C=N, P=M, recovery and no fatal violation. A legal rally without the required moves can pass R-style continuity and still fail MR. M and its slot IDs are frozen before the episode and cannot shrink after failure. Target quality is separate, as in R.

Examples with N=10, M=4:

| Record | Score | Full task success |
| --- | --- | --- |
| R: C=6, H=4, then miss | 52 | false |
| R: C=10, H=8, recovered | 98 | true; precision_success=true |
| R: C=10, H=10, then fall before recovery | 90 | false |
| MR: C=10, H=8, P=3; all other conditions met | 83 (recovery credit withheld because P<M) | false |
| MR: C=10, H=10, P=4, recovered | 100 | true |
| Any forged/reset/missing-data record | 0, VOID | false |

Report these three scores separately. Their weights differ and they must not be averaged into an unlabeled cross-task ranking. For a matched cross-robot comparison, report common-domain legal-return coverage, survival curves and target coverage, alongside each embodiment's constraints and task score.

## 6. Difficulty, case selection and statistical reporting

Use two explicitly named evaluation domains. **Common domain:** identical physically realizable incoming ball distributions, targets, opponent, timing and observation conditions for all compared embodiments. **Embodiment envelope:** reach, step or carriage demands appropriate to each platform, with results separated by profile. A common-domain inability is a scored failure; an embodiment-envelope result cannot establish superiority on a common distribution.

Stratify feeds by left/right displacement, short/deep landing, approach speed, lead time, alternating versus repeating side, and abrupt direction reversal. Report these dimensions and actual measured travel separately; a single speed label hides reach and timing difficulty. Use initial no-spin privileged-state tracks, then introduce spin, perception delay and noise as distinct versions. For MR, freeze designated relocation slots and regions and record actual feed coordinates as well: a physical opponent cannot teleport a ball to repair a bad feed.

Before freezing the task, seek one continuous normal-reset expert witness per profile and declared difficulty family, with all three hierarchy mappings and torque/action replay. Keep unresolved candidate cases marked unknown; one failed fixed-feet IK search or one failed no-step baseline does **not** prove that a feed mathematically requires stepping. Explicit movement objectives define I/MR relocation demand. Use no-step/locked-carriage baselines as evidence of contribution, not as infeasibility certificates.

Proposed capability set: 20 exact cases per enabled profile (5 difficulty families × 2 lateral directions × 2 speed levels), each repeated 3 times. Proposed later generalization set: 100 held-out, preregistered episode seeds per profile, generated within the declared domain. These counts are future evaluation plans, not completed trials. Resolve physical instance feasibility and thresholds before freezing the seed list; after freezing, keep every attempt. No replacement of hard seeds, failed runs or opponent faults. Report macro averages over difficulty cells as well as counts and micro averages. Group repeated identical-case observations for uncertainty estimation; use a bootstrap over independent cases/seeds, not individual shots from one rally. With no witnessed data, scores and success rates are null.

## 7. Hierarchical expert and evidence contract

| High-level goal | G1 low-level actions | Arm low-level actions | Independent evidence |
| --- | --- | --- | --- |
| Reach the next interception region | shift load → swing foot → land/load → stabilize; arm preparation may overlap | fixed arm: reach preparation; rail arm: accelerate → translate → brake, coordinated with arm | Measured contacts, foot/carriage movement, deadline, reachable racket envelope |
| Make a legal return | strike → follow-through | strike → follow-through | Ordered ball contact/net/first-landing events |
| Continue the rally | reobserve opponent impact → predict → replan next interception | Same cycle with arm/rail constraints | Same ball identity, indexed alternating events, bounded planning latency |
| End in control | recover ready envelope → hold | recover arm/carriage envelope → hold | Live recovery, whole-body or carriage limits |

Use a temporal graph, not a requirement for all actions to be sequential: stepping and racket preparation can overlap. Every action has plan/revision/shot/robot IDs, entry and exit state indices, support mode, deadline, actuator command range, failure exit and dependencies. Do not concatenate reset-based single-shot trajectories as a rally. HL→LL checks goals, shot indexing and dependencies; LL→trajectory checks actual bounded commands, support transitions and contiguous time coverage; HL→trajectory independently checks movement, legal-ball prefix and terminal recovery. Skill names and expert trajectory similarity never award task points.

Required trace fields include simulation time, episode/ball/shot/actor IDs, qpos/qvel, actuator commands and bounds, racket pose/velocity, raw contact geometry/force, ball state, target ID, stance/foot pose/forces for G1, carriage state/force for rail, opponent actions, planner input timestamp/output latency, and every reset/state-write audit event. Episode output includes termination reason, valid prefix C, H, prescribed N, P/M where applicable, per-stage credit, full success, precision_success, VOID status, conditional-metric denominators and trace coverage.

## 8. Validation before enabling evaluation

Required negative fixtures: stand still on a required-step shot; drag a loaded foot; step only after impact; valid single support; a correct return followed by a fall; count swing travel as slip; score a fixed arm as having moved its base; move a rail by state assignment; illegal net/double hit/wrong first bounce; ten independent feeds labeled a rally; opponent miss; stalling; ball replacement; repeated contact ID; late target switch; missing frames; truncated crash; shrink N or M after failure; and a controller self-report of success without physical evidence.

Compare expert against hold, no-step/locked-carriage, no-replanning and ideal-observation baselines, retaining all outcomes. Add fresh action replays and timestep/contact checks before producing execution claims. Synthetic metric examples validate the specification only; they do not validate a locomotion or rally controller. GPU simulation/training is subsequent implementation work; no new cluster result is claimed here.
