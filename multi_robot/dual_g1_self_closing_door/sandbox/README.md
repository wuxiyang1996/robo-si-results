# H3 isolated native sandbox

The new adapter preserves the native environment, joint-only actuator law and
native scorer. The shared launcher provides sealed scenarios/deliveries, private
Docker networks, read-only agent roots and trusted hash-chained RPC records.
The public bundle contains only SDK/model/tools/instructions and smoke examples.

```sh
python -m multi_robot.dual_g1_self_closing_door.sandbox.launch --mode dev --isolation process --seed 0 --sim-time 1 --sensors proprio --no-video --agent-dir multi_robot/dual_g1_self_closing_door/sandbox/agent_sdk/examples -- python hello_robot.py
python -m multi_robot.dual_g1_self_closing_door.sandbox.launch --mode eval --sim-time 1 --sensors proprio --no-video --agent-dir multi_robot/dual_g1_self_closing_door/sandbox/agent_sdk/examples -- python hello_robot.py
```

Full native scorer inputs are recorded at physics frequency and independently
replayed on the trusted side. Successful smoke execution means interface health,
not task success. A no-op is expected to score zero without VOID. Existing
native reference successes remain their original evidence; they are not counted
as a new full sandbox replay. See the unified sandbox validation report for
checks actually completed. Formal admission is separate.
