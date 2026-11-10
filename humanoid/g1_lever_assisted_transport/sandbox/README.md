# H5 sandbox

H5 uses the shared `infra/sandbox` runtime with a task-specific world, scenario
generator, command channel, monitors, scoring and verifier. The current
[layer 1 reference-material release](https://github.com/wuxiyang1996/robo-si/releases/tag/h5-layer1-20261023) contains 5/5 full runs and
20/20 independent subtasks. Full human sign-off and independent reproduction
remain pending; the release does not set `admitted=true`.

## Runtime and validation

- `launch.py` connects H5 to the shared launcher; `instruction.md` is the public
  task instruction and `agent_sdk/` describes the allowed observation/action API.
- `trusted/scenarios.py` declares scenarios. The canonical instruction and
  historical default remain separate from the released 100 kg v3 candidate.
- `trusted/world.py` and the shared command channel apply bounded joint commands.
- `trusted/scoring.py`, `trusted/monitors.py` and `trusted/verifier.py` evaluate
  the recorded contact, support, transport and safety evidence.
- `trusted/record_reference.py` and `trusted/subtask_reference.py` record the
  full controller and independent checkpoint continuations.
- `pipeline.json` defines CPU, GPU and container checks. `../admission.json`
  records historical admission evidence; it is not a declaration that all
  first-layer release reviews have passed.

For the release, download the frozen offline packet and run its reproduction
preflight. Execute physical reproduction only in a fresh output directory.
For current-source checks from the repository root:

```powershell
python -m unittest humanoid.g1_lever_assisted_transport.sandbox.tests.test_scoring humanoid.g1_lever_assisted_transport.sandbox.tests.test_monitors
python -m infra.sandbox.records humanoid/g1_lever_assisted_transport/admission.json
```

The obsolete development diary and `solution/runs` history have been removed
from the active workspace. `sandbox/runs` and acceptance records referenced by
the pipeline, admission record, counterexample audit or release are retained.
Cleanup does not change recorded evidence or constitute a fresh physical run.
