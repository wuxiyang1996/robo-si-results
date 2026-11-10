# H3 · Cooperative self-closing door delivery: tasks and requirements

2026-10-30 · In progress · **95** logged attempts · **22** full native task successes · Formal admission **false**.

[实施与六配置证据 / Implementation and six case evidence](implementation.html) · [状态 JSON / Status JSON](implementation.json)

**L2 single-candidate closed-door delivery passed in 413.92 s; autonomous multi-tool discovery remains pending. Fixed repeats: 0/3 completed, 0/3 passed; pilot excluded. L3 support switching passed 3/3 fixed repeats. Recovery-to-parcel delivery after a local fixture passed in 211.48 s; closed-door fault delivery remains pending. Actual fault recovery from a closed-door start without a fixture is also verified; the subsequent support switch failed. Formal admission remains pending.**

[中文](README.md) · [English](README-en.md) · [JSON](task-list.json) · [H3 website](../../task-h3-en.html#h3-extension)

## 1. Goal and first delivery

**Carry the 0.4 kg parcel through the self-closing door, place it on table B and release it stably.**

Given the same goal and physical mechanism, can an agent discover tools, infer its own and its partner’s capabilities, and choose and execute effective cooperation?

**G1 carries the original parcel; Stretch supports the door or places tools. Complete native L1 witnesses exist. L2/L3 extensions proceed separately, as requested, without blocking separate L1 acceptance.**

P0/P1/P2 are implementation priorities; L1/L2/L3 are evaluation levels. Work-item and configuration IDs differ. See the acceptance board for measured evidence, frozen versions and remaining gates.

## 2. Mandatory requirements

### R01 · Separate mechanism and difficulty

**heavy_prop and no_prop are parallel mechanisms. Define L1/L2/L3 by physical constraints, information uncertainty and decision demands.**

### R02 · Keep comparisons matched

**Apply parcel, handle or scene revisions to every paired robot. Merely replacing a robot model does not demonstrate self-modeling.**

### R03 · Verify the full physical process

**Synchronize door angle/velocity, support contacts, parcel and robot states. Check clearance and support from combined-envelope entry until full exit; final contact force is insufficient.**

### R04 · Make capability predictions testable

**Record reach, force or grasp predictions before acting and compare with outcomes; insufficient evidence remains undetermined. Compare fixed roles, probing and no-update controls.**

### R05 · Define information boundaries

**Expose nominal specifications and legal controls; hide actual capability perturbations, tool physics and fault ground truth. Privileged references establish feasibility, not public-sensor agent performance.**

### R06 · Validate before fixing budgets

**Establish feasibility before freezing new budgets; do not automatically reuse 180 seconds. Record and budget probing, communication, execution and recovery costs.**

### R07 · Separate evidence levels

**Retain complete witness / feasibility-screen passed / undetermined / check failed. Separate asset loading, local checks, task success and formal admission; a full expert solution is not required for every seed.**

### R08 · Retain all failures

**Frozen reference counts are not randomized success rates. Do not pool versions or mark unvalidated configurations complete.**

### R09 · Specify the coordination model

**Use centralized control of two robots initially. Independent-agent experiments additionally freeze each agent’s observations, communication permissions, latency and synchronization.**

### R10 · Use physical execution and legitimate faults

**Do not manufacture success with pose resets, hidden attachments or physics edits. L3 permits only predeclared trusted-side faults with raw records.**

## 3. Three evaluation levels

| Level | Question | Acceptance focus |
| --- | --- | --- |
| L1 · Known Coordination | Coordinate with known door mechanics and capabilities | Complete delivery using robot holding or crate support; mapped to the frozen dual-G1 references. |
| L2 · Tool & Role Discovery | Discover tools and assign roles | Measure tool effectiveness, verify support and resolve single-arm resource competition. |
| L3 · Capability-Aware Adaptive Cooperation | Hidden capabilities and online faults | Pre-action predictions, capability updates, role changes and recovery. |

## 4. Implementation checklist

### P0

| ID / status | Task | Mandatory requirement | Acceptance | Dependencies |
| --- | --- | --- | --- | --- |
| P0-1 · Contract recorded; admission pending | Freeze the task and experiment contract | **Specify robots, grippers, scene, parcel, observation permissions and centralized versus independent-agent control; retain the original L1 baseline.** | Versioned specification, public/hidden parameter list and asset inventory. Contract recorded; admission pending; see the acceptance board for individual evidence. | — |
| P0-2 · Navigation and drives measured | Integrate Stretch 4 | **Use pinned, actual Stretch 4 assets, without substituting Stretch 3; verify translation, strafing, rotation, stopping, lift and extension.** | Measured single-robot controls, actuator limits and raw trajectories. Navigation and drives measured; see the acceptance board for individual evidence. | P0-1 |
| P0-3 · G1 carry measured; Stretch grasp unproven | Verify parcel grasp and release | **Physically grasp, transport and release the 20 × 18 × 16 cm, 0.4 kg parcel; rated payload alone does not establish graspability.** | Stable manipulation witness; any parcel revision is shared by every paired embodiment. G1 carry measured; Stretch grasp unproven; see the acceptance board for individual evidence. | P0-2 |
| P0-4 · Shared heterogeneous interface implemented | Implement embodiment adapters | **Configure action dimensions, drives, grasp contacts, collision envelopes and stability checks per embodiment; do not apply the G1 root-height fall threshold to a wheeled robot.** | G1 and Stretch operate on a shared clock through bounded actuators. Shared heterogeneous interface implemented; see the acceptance board for individual evidence. | P0-1, P0-2 |
| P0-5 · Continuous scoring implemented; isolation pending | Extend scoring and the sandbox | **Support single-arm grasping, evaluate the entire crossing interval, and prevent hidden actual parameters leaking through metadata or privileged reference interfaces.** | Scoring and isolation checks, synchronized records and independent replay; preserve the legacy scorer. Continuous scoring implemented; isolation pending; see the acceptance board for individual evidence. | P0-4 |
| P0-6 · Complete L1 witnesses; admission pending | Complete the heterogeneous baseline | **Use the user-confirmed route: G1 carries the original parcel and Stretch supports the door or places tools. Verify real contact throughout, without runtime pose resets or hidden attachment.** | At least one complete delivery witness and independent audit; the reference does not prescribe the agent’s role allocation. Complete L1 witnesses; admission pending; see the acceptance board for individual evidence. | P0-3, P0-5 |

### P1

| ID / status | Task | Mandatory requirement | Acceptance | Dependencies |
| --- | --- | --- | --- | --- |
| P1-1 · Local tool screening and placement measured | Introduce candidate tools | **Start with a physical wedge, heavy crate and one distractor; check support after assistance is removed and passage occupancy; defer the brace rod.** | Verified tool collision geometry, stability, slip and passage clearance. Local tool screening and placement measured; see the acceptance board for individual evidence. | P0-6 |
| P1-2 · Local physical counterfactuals measured | Build counterfactual tool pairs | **Keep appearance and geometry matched, changing only the specified friction or closer parameter; account for contact-material combination and measure the resulting difference.** | The same placement produces reproducible stable/failing outcomes, with evidence for a feasible route. Local physical counterfactuals measured; see the acceptance board for individual evidence. | P1-1 |
| P1-3 · Single-candidate delivery passed; autonomous choice pending | Discover tools and allocate roles | **Do not label effective tools; predict, probe and verify affordances through feedback; include instances where a tool is necessary or has a defined cost benefit.** | Traces of probing, selection, withdrawal checks, support handoff and role reassignment. Closed-door delivery passed in 413.92 s with an independent audit; three fixed repeats are running. Autonomous multi-tool choice remains missing. | P1-2 |
| P1-4 · Planned | Run capability pairs and ablations | **Compare dual G1 and G1 + Stretch 4 in matched scenes with matched sensing, interfaces and budgets; record capability predictions before actions.** | Fixed-role, active-probing and no-probe/no-update controls; distinguish role adaptation from path-planning gains. | P0-6, P1-3 |

### P2

| ID / status | Task | Mandatory requirement | Acceptance | Dependencies |
| --- | --- | --- | --- | --- |
| P2-1 · Trusted faults implemented and audited | Implement trusted fault events | **Predeclare fault triggers, magnitude and allowed changes; execute and record on the trusted side, separately from unauthorized physics changes.** | Replayable events; legitimate faults are not misclassified as VOID and unauthorized changes remain rejected. Trusted faults implemented and audited; see the acceptance board for individual evidence. | P0-5 |
| P2-2 · Local recovery measured; full delivery pending | Verify online recovery | **Introduce one fault type at a time, first establish recoverability, and record capability updates and role changes.** | Complete fault-to-delivery traces, recovery success and additional cost. Local recovery measured; full delivery pending; see the acceptance board for individual evidence. | P1-4, P2-1 |
| P2-3 · Planned | Expand robot pairings | **Validate individual capabilities and scene feasibility before dual Stretch 4 or G1 + Go2/Z1 tasks; retain A3 as a later candidate.** | Separate evidence and budget for each pairing; no transfer of success claims between embodiments. | P0-6 |

## 5. Six evaluation configurations

| Configuration | Robots | Level | Mechanism | Evidence | Budget |
| --- | --- | --- | --- | --- | --- |
| H3-01 | G1 + G1 | L1 | `no_prop` | Complete witness: frozen 1/1, 102.22 s | 180 s |
| H3-02 | G1 + G1 | L1 | `heavy_prop` | Complete witnesses: frozen 2/2, 172.44 / 169.24 s | 180 s |
| H3-03 | G1 + Stretch 4 | L2 | `tool_discovery` | Single-candidate closed-door native delivery passed in 413.92 s with independent audit; fixed repeats are pending. Autonomous multi-tool discovery remains incomplete. | Freeze after physical validation |
| H3-04 | Stretch 4 + Stretch 4 | L2 | `single_arm_resource_allocation` | Dual Stretch has no independently verified implementation; mixed-pair results do not transfer. | Freeze after physical validation |
| H3-05 | G1 + Stretch 4 | L3 | `hidden_capability_and_recovery` | Local support switching passed 3/3 fixed repeats; local recovery-to-delivery passed in 211.48 s. Closed-door actual fault recovery is now verified, but the later switch failed; an angle-reserve revision is being tested. | Freeze after physical validation |
| H3-06 | G1 + Go2/Z1 | L3 | `heterogeneous_contact_and_reallocation` | Composite asset preflight incomplete; no physics run. | Freeze after physical validation |

H3-01/02 map the existing frozen variants and add no task successes. H3-03 through H3-06 are new designs with no completion claim. G1 + A3 remains a later candidate outside these six configurations.

## 6. Diagnostics and event traces

| Metric | Definition and recording |
| --- | --- |
| Tool Discovery Success | Whether the selected tool maintains support after assistance is removed and permits actual passage; continuous robot holding is recorded separately. |
| Capability Prediction Accuracy | Agreement between pre-action predictions and outcomes, including confidence and undetermined cases; post-hoc explanation is not a prediction. |
| Role Allocation Quality | Feasible roles, failed reassignments and cost against a matched reference; do not claim optimality without a cost definition. |
| Support Continuity | Minimum clearance, unsupported duration, support source and handoff events throughout crossing; freeze thresholds after physical validation. |
| Recovery Success | Restore safe support and complete delivery under predeclared recoverable faults; report unrecoverable cases separately. |
| Probe / Execution Cost | Probe actions, simulation time, observation/communication counts and robot occupancy; separate additional recovery cost. |

Use the existing 200 Hz physics trace as a starting point. Align raw state, commands, support sources, crossing intervals, fault events and scorer versions for independent review. Local gates are recorded in each frozen plan and audit; full evaluation budgets for new configurations remain pending.

## 7. Existing foundations and implementation changes

Historical frozen dual-G1 witnesses: heavy_prop 2/2 and no_prop 1/1. A dual-robot sandbox adapter exists; isolated expert execution, independent reproduction and formal admission remain pending. Stretch 4 has measured navigation, tool placement and local recovery evidence. The current acceptance board records full-task results and remaining L2/L3 gates.

| Module | Observed limitation / required change |
| --- | --- |
| `multi_robot/dual_g1_self_closing_door/task_spec.py` | Fixed dual G1 and two inventories; explicitly define embodiments, tools and hidden parameters in the new version. |
| `genesis_env.py` | Fixed robots and joint parameters; non-parcel objects use Box geometry; introduce real wedge collisions and per-embodiment stability checks. |
| `scoring.py` | The bilateral-hand contact rule does not apply to a single arm; extend parcel-center crossing to the full combined-envelope passage interval. |
| `guard.py` / `reference.py` | Peer envelopes and control assume G1; privileged mass/friction access is for reference feasibility only. |
| `infra/sandbox/native_reference.py` | Currently 43 position targets per robot; adapt heterogeneous drives, per-robot parameters and trusted fault replay. |

The heterogeneous implementation is in `multi_robot/cooperative_door/`, including the shared clock, bounded drives, tool probes, recovery controls and independent audits. Frozen runtimes and failed trials are retained.

## 8. Sources and evidence boundaries

- [H3 reference README](../../../multi_robot/dual_g1_self_closing_door/README.md)
- [H3 sandbox README](../../../multi_robot/dual_g1_self_closing_door/sandbox/README.md)
- [Sandbox validation ledger](../../sandbox-delivery/validation.json)
- [Stretch 4 passive import result](../h1-extension/asset-smoke-evidence/8035305_1/result.json)
- [Official Stretch 4 specifications](https://hello-robot.com/stretch-4/)

Official payload ratings are 2.5 kg extended and 4 kg retracted; they guide asset review but do not replace grasp, push or transport measurements for the selected model. This update implements drivers and prerequisite probes; measured runs are listed in the implementation dashboard. Historical success counts and formal admission remain unchanged.
