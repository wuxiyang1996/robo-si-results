# M1: retrieve the yellow cube

Two robots share this room: a Unitree G1 humanoid with Dex3 hands and a mobile gripper (an ARX X5 arm on a
two-wheeled base). You control both.

A yellow cube (4.5 cm) lies in a plastic crate on a shelf. Bring the cube onto the tray inside the low cabinet and
leave it there, resting on the tray, released by both robots. Before the robots finally let go of the cube,
the cabinet must already support it; throwing it onto the tray does not complete the task.

Rules:
- Use only the robots' own sensors and joint commands (the SDK in this bundle). Nothing else can move objects.
- Do not drop the crate or the cube (no free fall of more than about 0.3 m).
- The episode ends if the G1 falls or the mobile gripper tips over.
- Call finish() when you are done, or declare_infeasible() if you are convinced the task cannot be done.
