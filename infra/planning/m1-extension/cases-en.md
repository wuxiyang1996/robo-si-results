# M1: 9 capability-boundary and tool-use cases

**One original task + 6 extension operations + 2 infeasibility controls: 9 total.** The original task has scoped historical witnesses and retains its configuration and scorer. Extensions remain unknown; zero new simulations. Parent groups and Cartesian model/rule/tool combinations are not counted.

| Case ID | Capability boundary | Scene and complete goal | Tools / partner | Status |
| --- | --- | --- | --- | --- |
| M1C-ORIG | Original M1: crate lowering, target retrieval and cabinet delivery | Original G1 + Dex3 lowers the crate to the transfer stand; X5 retrieves the block and places it deep in the low cabinet with support before release. Retain original v0.3 / V4 configuration, scorer and budget: 13 complete successes, eight physical seeds and 3/3 strict repeats; no new simulation. | Crate, original transfer stand, G1 + X5 | Witnessed in original scope |
| M1C-B01 | Crate cannot be lifted, but can be repositioned by pushing | Current grasp/carry limits block crate lifting and its initial position obstructs picking; controlled pushing and environmental support may establish retrieval access before cabinet delivery. | Crate and support surfaces | unknown |
| M1C-B02 | Held crate blocks safe picking; independent support needed | Provide supports with different top areas, capacities and handling geometry; determine which can independently support the released crate through retrieval and cabinet delivery. | Stands, boxes and work surfaces | unknown |
| M1C-B03 | Direct grasp falls short; an operable tool extends retrieval | Target in a fixed crate is beyond direct grasp; hooks, extended grippers, rods and short tools coexist. Check grasp, useful force and withdrawal, then complete cabinet delivery. | Hook, extended gripper, rod, short tool | unknown |
| M1C-B04 | Useful tool is inoperable by self but operable by partner | Keep target and tool working-end conditions; current hand is limited by handle, actuation or wrist moment, while a partner may operate the tool. Change operator or use another legal tool to deliver; no forced initial failure. | Tools with different body compatibility and a partner | unknown |
| M1C-B05 | Hand cannot enter the cabinet; a tool may deliver | Target fits the cabinet entrance but current hand envelope/reach prevents deep placement; choose a pusher or carrier with continuous support and complete tool withdrawal. | Narrow pusher, thin/thick carriers | unknown |
| M1C-B06 | Own tool cannot complete withdrawal; change deliverer | Target can enter, but the current body/tool combination cannot complete support transfer and withdrawal; a lower or smaller-hand partner is a candidate alternative. Insertion with retained tool support is not success. | Transfer surface, low-level operator and delivery tools | unknown |
| M1C-I01 | No body or available tool completes retrieval | Exclude all body poses, crate movement, alternative approaches, tool combinations and cooperation; only an all-route certificate establishes correct abstention. | All available tools and participants | unknown |
| M1C-I02 | Target itself cannot pass the cabinet entrance | The intact rigid target and sole entrance form the bottleneck, not hand width; exclude alternative openings, disassembly and deformation, then verify physical exit. | All delivery tools and participants | unknown |

Original-task evidence: [JSON](/infra/m1-current-evidence.json). New capability, Y/N, Q-exit and 2 kg screening rules below apply to extension designs, not retroactively to the original task. Historical witnesses do not validate extensions.

**Body/tool compatibility:** bind embodiments to explicit boundaries through asset and capability probes. Add a case only when body changes create a materially different feasible-route set or tool-operation problem; model-name swaps do not add cases. Test grasp, actuation, useful force, moments, transfer, withdrawal and final delivery, not merely tool pickup. Differences must be observable, never inferred from brands or appearance.

| Candidate profile | Embodiment |
| --- | --- |
| A | G1 + Dex3 + X5 |
| B | G1 + five-finger hand + same X5 |
| C | Wheeled dual-arm + low-level manipulator |

Y/N remain separately reported public-rule versions within each case: N permits help; Y requires designated-manipulator receipt and final delivery. Pairs change only rules, holding world, bodies, tools and sensors fixed. Direct/help records actual routes, never hidden prescribed solutions. Multiple routes, tool mismatch and recovery belong to concrete scenes; do not force an initial mistake. Cart 04, I02/I04 and D remain deferred.

**Implementation and scoring:** audit body/tool interfaces and complete routes before freezing parameters and priorities. Complete retrieval, required transfer, return/delivery and support release; accept all legal goal-satisfying solutions. Infeasibility requires all-route exclusion and all robots physically in Q, empty-handed and independently stable for 3 seconds. A failed route is insufficient. Seeds are instances, not cases. The 2 kg external-load screen remains provisional; component, pose and dynamic scope need verification.
