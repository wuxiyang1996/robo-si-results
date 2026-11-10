# H4 reference controller

The current scene is v4.2: build a bridge by pushing the long plank past vertical,
cross the gap, retrieve the handled box, return and place it in the goal.

The [2026-10-24 reference release](https://github.com/wuxiyang1996/robo-si/releases/tag/h4-layer1-20261024)
preserves **11/14 first-layer full runs**, including all three bridge-building
failures. Historical layers 2 and 3 each passed 4/4 and remain an appendix.
All 19 episodes that built the bridge completed retrieval and delivery.
[中文 review](../../../infra/task-h4-zh.html) · [English review](../../../infra/task-h4-en.html).

`run_oracle.py` implements the privileged reference controller. `env.py` provides
the environment adapter; the physical manipulation modules remain part of that
controller. `shove.py` and `pickup.py` are also dependencies of other tasks.
`audit.py`, `contact_sheet.py` and `feasibility.py` remain supporting analysis tools.
The old stop-motion probe and legacy preview evaluator have been retired.

Use the trusted recorder from a configured repository checkout for a new physical
reference run. This command is an entry point, not a claim that the publication
snapshot independently reproduces the historical result:

```powershell
python -B -m humanoid.g1_ramp_bridge_construction.sandbox.trusted.record_reference --seed 101 --layer 1 --out humanoid/g1_ramp_bridge_construction/sandbox/runs/reference/new-L1-s101
```

The output directory must be new. The recorder emits sealed state logs, the
original video, source hashes and the verifier verdict under the task's hardware
limits. Read [sandbox instructions](../sandbox/README.md) for setup and scoring.

The release is reference material with `admitted=false`. Independent subtask
starts, boundary and same-seed repeat coverage, tool/shortcut audits, human
signatures and second-person reproduction remain pending. R9 is deferred.
The release source audit records differences between the historical runtime
hashes and the publication-time snapshot; exact historical reconstruction is
not certified.

Superseded development narratives are removed from the active documentation.
The immutable offline release preserves the original solution README and evidence;
the cleanup record documents the retirement of unreferenced development runs.
