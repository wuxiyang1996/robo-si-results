# robo-si: accepted embodied tasks

Website: https://wuxiyang1996.github.io/robo-si-results/

This repository hosts the public results site of **robo-si**, a robotics benchmark for self-modeling, tool
discovery, loaded locomotion and multi-robot cooperation. The site lists the tasks and task families that the
author has accepted, as of the acceptance snapshot of 2026-11-02. For every accepted configuration it gives:

- an 8x-speed video of the reference run (clips shorter than 20 s play at 4x, 2x or 1x; the badge shows the
  speed),
- conditions, task design, tools and embodiment,
- whether the correct behaviour is refusal: the task is infeasible, so the robot should exit empty-handed into
  the exit zone and stand still.

Scope notes:

- "Accepted" means the author signed off the reference-delivery scope. It is not formal benchmark admission and
  not independent second-person reproduction.
- Videos are continuous runs of privileged-state reference experts in physics simulation (Genesis / MuJoCo).
  They show feasibility, or that exiting is correct. They are not results of a learned agent.
- Families still in development are listed on the home page without videos.

The site is static HTML (`index.html`, one page per family). `data/accepted-tasks.json` holds the same task data
in machine-readable form. Source code, simulators and full evidence live in the private robo-si repository and
dataset.
