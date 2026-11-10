"""Guard ordinary simulator state-write APIs during representative execution.

This is a development integrity check, not isolation against hostile policies.
"""
from copy import deepcopy

import numpy as np

from humanoid.g1_tabletop_assembly.solution.recording import EpisodeAudit


class DiskEpisodeAudit(EpisodeAudit):
    def __enter__(self):
        if self.active or self.initial_observation is not None:
            raise RuntimeError("episode audit is single-use")
        initial = deepcopy(self.env.reset())
        if self.env.physics_steps != 0 or initial["time"] != 0:
            raise ValueError("fresh reset must start at time zero")
        disk = initial["objects"]["disk"]
        expected = (*self.env.cfg.start_xy, self.env.cfg.rest_z)
        if not np.allclose(disk["pos"], expected, rtol=0, atol=1e-6):
            raise ValueError("reset disk position differs from declared configuration")
        if not np.allclose(disk["quat"], [1, 0, 0, 0], rtol=0, atol=1e-6):
            raise ValueError("reset disk must have orange face up")
        for name in ("linear_velocity", "angular_velocity"):
            if not np.allclose(disk[name], 0., rtol=0, atol=1e-6):
                raise ValueError("reset disk must be stationary")
        if not np.allclose(initial["joint_position"], self.env.default_q.cpu().numpy(), rtol=0, atol=1e-6):
            raise ValueError("reset robot differs from default posture")
        if not np.allclose(initial["joint_velocity"], 0., rtol=0, atol=1e-6):
            raise ValueError("reset robot must be stationary")
        self.initial_observation = initial
        self.fresh_default_reset = True
        try:
            entities = {"robot": self.env.robot, **self.env.objects}
            for index, entity in enumerate(self.env.scene.entities):
                if all(entity is not known for known in entities.values()):
                    entities[f"scene_entity_{index}"] = entity
            for label, entity in entities.items():
                for method in self.ENTITY_METHODS:
                    self._guard(entity, method, label)
            self._guard(self.env.scene, "reset", "scene")
            self._guard(self.env.scene, "set_state", "scene")
            self._guard(self.env, "reset", "env")
            self.active = True
            return self
        except BaseException:
            self._restore()
            raise

    def report(self):
        result = super().report()
        result["fresh_declared_config_reset"] = result.pop("fresh_default_reset")
        return result
