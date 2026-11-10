# M2 · Cooperative long-object transport: six core configurations

Version: 2026-10-28 · Design specification. M2 remains one task family with six configurations, using two robot types (G1 and Stretch) in three teams: two G1s, G1 + Stretch, and three G1s. Difficulty levels, tools and observation conditions do not multiply the task count.

**Evidence scope.** M2-1 corresponds to the published fixed L1 reference: 0.25 kg, 1.8 m corridor, three successful privileged references (09/10/11) and ordinary open-loop replay 09d, all in the same scene and seed. Independent reproduction and formal admission remain pending. M2-2–6 are proposed configurations without full physical witnesses for their specified conditions. This paragraph describes the evidence available at design registration. Implementation has now started; see the [implementation record](m2-implementation.md) and [task progress page](../infra/task-m2-en.html#m2-implementation) for new outcomes, failures and videos. New runs do not rewrite the historical L1 record.

[中文](m2-task-family.md) · [M2 website and historical evidence](../infra/task-m2-en.html) · [Frozen baseline record](../infra/m2-current-evidence.json)

## 1. Configuration register

| ID | Task | Team | Research question | Status |
| --- | --- | --- | --- | --- |
| M2-1 | Light box through an L corridor | Two G1s | Coordinated grasp, carry and release | Existing fixed L1 reference |
| M2-2 | Same light scene with a different partner | G1 + Stretch | Body adaptation and role allocation | Unvalidated |
| M2-3 | Heavier box through the same corridor | Two G1s | Load limits and stable shared transport | Load screening pending |
| M2-4 | Same heavy scene with a different partner | G1 + Stretch | Capability estimation and mechanism choice | Unvalidated |
| M2-5 | Heavy transport with a movable obstruction | Two G1s | Clearing, temporary placement and sequencing | Unvalidated |
| M2-6 | Same obstructed scene with a third robot | Three G1s | Useful division of work versus coordination costs | Unvalidated |

L1 is the frozen M2-1 baseline. L2 denotes adaptation to known constraints; L3 denotes discovery under partially unknown capabilities or object properties. These are experimental conditions, not additional task IDs or a claim that larger teams are harder.

## 2. Shared scene and rules

**Goal.** Move the designated long box through a 90-degree L corridor, place the entire box in the target region, transfer support and release it, and finish with every robot stable. The instruction does not prescribe tools, grasp points or roles.

**Matched scenes.** The reference box is 2.25 × 0.35 × 0.24 m, the light mass is 0.25 kg, and the reference corridor is 1.8 m wide. M2-2 preserves the M2-1 box, corridor and goal; only necessary, documented initial stance adjustments accommodate the different body. M2-3/4 share the same heavy mass, center of mass, dimensions, floor, corridor, goal and tool conditions. M2-5 adds one movable obstruction and a legal storage region to M2-3. M2-6 preserves every M2-5 object state and the original two robot poses, adding one G1 at a noninterfering start.

**Heavy mass.** Screen 0.25, 0.5, 1 and 2 kg progressively before considering 3–4 kg. The admitted heavy value m_H remains unset until validation. Nine kilograms is not a required target. The historical failed 2 kg support-start trial establishes failure for that controller and configuration, not an absolute hardware limit.

**Embodiments.** Keep the L1 G1 assets, Dex3 hands and controllers where applicable. Select one specific Stretch 3 or Stretch 4 model, end effector and controller before binding the new tasks; a Stretch 3 asset does not validate Stretch 4. The third G1 uses the same version as its partners. Record model/controller identities, friction, actuator limits and sensor configuration.

**Tools and initial state.** Use one transport tool set: a low roller dolly and necessary connectors. M2-1 remains unchanged; M2-2's primary comparison adds no tools. Tool-enabled M2-3/4/5/6 use the same inventory and placement. Cargo starts on the floor, separate from the dolly; connectors are initially disengaged. Loading, docking, towing, turning, braking, unloading and detachment must be physically executable. Remote attachment is disallowed. Preloaded or preconnected tests are skill diagnostics, not full task witnesses.

**Final state.** For these core configurations, cargo must be stably supported directly on the target floor, with robots and transport connectors detached. Cargo remaining on the dolly demonstrates transport progress, not complete delivery. Tools need not return to their initial locations, but must be stable and not trap cargo or prevent safe completion.

**Permitted behavior.** Legal grasping, pushing, pulling, temporary placement, regrasping, repositioning, role exchange and tool operation are allowed. No runtime pose edits, hidden support forces or collision bypasses. Alternative legal solutions count even when they differ from the intended research hypothesis.

## 3. Detailed task descriptions

### M2-1 · Two-G1 light transport

**Initial state and objective.** Use the frozen two-G1 start, 0.25 kg floor-start box and full-height corridor walls. Deliver and release the box using the published scene, control interface, budget and scoring rules.

**Agent instruction.** Control the two robots to move the designated box from the floor through the L corridor into the goal region. Respect the published contact, actuator and stability constraints; release the cargo and finish stably.

**Execution focus.** Synchronize approach, grip and lift; monitor end loads and cargo attitude; check both box endpoints and robot envelopes through the turn; brake, lower and withdraw the hands. Skill transitions use actual poses, velocities, contacts and support rather than controller phase labels alone.

**Acceptance.** Preserve the published grasp/lift/turn/transport/lower/place scorer. Existing evidence supports only the fixed configuration, not randomized generalization, sensor-feedback planning or arbitrary skill composition.

### M2-2 · G1 + Stretch light transport

**Initial state and objective.** Replace one G1 with the selected Stretch while preserving the light cargo and environment. Use physically reachable starting poses without preattachment or hidden support.

**Agent instruction.** Use the two available robots to deliver the designated light box from the floor and release it in the goal. Choose contacts and coordinated motions using each robot's joints, end effector and mobility.

**Execution focus.** Find compatible contact positions and heights; coordinate walking with wheeled motion; account for telescope extension, wrist loads and base stability. Formation changes, temporary placement and regrasping are allowed. Equal load sharing and replay of G1 trajectories are not required.

**Acceptance and comparison.** Validate reach, grip, lift and loaded motion before attempting a continuous route. Full success requires the shared process and final-state conditions. A failed tool-free light configuration stays unvalidated. Compare with M2-1 for strategy changes and coordination cost, while keeping historical six-stage scores separate from the new task criterion.

### M2-3 · Two-G1 heavier transport

**Initial state and objective.** Change only cargo mass to screened m_H while preserving geometry and center-of-mass placement. In tool-enabled conditions, the dolly and connectors begin accessible, unloaded and disconnected.

**Agent instruction.** Deliver the designated long box to the goal. Use observation and permitted probes to assess transport feasibility; choose direct carrying or available tools, and finish with cargo released on the target floor.

**Execution focus.** Detect slip, actuator loading, asymmetric heights and gait instability; choose load distribution, speed, contacts and route accordingly. Stop advancement, legally set down and replan when stable transport cannot be maintained.

**Acceptance.** Screen grip, stable lift, short motion, turn and lowering in sequence, preserving failures. Full success requires one continuous run. A legal tool-assisted solution also counts. Separately establish a direct-carry reference for comparison with M2-4, without making it the only allowed agent solution.

### M2-4 · G1 + Stretch heavy mechanism selection

**Initial state and objective.** Match M2-3's cargo, m_H, scene, tools and information conditions; replace one robot. Use the same Stretch binding as M2-2.

**Agent instruction.** Use the available robots and objects to deliver the long box and release it on the target floor. Choose the transport method and distribute responsibilities autonomously.

**Execution focus.** Assess direct-carry margins and whether the dolly can be loaded, connected, controlled and unloaded. Allocate loading, towing, positioning and unloading based on actual capabilities. Probes and recovery consume the episode budget.

**Acceptance and hypothesis.** A tool solution must include the full floor-to-dolly-to-floor chain; manual preparation is not autonomous tool use. Legal direct carrying remains successful. The design seeks a common mass at which two G1s can carry directly while the mixed team benefits substantially from the dolly. This is a hypothesis to test, not an established result or a reason to prohibit alternative solutions.

### M2-5 · Two-G1 transport with obstacle clearing

**Initial state and objective.** Add a movable box in the turning workspace and a legal storage region to M2-3. It should obstruct the required swept space, with a feasible route after relocation. Preserve payload and tool inventory.

**Agent instruction.** Deliver the designated long box. You may reposition movable objects within the published rules. Finish with cargo, relocated objects and robots stable in their allowed regions.

**Execution focus.** Identify whether the obstruction blocks cargo or robot motion. Choose clearing before pickup or legal placement, clearing and regrasping during execution. Avoid blocking the route again. Validate obstacle size, mass, friction, access and storage space before evaluating planning.

**Acceptance and comparison.** Apply the common delivery conditions and require moved obstacles to be stably stored without invading the goal or necessary finishing space. Legal bypasses count; an easy bypass means the instance did not establish clearing necessity. Neither a particular sequence nor a mandatory regrasp is imposed. Compare against M2-3. The first version uses a visible initial obstruction, not a surprise dynamic obstacle.

### M2-6 · Three-G1 division of work

**Initial state and objective.** Reuse the entire M2-5 scene, adding only a third identical G1 at a legal noninterfering start. Keep the original robot positions.

**Agent instruction.** Control the three robots to deliver the long box and handle movable objects along the route. Allocate work autonomously and finish with every robot stable.

**Execution focus.** Decide whether the third robot clears, moves tools, carries, positions or waits. Coordinate workspace occupancy, sequencing and handoffs. Two carriers plus one clearing robot is an author-side candidate, not a prescribed role assignment. Simultaneous three-robot cargo contact is unnecessary.

**Acceptance and comparison.** Use the same cargo and obstacle rules as M2-5, adding checks for the third robot. An idle third robot does not automatically cause failure; record utilization and actual contribution. Compare success, elapsed time, aggregate robot action cost, temporary placements, regrasps, waiting and mutual obstruction under matched budgets. Report coordination overhead as well as benefits.

## 4. Evaluation and controls

**Preserve L1; version new criteria separately.** M2-2–6 use goal containment, legal support and release, stable robots and process constraints, without a universal four-hand rule. If cargo has no physical damage model, report impact/contact/drop proxies rather than claiming damage validation. Distinguish permitted tool and obstacle contact from prohibited collisions.

**Calibrate before evaluation.** Final dwell, speed, tilt, force/impact thresholds, effort margins, containment tolerance and budgets remain to be frozen for new configurations. Do not copy G1 thresholds to Stretch or three-robot scenes without validation. Resolve the working-tree versus release scorer-version discrepancy against the immutable L1 packet.

**Observations.** Expose only declared vision, proprioception, tactile and force interfaces; log differences between bodies. Unknown-condition episodes do not expose mass, friction, hidden capability scaling or the correct tool. Author-side physical truth stays outside agent input. Record feasibility predictions, confidence, evidence and post-probe updates.

**Matched comparisons.** 1↔2 and 3↔4 test embodiment; 1↔3 and 2↔4 test mass; 3↔5 tests obstruction; 5↔6 tests team size. Use tool-free conditions on both sides of the mass comparison, estimating tool benefits separately through within-task ablations. Other comparisons also match tool availability and information conditions; document necessary stance differences. New controlled evaluations may be added for comparable statistics, but do not rewrite historical L1 outcomes.

**Ablations.** On M2-3/4, cross tool availability with dedicated active probing, and add a known-parameter reference. Normal execution feedback remains available in every group; define dedicated identification actions before evaluation. Conditions and seeds do not add task IDs. Match simulation-time, action and observation budgets, and report aggregate and per-robot costs for three-robot teams.

**Solo checks.** Give reasonable single-robot alternatives the same cargo, tools and comparable resources. Distinguish necessity from efficiency gains. One failed solo policy does not prove physical impossibility; repeated identical seeds do not establish randomized coverage.

**Records.** Preserve outcome and failure stage, cargo/robot trajectories, actuator forces, contact/support, load distribution, tool and obstacle states, role changes, probe costs, feasibility estimates, recovery, placement/regrasp counts, waiting, interference, completion time, video and configuration hashes. Load shares are diagnostics, not equal-contribution requirements.

## 5. Delivery order and open parameters

1. Freeze and independently reproduce M2-1; document skill transitions and scorer identity.
2. Bind a Stretch model and validate M2-2; screen M2-3 loads.
3. Validate M2-4 at a matched load, including the full tool loading/unloading chain.
4. Calibrate the obstruction and storage region; complete M2-5 and then matched M2-6.
5. Freeze parameters and budgets; run tool, probing, solo and team-size controls with perturbation repeats.

Open parameters: Stretch identity, m_H, dolly and connector/unloading mechanism, obstacle geometry/mass and storage region, third-robot start, new scorer thresholds, public sensors, budgets and validation seeds. Go2, A3, hand swaps, rotary supports and broad geometry randomization are outside this initial six-configuration scope.

Each new configuration needs at least one continuous physical witness from the declared start to the legal final state before admission to the instance set. Asset import, static screening, local probes and full success remain separate evidence categories. Preserve failures and never splice successful segments from different runs.
