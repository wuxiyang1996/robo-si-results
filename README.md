# robo-si: accepted embodied tasks

Website: https://wuxiyang1996.github.io/robo-si-results/

This repository hosts the public results site of **robo-si**, a robotics benchmark for self-modeling, tool
discovery, loaded locomotion and multi-robot cooperation. The site lists the tasks and task families that the
author has accepted, as of the acceptance snapshot of 2026-11-04: 30 families and 251 configurations,
with 237 public configuration videos and evidence backed up for 247 of 251 (archive verification pending: F3, F4). For every accepted configuration it gives:

- an available reference video, with its speed shown in the badge (earlier short clips may use 4x, 2x or 1x),
- conditions, task design, tools and embodiment,
- whether the correct behaviour is refusal: the task is infeasible, so the robot should exit empty-handed into
  the exit zone and stand still.

Scope notes:

- "Accepted" means the author signed off the reference-delivery scope. It is not formal benchmark admission and
  not independent second-person reproduction.
- Videos show privileged-state reference experts in physics simulation (Genesis / MuJoCo).
  Their labels distinguish complete feasibility, correct exits and incomplete research snapshots. They are not results of a learned agent.
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

F5/F6/F7 were accepted on 2026-11-04: 6 transport/installation, 6 routing/reel and 5 fastening/recovery configurations (17 total). Eight have this-round declared revisions; all retain their specific scope. The 17 public videos use a common camera direction and 8x physical-time speed at 1280x720/24 fps. Full raw records, source, models, presentation provenance and development history are privately backed up with a pinned restore index.

F2 (garment tidying and packing) was added on 2026-11-04 with 1 of 6 declared configurations accepted: F2-01-L1, one continuous native dual-Stretch 3 run with a free 2D towel and a passive flip board (29,751 physics steps, 9 low-level actions, zero action-replay error, matching static negative control). The other five configurations are not accepted and are listed on the F2 page with their measured status at the 2026-11-04 15:39 pause. The public clip is an 8x kinematic re-render with the F5/F6/F7 camera contract; new F2 runs use the task_outcome_v1 precision profile while the accepted L1 record keeps the legacy profile.

M1 was author-accepted on 2026-11-04: seven independently reviewed frozen configurations (four complete deliveries and three certified safe exits). B03 remains paused incomplete; B04/B05 are deferred. Six same-run original recordings are shown at 8x and offered at 1x; I01 has no original recording. Remote M1 backup verification passed. No full eight-configuration completion or capability-boundary certification is claimed.

MTC update 2026-11-04: 3 author-accepted scopes; L1/L2 have complete independently verified experts, while L3 reconfiguration and second retrieval remain incomplete and development is paused. All working evidence is backed up at https://huggingface.co/datasets/IntelligenceLab/robo-si/tree/e00a254d78fe1d6c422e9cc03cde92128aa2a452/releases/mtc-pause-backup-20261104-v1. The 3 public MTC videos include one explicitly labelled partial run.

F3/F4: the author accepted four paused research-delivery representatives on 2026-11-04. This is author-designated acceptance, separate from measured original-task success. Only F4-01-L1 has the full original goal independently verified: three fresh expert runs and one independent action replay. Strict numeric reproduction failed; the complete 100 s no-op physics audit was interrupted and remains pending. The jacket, apron and irregular-cover original goals remain incomplete. Historical incomplete videos and the measured R30 contact window are explicitly labelled. Fixed-pelvis evidence does not establish free walking or other difficulty levels.
