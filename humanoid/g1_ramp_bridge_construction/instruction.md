# G1 retrieval across a gap

A box rests on a pedestal on the far side of a gap in the floor. Bring the box back
to this side and leave it at rest inside the green square marked on the floor, and
keep it there for at least 2 seconds. You may interact with any object in the room.

The episode ends when you call `finish()`, when the simulated time budget runs out,
or when the robot falls (pelvis below 0.35 m or tilted more than 50 degrees from
upright). Falling into the gap is a fall. The box must not end up in the gap.

Use the robot-mounted observations and the supplied joint command interface. Your
own code, perception, planning, IK/FK and the provided robot skills may help; they
must execute through that same physical interface. You may not change world or
robot state, attach objects to the robot, alter physical properties, read private
scenario or scoring files, or inject observations or contacts. A private robot model
for planning does not change the simulated world.

Call `info()` for the enabled sensors, actuator limits and episode budgets;
`observe()` reads sensors. Send joint targets with `command()` or
`command_sequence()`, and call `finish()` when done. Development resets are
budgeted; evaluation and grading allow no resets. Grading runs your delivered
program in fresh episodes whose layout differs from the development episode.
Credit is given for physical progress along the task, judged from what happened
in the simulator; the interface does not reveal progress or the score while you
run.
