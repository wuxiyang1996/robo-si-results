# Designer solution

The oracle produces a high-level plan, skill constraints, key states and a
budgeted screening report. Complete trajectories are optional evidence for the
small [representative cohort](../validation/representative_plan.json), never a
prerequisite for every random instance. Observed operating points do not establish
continuous applicability ranges.

For concrete-case hierarchical acceptance, use the
[expanded low-level plan and trajectory mapping](../validation/hierarchical/README.md).
It reuses two complete expert executions, retaining their preparation and support
handoff segments. Each high-level goal is linked through low-level actions to
measured completion on the same continuous trajectory. Generic rolling planning,
arbitrary skill-to-skill composition and random robustness are separate extensions;
they are not prerequisites for this evidence. The expansion is retrospective and
does not claim that the annotation document existed before execution.

1. Place a straight thumb outside the far rim and gently slide the supported disk
   to the table edge. Stop from measured overhang and contact conditions.
2. Insert both hands at the exposed edge. Each hand establishes its own inward
   thumb–finger contact on both disk faces. Regulate measured finger loads using
   their contact lever arms; a touch flag alone is insufficient.
3. Lift both pinches together until the disk has clearance for its entire turn.
4. Rotate the hand frames with a 60-second minimum-jerk reference, wrist-housing
   clearance and tangential-force feedback. Near inversion, if the normal-only
   wrench model becomes infeasible while both measured pinches remain valid,
   bounded per-hand pressure feedback can finish the turn. The physical evaluator
   continues enforcing the original force, speed and grasp limits.
5. Settle the inverted disk, transfer its weight to the right pinch, and release
   the left hand. Carry the holding hand outside the table edge and lower the
   disk to table height. The left thumb pushes the near rim while the right thumb
   opens clear of the side. After the disk center is supported inside the table,
   withdraw the lower finger pads continuously and pause forward pushing until
   they clear. Finish pushing at tabletop rim height, then release for two seconds.

`controller.py` selects skills from measured stage completion. Each skill derives
local goals from current disk and hand state. `RollingPlanner(horizon=1)` solves
and executes one joint-reference step at a time in this implementation. The separate MuJoCo IK model is
used for local robot geometry; physical motion and contact are executed in Genesis.
The policy changes joint targets only.

The final placement guards matter: an opening thumb tip can leave the proximal
thumb against the disk's side; waiting for nearly all the weight to reach the
table can trap the disk against lower pads; following a descending overhanging
rim can put the pusher beneath it. The retained offset failures and subsequent
validation runs document these cases. Planned key poses are never substituted
for physical transitions.

The [task README](../README.md) lists the exact reference configurations, limits,
commands and evidence scope. `validate_release.py` packages complete runs and
independent replays only after their checks pass. `evidence.py` verifies the
resulting operating-point catalog before the offline oracle uses it. Failed
attempts and checkpoint fragments remain in the attempt ledger; they are not
promoted into complete witnesses.
