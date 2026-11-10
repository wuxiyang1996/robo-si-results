# G1 transport of a heavy crate

A heavy wooden crate (65 kg) stands near where you start. Bring it into the green square
marked on the floor at the far end of the room and leave it there upright and at rest for
at least 2 seconds, with its weight carried by the floor or by objects that rest on the
floor. Moving the crate counts only while its whole weight rests on other objects: none of
it on the floor and none of it held up by the robot. A delivery counts only after the
crate has rested on such objects by itself, without the robot touching it or them. You may
interact with any object in the room.

The episode ends when you call `finish()`, when the simulated time budget runs out, or
when the robot fails: pelvis below 0.42 m, the body tilted more than 60 degrees from
upright, the crate tilted more than 60 degrees, the robot or the crate leaving the room,
or a contact force above 800 N on any robot link other than the feet.

Use the robot-mounted observations and the supplied joint command interface (joint
position targets with gains, or motor torques, within the robot's limits; see
`info()["robot"]`). Your own code, perception, planning, IK/FK and the provided robot
skills may help; they must execute through that same physical interface. You may not
change world or robot state, attach objects to the robot, alter physical properties, read
private scenario or scoring files, or inject observations or contacts. A private robot
model for planning does not change the simulated world.

Call `info()` for the enabled sensors, actuator limits and episode budgets; `observe()`
reads sensors. Send joint targets with `command()` or `command_sequence()`, and call
`finish()` when done. Development resets are budgeted; evaluation and grading allow no
resets. Credit is given for physical progress along the task, judged from what happened
in the simulator; the interface does not reveal progress or the score while you run.
