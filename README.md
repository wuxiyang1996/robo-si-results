# robo-si: accepted embodied tasks

Website: https://wuxiyang1996.github.io/robo-si-results/

This repository hosts the public results site of **robo-si**, a robotics benchmark for self-modeling, tool
discovery, loaded locomotion and multi-robot cooperation. The site lists the tasks and task families that the
author has accepted, as of the acceptance snapshot of 2026-11-04: 22 families and 219 configurations,
with 207 public configuration videos and evidence backed up for all 219. For every accepted configuration it gives:

- an available reference video, with its speed shown in the badge (earlier short clips may use 4x, 2x or 1x),
- conditions, task design, tools and embodiment,
- whether the correct behaviour is refusal: the task is infeasible, so the robot should exit empty-handed into
  the exit zone and stand still.

Scope notes:

- "Accepted" means the author signed off the reference-delivery scope. It is not formal benchmark admission and
  not independent second-person reproduction.
- Videos show privileged-state reference experts in physics simulation (Genesis / MuJoCo).
  They show feasibility, or that exiting is correct. They are not results of a learned agent.
- The SC/PC release adds 10 cooking successes and 2 correct-exit controls. Its 12 videos and compilation
  use a common camera at 960×720, 24 fps and 8x speed. These are presentation renders of recorded measured
  trajectories; original same-run videos and independent physical replays are retained in the evidence archive.
  SC-05 barriers and the PC-I01 room and partition are transparent only in the presentation render.
  Individual clips also offer playback at 4x or the original time scale.
- Complete SC/PC evidence is backed up in the private Hugging Face dataset `IntelligenceLab/robo-si`,
  release `cooking-sc-pc-acceptance-20261104-v1`, pinned to commit
  `f35de6f630ab31f3b43931546bab767aa0069e0b`. All 50 release files were verified by size and SHA-256.
  The full evidence links require dataset access; public videos are hosted in this repository.
- Families still in development are listed on the home page without videos.

The site is static HTML (`index.html`, one page per family). `data/accepted-tasks.json` holds the same task data
in machine-readable form. Source code, simulators and full evidence live in the private robo-si repository and
dataset.

GEAR was accepted on 2026-11-04: 7 records across 3 independent task designs, with 3 historical references
and 4 formal-body configurations shown separately. The GEAR page includes 8x previews, full 1x downloads,
a matched-world G/F comparison, the author acceptance record, and a private full-evidence archive link.

ASM / JNG was signed off on 2026-11-04: 4 ASM and 15 JNG successes. ASM-04.S and JNG-06.B remain incomplete diagnostics and are excluded from accepted counts. Videos are unified-angle measured-state presentation renders at 8x, with original recordings linked separately; this does not change the physical results. Full evidence, sources and models are privately backed up with a pinned recovery index.

M4 contains six accepted preconnected towing references using ground-supported cargo.

H4 was accepted on 2026-11-04 within its existing reference-delivery scope: 9 bridge constructions, 1 direct crossing and 7 explicit-refusal cases (17 total). Seven same-body feasible controls are shown separately and are not extra tasks. All seven new pairs meet 240 seconds; five historical retrieval references retain declared budget exceptions. Original recordings, source, models and development failures are privately archived with a pinned recovery index.
