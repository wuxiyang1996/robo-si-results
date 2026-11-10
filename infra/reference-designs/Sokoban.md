# Sokoban · 双 G1 未知地图推箱清路：参考解设计

<!-- sokoban-current-design -->
> 当前任务设计：[从局部观察到全局建图](../planning/sokoban/design.md)。以全局建图、通信对照和可选自主工具构建为主线；下文保留历史参考执行与证据范围。

已有声明范围内的参考执行见证；本文补齐统一设计说明。本次新增物理运行：0。

## 设计思路

两台机器人从自身图像与本体感知建立局部地图，通过显式消息协调离散走动与推箱操作，再展开为转向、步行、接近、推行及扫描轨迹。完整开发地图见证不能替代未见地图或仅推不抓的完整接触认证。

## 选定参考与范围

四箱开发地图；自身 RGB、本体感知与显式消息；单次完整实验见证。

Gamma 8011370：279.18 s、24 个高层操作、76 个低层段；两机到各自目标并保持 3 s。独立采样审阅及完整公共输入回放通过；task_success=null。

## 配置／见证 sokoban-8011370

[完整分层映射与生成来源](../sokoban-release/mapping.json)。下面的轨迹段来自同一连续记录；准备与上下文段也保留。

| 操作 | 机器人 | 动作 | 低层段 | 实测后置条件 |
| --- | --- | --- | --- | --- |
| action_1 | g1_a | walk | ["segment_7"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.1273854821920395, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_2 | g1_b | walk | ["segment_10"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.09729092121124272, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_3 | g1_b | walk | ["segment_13"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.12796814441680882, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_4 | g1_b | walk | ["segment_15"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.13690230846405005, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_5 | g1_b | walk | ["segment_17"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.12639222145080542, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_6 | g1_a | push | ["segment_19", "segment_20", "segment_21", "segment_22", "segment_23", "segment_24", "segment_25"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.10844402313232449, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule", "crate": "crate_d", "crate_target_cell_reached": true, "crate_cell_center_error_linf_m": 0.12481286525726332, "displacement_m": [1.0248128175735474, -0.012602751253751335]} |
| action_7 | g1_a | push | ["segment_26", "segment_27", "segment_28", "segment_29", "segment_30", "segment_31", "segment_32"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.12386236190795896, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule", "crate": "crate_a", "crate_target_cell_reached": true, "crate_cell_center_error_linf_m": 0.1249409437179565, "displacement_m": [0.04608607292175293, 1.0249409675598145]} |
| action_8 | g1_a | walk | ["segment_33"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.07554844617843615, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_9 | g1_a | walk | ["segment_34"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.021340680122375444, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_10 | g1_b | push | ["segment_36", "segment_37", "segment_38", "segment_39", "segment_40", "segment_41", "segment_42"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.1307489424943924, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule", "crate": "crate_c", "crate_target_cell_reached": true, "crate_cell_center_error_linf_m": 0.20348474979400644, "displacement_m": [-1.103484749722887, 0.0862802267074585]} |
| action_11 | g1_b | push | ["segment_44", "segment_45", "segment_46", "segment_47", "segment_48", "segment_49", "segment_50"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.2160142421722413, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule", "crate": "crate_c", "crate_target_cell_reached": true, "crate_cell_center_error_linf_m": 0.26437087059021014, "displacement_m": [-0.9608861207962036, -0.10270291566848755]} |
| action_12 | g1_b | push | ["segment_52", "segment_53", "segment_54", "segment_55", "segment_56", "segment_57", "segment_58"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.2154469013214113, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule", "crate": "crate_c", "crate_target_cell_reached": true, "crate_cell_center_error_linf_m": 0.12499837875366193, "displacement_m": [-0.7606275081634521, 0.07241791486740112]} |
| action_13 | g1_a | walk | ["segment_60"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.13441703319549558, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_14 | g1_a | walk | ["segment_61"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.12838828563690186, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_15 | g1_a | walk | ["segment_62"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.12018259763717642, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_16 | g1_a | walk | ["segment_63"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.13259273767471313, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_17 | g1_a | walk | ["segment_64"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.11106102466583234, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_18 | g1_a | walk | ["segment_65"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.09153242111206072, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_19 | g1_a | walk | ["segment_66"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.13726797103881838, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_20 | g1_a | walk | ["segment_67"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.12455766201019314, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_21 | g1_b | walk | ["segment_69"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.10868376493453924, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_22 | g1_b | walk | ["segment_71"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.13589591979980487, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_23 | g1_b | walk | ["segment_73"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.1290633916854852, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |
| action_24 | g1_b | walk | ["segment_75"] | {"robot_target_cell_reached": true, "robot_cell_center_error_linf_m": 0.13528292179107604, "interpretation": "Nominal cell occupancy, not exact center tracking or an extra task scoring rule"} |

| 低层段 | 机器人／高层 | 动作 | 约束 | 轨迹时间 s |
| --- | --- | --- | --- | --- |
| segment_1 | g1_a / episode_context | Stabilize before the initial camera scan. | Initial 2 s before scanning; zero yaw command. | [0.0, 2.0] |
| segment_2 | g1_b / episode_context | Stabilize before the initial camera scan. | Initial 2 s before scanning; zero yaw command. | [0.0, 2.0] |
| segment_3 | g1_a / episode_context | Turn and reconstruct local visible cells from own RGB and proprioception. | Own unwrapped yaw completes a turn; 30 s scan timeout. | [2.0, 9.86] |
| segment_4 | g1_b / episode_context | Turn and reconstruct local visible cells from own RGB and proprioception. | Own unwrapped yaw completes a turn; 30 s scan timeout. | [2.0, 10.58] |
| segment_5 | g1_a / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [9.86, 10.6] |
| segment_6 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [10.58, 24.0] |
| segment_7 | g1_a / action_1 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [10.6, 16.82] |
| segment_8 | g1_a / episode_context | Turn and reconstruct local visible cells from own RGB and proprioception. | Own unwrapped yaw completes a turn; 30 s scan timeout. | [16.82, 23.98] |
| segment_9 | g1_a / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [23.98, 58.92] |
| segment_10 | g1_b / action_2 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [24.0, 30.900000000000002] |
| segment_11 | g1_b / episode_context | Turn and reconstruct local visible cells from own RGB and proprioception. | Own unwrapped yaw completes a turn; 30 s scan timeout. | [30.900000000000002, 38.86] |
| segment_12 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [38.86, 38.9] |
| segment_13 | g1_b / action_3 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [38.9, 45.86] |
| segment_14 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [45.86, 45.9] |
| segment_15 | g1_b / action_4 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [45.9, 52.26] |
| segment_16 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [52.26, 52.300000000000004] |
| segment_17 | g1_b / action_5 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [52.300000000000004, 58.9] |
| segment_18 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [58.9, 125.18] |
| segment_19 | g1_a / action_6 | Approach the visually tracked crate and align the pushing direction. | Target 0.95 m behind the visually tracked crate; <0.13 m position and <0.16 rad heading error. | [58.92, 61.04] |
| segment_20 | g1_a / action_6 | Deploy the pushing posture, lower commanded height smoothly, and anchor to the stationary crate. | 3 s blend; height command ramps 0.72 to 0.65 m; visual anchor corrections restricted to <0.25 m. | [61.04, 64.04] |
| segment_21 | g1_a / action_6 | Advance with visual crate tracking, lateral correction and heading feedback. | Forward command 0.18 m/s, lateral correction capped at 0.08 m/s; stop at estimated remaining distance <0.06 m; stale tracking >1 s stops translation. | [64.04, 75.42] |
| segment_22 | g1_a / action_6 | Retreat until own odometry or fresh RGB plus own FK indicates release clearance. | Backward command 0.30 m/s; release after >0.20 m estimated retreat OR fresh RGB (<0.3 s) and own-FK clearance >0.08 m. | [75.42, 76.02] |
| segment_23 | g1_a / action_6 | Hold the crouched posture for one second after retreat. | 1 s at zero commanded velocity and 0.65 m height command. | [76.02, 77.04] |
| segment_24 | g1_a / action_6 | Retract the arms while smoothly restoring the standing height command. | 3 s blend; height command ramps 0.65 to 0.72 m. | [77.04, 80.06] |
| segment_25 | g1_a / action_6 | Move to the post-push robot subgoal and complete the operation. | Post-push robot subgoal: <0.13 m position and <0.16 rad heading error. | [80.06, 85.84] |
| segment_26 | g1_a / action_7 | Approach the visually tracked crate and align the pushing direction. | Target 0.95 m behind the visually tracked crate; <0.13 m position and <0.16 rad heading error. | [85.84, 87.86] |
| segment_27 | g1_a / action_7 | Deploy the pushing posture, lower commanded height smoothly, and anchor to the stationary crate. | 3 s blend; height command ramps 0.72 to 0.65 m; visual anchor corrections restricted to <0.25 m. | [87.86, 90.88] |
| segment_28 | g1_a / action_7 | Advance with visual crate tracking, lateral correction and heading feedback. | Forward command 0.18 m/s, lateral correction capped at 0.08 m/s; stop at estimated remaining distance <0.06 m; stale tracking >1 s stops translation. | [90.88, 102.62] |
| segment_29 | g1_a / action_7 | Retreat until own odometry or fresh RGB plus own FK indicates release clearance. | Backward command 0.30 m/s; release after >0.20 m estimated retreat OR fresh RGB (<0.3 s) and own-FK clearance >0.08 m. | [102.62, 103.12] |
| segment_30 | g1_a / action_7 | Hold the crouched posture for one second after retreat. | 1 s at zero commanded velocity and 0.65 m height command. | [103.12, 104.14] |
| segment_31 | g1_a / action_7 | Retract the arms while smoothly restoring the standing height command. | 3 s blend; height command ramps 0.65 to 0.72 m. | [104.14, 107.16] |
| segment_32 | g1_a / action_7 | Move to the post-push robot subgoal and complete the operation. | Post-push robot subgoal: <0.13 m position and <0.16 rad heading error. | [107.16, 110.9] |
| segment_33 | g1_a / action_8 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [110.9, 117.38] |
| segment_34 | g1_a / action_9 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [117.38, 125.16] |
| segment_35 | g1_a / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [125.16, 194.8] |
| segment_36 | g1_b / action_10 | Approach the visually tracked crate and align the pushing direction. | Target 0.95 m behind the visually tracked crate; <0.13 m position and <0.16 rad heading error. | [125.18, 128.84] |
| segment_37 | g1_b / action_10 | Deploy the pushing posture, lower commanded height smoothly, and anchor to the stationary crate. | 3 s blend; height command ramps 0.72 to 0.65 m; visual anchor corrections restricted to <0.25 m. | [128.84, 131.84] |
| segment_38 | g1_b / action_10 | Advance with visual crate tracking, lateral correction and heading feedback. | Forward command 0.18 m/s, lateral correction capped at 0.08 m/s; stop at estimated remaining distance <0.06 m; stale tracking >1 s stops translation. | [131.84, 141.92000000000002] |
| segment_39 | g1_b / action_10 | Retreat until own odometry or fresh RGB plus own FK indicates release clearance. | Backward command 0.30 m/s; release after >0.20 m estimated retreat OR fresh RGB (<0.3 s) and own-FK clearance >0.08 m. | [141.92000000000002, 142.56] |
| segment_40 | g1_b / action_10 | Hold the crouched posture for one second after retreat. | 1 s at zero commanded velocity and 0.65 m height command. | [142.56, 143.56] |
| segment_41 | g1_b / action_10 | Retract the arms while smoothly restoring the standing height command. | 3 s blend; height command ramps 0.65 to 0.72 m. | [143.56, 146.56] |
| segment_42 | g1_b / action_10 | Move to the post-push robot subgoal and complete the operation. | Post-push robot subgoal: <0.13 m position and <0.16 rad heading error. | [146.56, 150.9] |
| segment_43 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [150.9, 150.96] |
| segment_44 | g1_b / action_11 | Approach the visually tracked crate and align the pushing direction. | Target 0.95 m behind the visually tracked crate; <0.13 m position and <0.16 rad heading error. | [150.96, 151.34] |
| segment_45 | g1_b / action_11 | Deploy the pushing posture, lower commanded height smoothly, and anchor to the stationary crate. | 3 s blend; height command ramps 0.72 to 0.65 m; visual anchor corrections restricted to <0.25 m. | [151.34, 154.34] |
| segment_46 | g1_b / action_11 | Advance with visual crate tracking, lateral correction and heading feedback. | Forward command 0.18 m/s, lateral correction capped at 0.08 m/s; stop at estimated remaining distance <0.06 m; stale tracking >1 s stops translation. | [154.34, 159.82] |
| segment_47 | g1_b / action_11 | Retreat until own odometry or fresh RGB plus own FK indicates release clearance. | Backward command 0.30 m/s; release after >0.20 m estimated retreat OR fresh RGB (<0.3 s) and own-FK clearance >0.08 m. | [159.82, 161.0] |
| segment_48 | g1_b / action_11 | Hold the crouched posture for one second after retreat. | 1 s at zero commanded velocity and 0.65 m height command. | [161.0, 162.0] |
| segment_49 | g1_b / action_11 | Retract the arms while smoothly restoring the standing height command. | 3 s blend; height command ramps 0.65 to 0.72 m. | [162.0, 165.0] |
| segment_50 | g1_b / action_11 | Move to the post-push robot subgoal and complete the operation. | Post-push robot subgoal: <0.13 m position and <0.16 rad heading error. | [165.0, 169.6] |
| segment_51 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [169.6, 169.66] |
| segment_52 | g1_b / action_12 | Approach the visually tracked crate and align the pushing direction. | Target 0.95 m behind the visually tracked crate; <0.13 m position and <0.16 rad heading error. | [169.66, 169.70000000000002] |
| segment_53 | g1_b / action_12 | Deploy the pushing posture, lower commanded height smoothly, and anchor to the stationary crate. | 3 s blend; height command ramps 0.72 to 0.65 m; visual anchor corrections restricted to <0.25 m. | [169.70000000000002, 172.70000000000002] |
| segment_54 | g1_b / action_12 | Advance with visual crate tracking, lateral correction and heading feedback. | Forward command 0.18 m/s, lateral correction capped at 0.08 m/s; stop at estimated remaining distance <0.06 m; stale tracking >1 s stops translation. | [172.70000000000002, 186.62] |
| segment_55 | g1_b / action_12 | Retreat until own odometry or fresh RGB plus own FK indicates release clearance. | Backward command 0.30 m/s; release after >0.20 m estimated retreat OR fresh RGB (<0.3 s) and own-FK clearance >0.08 m. | [186.62, 187.12] |
| segment_56 | g1_b / action_12 | Hold the crouched posture for one second after retreat. | 1 s at zero commanded velocity and 0.65 m height command. | [187.12, 188.12] |
| segment_57 | g1_b / action_12 | Retract the arms while smoothly restoring the standing height command. | 3 s blend; height command ramps 0.65 to 0.72 m. | [188.12, 191.12] |
| segment_58 | g1_b / action_12 | Move to the post-push robot subgoal and complete the operation. | Post-push robot subgoal: <0.13 m position and <0.16 rad heading error. | [191.12, 194.76] |
| segment_59 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [194.76, 248.26000000000002] |
| segment_60 | g1_a / action_13 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [194.8, 206.42000000000002] |
| segment_61 | g1_a / action_14 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [206.42000000000002, 213.14000000000001] |
| segment_62 | g1_a / action_15 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [213.14000000000001, 218.18] |
| segment_63 | g1_a / action_16 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [218.18, 224.92000000000002] |
| segment_64 | g1_a / action_17 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [224.92000000000002, 231.62] |
| segment_65 | g1_a / action_18 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [231.62, 237.38] |
| segment_66 | g1_a / action_19 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [237.38, 244.02] |
| segment_67 | g1_a / action_20 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [244.02, 248.22] |
| segment_68 | g1_a / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [248.22, 279.18] |
| segment_69 | g1_b / action_21 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [248.26000000000002, 255.68] |
| segment_70 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [255.68, 255.74] |
| segment_71 | g1_b / action_22 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [255.74, 260.86] |
| segment_72 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [260.86, 260.92] |
| segment_73 | g1_b / action_23 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [260.92, 267.62] |
| segment_74 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [267.62, 267.68] |
| segment_75 | g1_b / action_24 | Track the selected walking subgoal and heading with the leg controller. | Normally <0.13 m and <0.16 rad; settled-walk handoff permits <0.18 m after 15 s at estimated speed <0.02 m/s. | [267.68, 274.58] |
| segment_76 | g1_b / episode_context | Hold position, exchange explicit messages, or stabilize in the observed own goal. | Position/heading hold; at the observed own goal, zero velocity with own-IMU hip trim. | [274.58, 279.18] |

### 已记录检查

```json
{
  "high_to_low": true,
  "low_to_trajectory": true,
  "high_to_trajectory": true,
  "end_to_end": true,
  "complete_per_robot_command_coverage": true,
  "controls": 13959,
  "robot_command_samples": 27918,
  "both_goal_dwell_s": 3.000000000000002
}
```

## 尚需核对

完整接触/仅推不抓有效性认证、未见地图验证、协作收益对照和人工验收；仍为实验候选。

`task_success = null`：已有完成开发地图操作目标的连续实验见证，但正式任务成功判定及完整接触有效性尚未认证。公开输入重放不计作第二次物理执行。

## 复现与生成入口

- [multi_robot/g1_sokoban/README.txt](../../multi_robot/g1_sokoban/README.txt)
- [multi_robot/g1_sokoban/HIERARCHICAL_WITNESS.txt](../../multi_robot/g1_sokoban/HIERARCHICAL_WITNESS.txt)

[完整参考包](https://huggingface.co/datasets/IntelligenceLab/robo-si/resolve/6179f8994220b6c6c6e9f0deec8e087f19e517ee/releases/g1-sokoban-hidden-map-0.1.0-rc2/g1-sokoban-hidden-map-0.1.0-rc2.zip)。使用包内冻结配置、依赖说明与生成／回放入口；审阅包不替代完整包。

历史源码说明只提供设计上下文；若与冻结见证冲突，以见证的配置、控制器身份和发布清单为准。设计动作表不等同于已绑定的通用控制器。

## 验收与执行边界

本文件说明已有参考的设计与证据，不修改旧评分。任务级要求至少一个声明配置内的连续端到端生成见证；高层计划→低层动作、低层动作→轨迹、高层目标→实测终态分别核对。这里的“两两转换”是表示之间的对应，不是任意随机状态下技能可无条件拼接。

随机实例保留四种结果：有完整成功证据、通过可行性筛查、未确定、检查不通过；筛查通过不写成已证明可解。只在需要执行时生成当前局部轨迹；通用滚动规划和全随机域鲁棒性另列，不是本参考文档的完成前提。

若接触、支撑或守卫条件不满足，不推进下一动作；保留已有安全支撑并记录失败，仅在已知安全状态下重新观察与局部规划。不得凭事件名推断接触合格，不得将不同检查点的成功片段拼接成连续成功。

## 来源与版本

来源内容哈希见 [catalog.json](catalog.json)，对应生成器为 [build_reference_designs.py](../tools/build_reference_designs.py)。本次只整理设计与证据，不将待审事件关联计作验收通过。
