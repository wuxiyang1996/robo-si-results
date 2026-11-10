# H5 reference controller

The [layer 1 release](https://github.com/wuxiyang1996/robo-si/releases/tag/h5-layer1-20261023) is the source of truth for the published
5/5 full runs and 20/20 standalone subtasks. Download its offline packet for
the exact controller, configuration, logs and reproduction preflight.

The maintained source in this directory consists of:

- [skate/](skate/README.md): the platform transport controller and its skills.
- `video.py`: frame recording used by the reference runner.
- `loop_monitor.py`: contact and support predicates retained for existing tests.
- `arm_ik.py`: arm Jacobian IK shared with the cart and door tasks.
- `run_candidate.py`: compatibility import for `ArmIK`; the old candidate CLI
  has been removed.

Legacy pickup and planning probes, experimental indexes, development runners
and local run data are removed. The old development diary is preserved in
[Git history](https://github.com/wuxiyang1996/robo-si/tree/5089a845a1168259a37a875a778c777a0dd131bf/humanoid/g1_lever_assisted_transport/solution). Existing sandbox consistency evidence is
retained separately. Use the frozen release for result reproduction; maintenance
of this checkout does not update its recorded source hashes.
