# M3: get the red ball

Two robots share this room: a Unitree G1 humanoid with Dex3 hands and a small wheeled robot with an arm and a gripper
(an ARX X5 arm on a two-wheeled base). You control both.

A red ball lies in a container on a shelf. Put the ball into the green tray on the floor and leave it resting
there, released by both robots.

Rules:
- Use only the robots' own sensors and joint commands (the SDK in this bundle). Nothing else can move objects.
- Do not drop the ball (no free fall of more than about 0.3 m).
- The episode ends if the G1 falls or the wheeled robot tips over.
- Call finish() when you are done, or declare_infeasible() if you are convinced the task cannot be done.
