# M3: 6 capability-boundary and tool-use cases

**One original task + 4 extension operations + 1 infeasibility controls: 6 total.** The original task has scoped historical witnesses and retains its configuration and scorer. Extensions remain unknown; zero new simulations. Parent groups and Cartesian model/rule/tool combinations are not counted.

| Case ID | Capability boundary | Scene and complete goal | Tools / partner | Status |
| --- | --- | --- | --- | --- |
| M3C-ORIG | Original M3: lift X5, supported retrieval, lowering and delivery | Original G1 lifts X5 for box-supported retrieval of the 65 mm ball, then lowers X5 for ground-tray delivery. Preserve hooks-v0.1, original scorer and 420-second budget: 2/2 normal-start successes, 411.16 seconds each, same-parameter repeats. This does not establish the new 2 kg compatibility. | Original support box, carrying interfaces, G1 + X5 | Witnessed in original scope |
| M3C-B01 | Lift candidate, but manipulation requires independent platform support | Prepared platform; complete lifting/lowering capability remains unverified and suspended manipulation is not assumed. Retrieve with independent platform support, then lower, release support and deliver. | Prepared platform and partner support interfaces | unknown |
| M3C-B02 | Existing supports are unsuitable; select and establish a workstation | Provide candidate supports varying in height, footprint and rating; assess partner support, extended-arm operation and safe return; establish a suitable workstation and complete retrieval/delivery. | Multiple support objects | unknown |
| M3C-B03 | Lifting is unsafe; a ramp is a candidate alternative | Keep cabinet, tools and partner; carrying capability is insufficient. Assess partner mobility, traction and ramp geometry for ascent and loaded return. Rejected lifting alone does not justify abstention. | Ramp, platform and partner mobility | unknown |
| M3C-B04 | Partner cannot use ramp; lifting is a candidate alternative | Retain B03 scene structure; partner chassis or drive capability prevents ramp use. Assess carrier lift, supported retrieval and lowering; lifting still requires the 2 kg and dynamic capability audit. | Carrying interfaces, platform and ramp | unknown |
| M3C-I01 | Lifting and every alternative route are infeasible | Carrying is unsuitable and direct retrieval, ramps, other supports, tools and combined routes are excluded; safely settle all participants independently before Q exit. | All available tools and participants | unknown |

Original-task evidence: [JSON](/infra/m3-current-evidence.json). New capability, Y/N, Q-exit and 2 kg screening rules below apply to extension designs, not retroactively to the original task. Historical witnesses do not validate extensions.

**Body/tool compatibility:** bind embodiments to explicit boundaries through asset and capability probes. Add a case only when body changes create a materially different feasible-route set or tool-operation problem; model-name swaps do not add cases. Test grasp, actuation, useful force, moments, transfer, withdrawal and final delivery, not merely tool pickup. Differences must be observable, never inferred from brands or appearance.

| Candidate profile | Embodiment |
| --- | --- |
| G | G1 + X5 |
| H | Other dual-arm humanoid + same X5 |
| W | Wheeled dual-arm + same X5 |

X5 is an unaudited partner candidate; compatibility with the current 2 kg condition is unknown. Do not rescale mass or silently substitute a lightweight robot. Rebind assets and capabilities for a partner change, adding a case only for a new bottleneck. Lift/ramp labels are unverified hypotheses, not prescribed solutions. Humanoid carrying and standalone return-posture tasks remain withdrawn.

**Implementation and scoring:** audit body/tool interfaces and complete routes before freezing parameters and priorities. Complete retrieval, required transfer, return/delivery and support release; accept all legal goal-satisfying solutions. Infeasibility requires all-route exclusion and all robots physically in Q, empty-handed and independently stable for 3 seconds. A failed route is insufficient. Seeds are instances, not cases. The 2 kg external-load screen remains provisional; component, pose and dynamic scope need verification.
