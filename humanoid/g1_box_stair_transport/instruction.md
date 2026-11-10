# G1 box transport over stairs

Pick up the box from the ground with both hands. Carry it up the stairs, pass
through the highest platform with both feet supported, and descend the stairs
on the opposite side. Visit every tread in order. At the marked ground goal,
gently place the whole box inside the goal, release it, and stand upright with
both feet inside the goal. Keep the box on the ground and remain stable for
2 seconds. The default scene has 10 upward and 10 downward steps; supported
scene variants have 2–10 steps on each side.

Keep carrying the box throughout the route. Do not drag, throw, drop, or rest it
on the stairs or platform. Ground contact is permitted when picking up the box
and during controlled placement at the destination. Do not skip a tread, bypass
the highest platform, leave the route, or use non-foot contact with the scene
to support the robot. A successful placement requires lowering the box while
still holding it, releasing both hands after touchdown, and standing upright.
Holding the box at the destination does not complete the task.

Use the robot-mounted observations and the supplied joint command interface.
Your own code, perception, planning, IK/FK, and provided robot skills may help;
they must execute through that same physical interface. You may not change
world or robot state, attach the box, alter physical properties, read private
scenario or scoring files, or inject observations or contacts. A private robot
model for planning does not change the simulated world.

Call `info()` for the enabled sensors, actuator limits and episode budgets;
`observe()` reads sensors. Send joint targets with `command()` or
`command_sequence()`, and call `finish()` when done. Development resets are
budgeted; evaluation and grading allow no resets. Grading runs the submitted
program in fresh episodes. The score is 1 only for the complete physical task
and 0 otherwise; partial progress does not earn positive score. The interface
does not reveal private stage progress or the score during execution.
