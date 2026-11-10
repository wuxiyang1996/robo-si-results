# H3 — Dual G1 self-closing door delivery

**Category: multi-robot · 2 × G1 + Dex3 · two variants · 180 seconds.** H3 retains its historical identifier; the current implementation is `multi_robot/dual_g1_self_closing_door`, with family ID `H3-cooperative`.

**Published native host reference:** [Release and downloads](https://github.com/wuxiyang1996/robo-si/releases/tag/h3-cooperative-20261024) · [English report](../../infra/task-h3-en.html) · [中文报告](../../infra/task-h3-zh.html).

Both robots start in room A. Deliver the 0.4 kg parcel through the self-closing door, place it on the table in room B, and release it stably. Both variants share the scene, starts, parcel, table, hardware effort limits, 200 Hz physics, 50 Hz shared control and 180-second budget.

| Variant | Available movable objects | Designer-facing reference route | Final frozen cohort |
|---|---|---|---|
| `heavy_prop` | Parcel and a 12 kg crate in B | A opens and holds; B pushes the crate into position; both release the door and crate; B clears the route; A carries the parcel through and places it on the table | **2/2**, 172.44 and 169.24 s |
| `no_prop` | Parcel only | A holds the door continuously while B carries the parcel through and places it on the table | **1/1**, 102.22 s |

The variants are parallel configurations, not three difficulty layers; difficulty is unranked. Neither creates the former wedge or light distractor. Reference-route descriptions above are for reviewers; [task instructions](instruction.md) describe the goal without prescribing a strategy.

Independent trajectory checks confirm full delivery and the corresponding support route. During both final heavy carried crossings, the crate supports the door while both robots have zero door/crate contact. All three final runs have zero inter-robot contact. Cumulative development successes are heavy 3 and no_prop 5 across multiple versions; three earlier no_prop successes retain their original 120-second configuration. These totals are not an all-attempt success rate. Failures are retained.

## Reproduction and release scope

Download the [full packet](https://huggingface.co/datasets/IntelligenceLab/robo-si/resolve/2cf4ebc452aeb859d9003104718c920dd99b0bc9/releases/H3/cooperative-20261024/h3-cooperative-reference-20261024.zip) (750.9 MB), verify its SHA-256 against the release manifest, extract it, and open `index.html` (English) or `index-zh.html` (Chinese). The [compact review packet](https://huggingface.co/datasets/IntelligenceLab/robo-si/resolve/2cf4ebc452aeb859d9003104718c920dd99b0bc9/releases/H3/cooperative-20261024/h3-cooperative-review-20261024.zip) (7.5 MB) contains the linked reports, recordings and evidence, but not the complete runtime or traces. Both include the original Chinese evidence report.

Use the **frozen `reference/runtime`** and environment specification in the full packet for reproduction. The shared controllers in the repository may evolve independently. The packet includes all development attempts, source and asset snapshots, original file seals, contact/state traces, two command streams, videos and independent audits. All 13,786 original sealed files were rechecked. Package relocation on the author's machine passed 27 CPU checks and a 2-second native dual-G1 standing test; this is not another full-task success or second-person reproduction.

This is a privileged-state native host reference. **Formal admission remains false.** An isolated dual-robot agent interface, human sign-off, second-person reproduction and broader coverage remain pending. Historical single-G1 sandbox results do not establish isolation for this task. No human signature is inferred from publication authorization.

The [single-G1 implementation](../../humanoid/g1_self_closing_door/README.md) is retained as historical code and a shared dependency, not a second current H3 task. Its old scenes, 120-second budget and scores remain unchanged in the archived evidence.


<!-- h3-extension-doc:start -->
## H3 扩展任务与实施要求 / Extension plan

[三难度与跨 Embodiment：10 项要求、13 项工作清单](../../infra/planning/h3-extension/README.md) · [English](../../infra/planning/h3-extension/README-en.md)

2026-10-28：设计与实施计划；本次新增物理运行 0。先验收 G1 + Stretch 4 完整见证，再推进工具发现与在线恢复。原双 G1 冻结见证与正式准入状态不变。
<!-- h3-extension-doc:end -->
