# UR10e table-tennis reference design

This is a new scoped reference candidate, outside the historical 14-task count.
The implementation and physical evidence use the task's own frozen
`stage-scoring/1` rubric; full success and formal admission are separate.

## Representation refinement

| High-level goal | Low-level refinement | Measured realization |
|---|---|---|
| Prepare interception | approach | Reference polynomial, actual joint endpoint and collision/speed checks |
| Return to target | strike → follow_through | Real racket impact within the action interval, outgoing net clearance and first target landing |
| Recover ready | recover → hold | Real ready-pose tolerance, joint speed and terminal dwell |

The selected witness is `nominal-r0`. All five actions cover the same continuous
2.4 s execution. Command intervals are contiguous, half-open and nonoverlapping;
entry/exit state rows are linked explicitly. Position, velocity and acceleration
references regenerate from the recorded quintic coefficients. Actual 2 kHz
states and motor torques remain distinct from planned reference values.

The independent grader uses ball contacts, measured net crossing, first landing
and arm recovery. It never reads controller stage labels. Full success requires
one legal own-half bounce, one racket impact, valid net clearance, target landing,
recovery and no physical or integrity violation. The three mapping checks are
recorded in every campaign attempt's audit.

## Scope and evidence

Four public exact configurations, three resets each: 12/12 complete references.
Four original torque streams also reproduce the states in fresh physics scenes.
The stationary-arm control scores 25/100 without full success; an invalid wide
feed is retained at zero. Numerical impact checks and evidence-tampering tests
are separate from successful demonstrations.

Evidence lives in the source checkout at
`single_arm/ur10e_table_tennis/acceptance/reference-v1/`, or in `evidence/` at the
root of the release bundle. See the [task page](../task-table-tennis-en.html),
[task design](../planning/table-tennis/task-design.json), and
[expert contract](../../single_arm/ur10e_table_tennis/expert_contract.json).

The minimum existential design gate is met in the recorded configurations.
Random robustness, arbitrary skill composition, vision, continuous rallies,
humanoid doubles, untrusted-agent sandbox admission, human sign-off and
independent-person reproduction remain separate. Planning uses CUDA on Gamma;
MuJoCo rigid-body/contact integration uses CPU and videos use GPU EGL.
