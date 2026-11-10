# Sokoban paired isolated sandbox

Two distinct token-authenticated workers expose views of one trusted world.
RPC threads dispatch all physics and sensor operations to the main thread.
Each delivered program runs in its own read-only Docker container and private
network. Only its own workspace, onboard sensor view and explicit messages are
available. Both 43-joint target vectors are required before one shared step.

```sh
python -m multi_robot.g1_sokoban.sandbox.launch --name paired-smoke --sim-time 1 --agent-a multi_robot/g1_sokoban/sandbox/agent_sdk/examples --agent-b multi_robot/g1_sokoban/sandbox/agent_sdk/examples -- python hello_robot.py
```

For development only, add `--mode dev --isolation process`; this does not provide
filesystem isolation. GPU Genesis and the existing G1 assets are required.
No privileged reference code is copied into the agent bundle. Task source and
assets must come from the complete workspace dependency pack, not only the rc2
review packet. The paired adapter retains the native physics configuration.

Trusted records retain every control command, physics-step contact/state sample,
message, separate request hash chains and sealed deliverables. Arrival is
independently re-evaluated. Full push-only/contact certification remains open:
`task_success` stays null and the task score is withheld (0), even on arrival.
Interface success is separately named `interface_checks_passed`.

Actual startup/container/escape results are reported in the unified sandbox
validation ledger. This implementation alone is not a new end-to-end success.
