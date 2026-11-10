# G1 transport of a heavy crate

A heavy wooden crate stands on the floor near where you start. Bring it into the
green square marked on the floor at the far end of the room, beyond two rows of
shelves, and leave it there at rest and upright for at least 2 seconds. The crate
counts as delivered only while it rests on the wheeled dolly (a low flat transport
cart) that stands in the room, not while it stands on the floor. You may interact
with any object in the room.

The episode ends when you call `finish()`, when the simulated time budget runs
out, or when the robot fails: pelvis below 0.42 m, the body tilted more than 60
degrees from upright, the dolly tipped over, the robot, the crate or the dolly
leaving the room, or a contact force above 800 N on any robot link other than the
feet.

Use the robot-mounted observations and the supplied joint command interface. Your
own code, perception, planning, IK/FK and the provided robot skills may help; they
must execute through that same physical interface. You may not change world or
robot state, attach objects to the robot, alter physical properties, read private
scenario or scoring files, or inject observations or contacts. A private robot model
for planning does not change the simulated world.

Call `info()` for the enabled sensors, actuator limits and episode budgets;
`observe()` reads sensors. Send joint targets with `command()` or
`command_sequence()`, and call `finish()` when done. Development resets are
budgeted; evaluation and grading allow no resets. Credit is given for physical
progress along the task, judged from what happened in the simulator; the
interface does not reveal progress or the score while you run.
