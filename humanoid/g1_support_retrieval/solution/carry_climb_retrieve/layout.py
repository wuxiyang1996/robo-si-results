"""Geometric support candidates only; execution must verify grasp and stability."""

from itertools import permutations


def support_layout(
    boxes, shelf_height, cabinet_front=3.3, floor_reach=1.15, step_limit=0.30
):
    required = max(0.0, shelf_height - floor_reach)
    if required == 0:
        return []
    usable = [
        b
        for b in boxes
        if b["size"][0] >= 0.22 and b["size"][1] >= 0.30 and b["mass"] > 0
    ]
    for count in range(1, len(usable) + 1):
        candidates = []
        for chain in permutations(usable, count):
            heights = [0.0] + [b["size"][2] for b in chain]
            if heights[-1] + 1e-6 < required:
                continue
            if not all(
                0 < b - a <= step_limit + 1e-6 for a, b in zip(heights, heights[1:])
            ):
                continue
            candidates.append(chain)
        if not candidates:
            continue
        chosen = min(
            candidates, key=lambda c: (sum(b["mass"] for b in c), c[-1]["size"][2])
        )
        edge = cabinet_front - 0.05
        layout = []
        for box in reversed(chosen):
            depth, width, height = box["size"]
            layout.append(
                dict(
                    **box,
                    goal=[edge - depth / 2, 0.0, height / 2],
                    verified=False,
                    scope="geometric_candidate_only",
                )
            )
            edge -= depth + 0.02
        return list(reversed(layout))
    raise ValueError(
        "No geometric support candidate within the supplied step and footprint limits"
    )
