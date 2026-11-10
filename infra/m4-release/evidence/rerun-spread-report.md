# M4 reference re-run spread

## Same scene, same arguments (sandbox recordings)

| variant | recordings compared | rows | bitwise identical | verdict identical | score | stage times |
| --- | --- | --- | --- | --- | --- | --- |
| base | base-v1 vs base-v2 | 1816 / 1816 | True | True | 1.0 | 2.16 / 10.34 / 24.5 / 30.38 / 33.38 |
| base | base-v1 vs base-v3 | 1816 / 1816 | True | True | 1.0 | 2.16 / 10.34 / 24.5 / 30.38 / 33.38 |
| hard | hard-v1 vs hard-v2 | 1910 / 1910 | True | True | 1.0 | 1.66 / 16.84 / 22.34 / 31.24 / 34.52 |
| hard | hard-v1 vs hard-v3 | 1910 / 1910 | True | True | 1.0 | 1.66 / 16.84 / 22.34 / 31.24 / 34.52 |

## Settle-time perturbation (expert's own runs on the sealed scenes, multi_robot/evaluate.py)

| variant | run | settle_s | sealed scene | goal_observed | violations | delivered (s) | final dwell (s) | max stance slide (m, limit 0.05) | max tension (N) | max tilt (deg) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | rep-m080-s100 | 1.0 | True | True | - | 31.28 | 4.92 | 0.0471 | 149.4 | 25.6 |
| base | rep-m080-s105 | 1.05 | True | True | - | 31.1 | 4.94 | 0.0484 | 149.9 | 24.8 |
| base | rep-m080-s110 | 1.1 | True | True | - | 29.84 | 4.96 | 0.044 | 133.6 | 20.6 |
| base | rep-m080-s115 | 1.15 | True | False | traction_and_slip | 31.42 | 4.92 | 0.0751 | 143.9 | 24.8 |
| base | rep-m080-s120 | 1.2 | True | False | traction_and_slip | 31.28 | 0.56 | 0.0566 | 150.3 | 24.4 |
| base | rep-m080-s125 | 1.25 | True | True | - | 31.64 | 4.92 | 0.0329 | 159.0 | 25.7 |
| base | **4/6 pass** | | | | | [29.84, 31.64] | [4.92, 4.96] | [0.0329, 0.0751] | | |
| hard | hard-a-s1.0 | 1.0 | True | True | - | 32.42 | 5.66 | 0.0424 | 168.5 | 19.8 |
| hard | hard-a-s1.05 | 1.05 | True | True | - | 32.42 | 5.56 | 0.0491 | 157.2 | 16.4 |
| hard | hard-a-s1.1 | 1.1 | True | True | - | 32.26 | 5.8 | 0.0431 | 168.3 | 17.0 |
| hard | hard-a-s1.15 | 1.15 | True | True | - | 33.72 | 5.5 | 0.0442 | 192.6 | 15.8 |
| hard | hard-a-s1.2 | 1.2 | True | True | - | 33.1 | 5.5 | 0.047 | 156.6 | 16.8 |
| hard | hard-a-s1.25 | 1.25 | True | True | - | 32.8 | 5.46 | 0.0406 | 175.8 | 16.2 |
| hard | hard-b-s1.3 | 1.3 | True | False | traction_and_slip | 33.84 | 0.06 | 0.0534 | 181.5 | 14.5 |
| hard | hard-b-s1.35 | 1.35 | True | True | - | 33.18 | 5.44 | 0.0399 | 184.2 | 17.2 |
| hard | hard-b-s1.4 | 1.4 | True | True | - | 32.6 | 5.5 | 0.0454 | 176.8 | 18.2 |
| hard | hard-b-s1.45 | 1.45 | True | False | traction_and_slip | 33.32 | 5.36 | 0.0615 | 181.9 | 15.2 |
| hard | hard-b-s1.5 | 1.5 | True | True | - | 33.36 | 5.48 | 0.0432 | 171.0 | 15.1 |
| hard | hard-b-s1.55 | 1.55 | True | True | - | 32.88 | 5.46 | 0.0392 | 175.1 | 15.0 |
| hard | **10/12 pass** | | | | | [32.26, 33.84] | [5.44, 5.8] | [0.0392, 0.0615] | | |

## Sandbox recordings of perturbed runs (current verifier)

| run | variant | ctl | score | success | first violation | sandbox vs evaluate.py vs expert | evidence per sample agrees |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base-settle1.15-v1 | base | {"settle_s": 1.15} | 0.3405 | False | {'traction_and_slip': 17.78} | False / False / False | True |
| hard-settle1.45-v1 | hard | {"settle_s": 1.45} | 0.6363 | False | {'traction_and_slip': 26.18} | False / False / False | True |
