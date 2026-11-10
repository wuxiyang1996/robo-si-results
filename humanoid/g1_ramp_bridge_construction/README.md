# H4 — Ramp / bridge construction

**项目状态：已完成。** 用户于 2026-10-24 确认按已发布的第一层参考范围结项（11/14 成功，保留并接受 3 个失败案例）。下述验证与准入待办作为后续事项保留，不阻塞本范围的完成标记。

The author-approved [first-layer reference release](https://github.com/wuxiyang1996/robo-si/releases/tag/h4-layer1-20261024) contains **11/14
successful first-layer runs**, including all three failures. The existing
layer-2 and layer-3 recordings are retained as a historical appendix (4/4 each;
19/22 overall). [中文](../../infra/task-h4-zh.html) · [English](../../infra/task-h4-en.html).

One G1 builds a bridge over a floor gap, crosses it, picks up the handled box,
carries it back and places it in the goal. The recorded scene is v4.2. A successful
reference is privileged with respect to observations and stays within the
declared hardware limits; it is not an agent benchmark result.

The package contains original videos, sealed logs, positive/negative/exploit
checks, source hashes, a publication-time source snapshot and unsigned review
forms. The snapshot includes later shared-runtime maintenance; exact historical
source differences are listed in `source-provenance.json`. It is not a claim
of second-person or exact-environment reproduction.

This is a reference-material prerelease, with `admitted=false`. Independent
subtask starts, targeted boundary coverage, same-seed repeat coverage, route/tool
necessity audits, itemized human labels and second-person reproduction remain
pending. R9 and additional difficulty layers are deferred for this publication.

Current environment and interface details are in [task_card.md](task_card.md),
[scene.py](scene.py), [sandbox/README.md](sandbox/README.md) and
[solution/README.md](solution/README.md). Publication does not change physics,
scoring or the existing admission record.
