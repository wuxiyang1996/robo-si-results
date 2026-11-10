# H5 — Lever-assisted heavy-object transport

**项目状态：已完成。** 用户于 2026-10-24 确认按已发布的 100 kg 第一层参考范围结项（全程 5/5、独立子任务 20/20、同种子重复 3/3）。下述整合、验证与准入待办作为后续事项保留，不阻塞本范围的完成标记。

The author-approved [layer 1 reference release](https://github.com/wuxiyang1996/robo-si/releases/tag/h5-layer1-20261023) contains the
100 kg `lever-insertion-v3` / `transport36` cohort: **5/5 full runs**, **20/20
independently started subtasks**, and **3/3 same-seed repeats**.
[中文 review page](file:///C:/Users/wuxiy/rsi_releases/h5_release_artifact_20261023/workspace/infra/task-h5-zh.html) · [English review page](file:///C:/Users/wuxiy/rsi_releases/h5_release_artifact_20261023/workspace/infra/task-h5-en.html).

One G1 moves a heavy cargo box into the goal region and leaves it upright, still
and supported for two seconds. The released reference uses a platform lever,
fulcrum and two wheeled skates. Strategy details belong to the reference and
review material; agent instructions state the goal and constraints.

## Release scope

The five scenes cover seeds 23, 47 and 71 plus two boundary configurations.
The four independently started subtasks per scene are edge lift, independent
support, transport and delivery. Full-run success and subtask success are
reported separately. Original recordings, sealed logs, new camera views,
source hashes and review templates are in the offline packet linked above.

This is a reference-material prerelease, with `admitted=false`. Itemized human
sign-off, second-person reproduction, broader tool-necessity review and
integration of the 100 kg candidate with the canonical 65 kg entry remain
pending. R9 and layers 2/3 are deferred by the author.

## Source and reproduction

- `task_spec.py`, `assets.py`, `robot.py` and the simulator adapters define the
  environment. The existing variants remain available for compatibility.
- [solution/](solution/README.md) contains the retained platform controller,
  recording utilities and shared kinematics compatibility interface.
- The complete sandbox, verifier, release configuration and frozen sources for
  the published cohort are included in the offline packet. Follow its
  `acceptance/release-layer1-20261023/reproduce_layer1.py` preflight before
  executing a reproduction in a new output directory.

Reproduce the published results from the frozen packet. The current checkout
may contain later maintenance changes and does not replace that source snapshot.

## Maintenance

Superseded pickup/planning probes, the old skate development and chain runners,
experimental indexes, smoke media and local `solution/runs` history have been
removed from the active tree. The former development documentation is available
in [Git history](https://github.com/wuxiyang1996/robo-si/tree/5089a845a1168259a37a875a778c777a0dd131bf/humanoid/g1_lever_assisted_transport); uncommitted local run data was archived outside the
repository before cleanup. Released evidence, counterexamples and sandbox runs
referenced by the admission record or consistency checks are retained.

The cleanup changes no physics, scoring or admission verdict and does not
constitute a new physical validation run.
