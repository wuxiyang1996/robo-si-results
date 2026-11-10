# DiskFlip · G1 桌面轻柔翻盘：参考解设计

已有声明范围内的参考执行见证；本文补齐统一设计说明。本次新增物理运行：0。

## 设计思路

轻推圆盘至桌边以形成可夹取几何，再双手夹持、抬升翻转、放回桌面并释放。先由桌面支撑、后由双手承载、最后回到桌面支撑，防止将运动学翻面误算为稳定交付。

## 选定参考与范围

固定骨盆、双 Dex3；名义与横向偏移两个声明配置。

6/6 全程（每配置 3 次）与 2/2 独立动作回放通过；两条见证分别有 26/27 个低层轨迹段及三层映射。

## 配置／见证 nominal

[完整分层映射与生成来源](../../humanoid/g1_tabletop_disk_flip/validation/hierarchical/nominal.json)。下面的轨迹段来自同一连续记录；准备与上下文段也保留。

| 高层目标 | 低层段 | 实测完成条件 |
| --- | --- | --- |
| slide · 轻推到桌边 | ["L01", "L02", "L03", "L04", "L05"] | ["at_edge"] |
| clamp · 建立双手独立夹持 | ["L06", "L07", "L08", "L09", "L10", "L11"] | ["bimanual_clamp"] |
| lift · 双手抬起并建立翻转净空 | ["L12"] | ["bimanual_clamp", "clear"] |
| turn · 双手翻面至蓝面朝上 | ["L13"] | ["bimanual_clamp", "clear", "inverted"] |
| place · 放回桌面并释放稳定 | ["L14", "L15", "L16", "L17", "L18", "L19", "L20", "L21", "L22", "L23", "L24", "L25", "L26"] | ["inverted", "placed", "released", "still", "in_goal"] |

| 低层段 | 动作 | 约束／支撑 | 时间 s | 命令切片 |
| --- | --- | --- | --- | --- |
| L01 | 稳定抬起且分开的双手 | 盘由桌面支撑；双手先稳定 | [0.0, 4.5] | [0, 225] |
| L02 | 拇指从上方接近远侧盘沿 | 接近阶段避免提前碰盘 | [4.5, 12.5] | [225, 625] |
| L03 | 在远侧盘沿外降低拇指 | 沿盘外侧下降，保留桌面支撑 | [12.5, 20.5] | [625, 1025] |
| L04 | 低速建立拇指推盘接触 | 以测得接触建立推力，限制速度与受力 | [20.5, 31.88] | [1025, 1594] |
| L05 | 沿桌面轻推至近侧桌沿 | 按实测悬伸量停止，盘心仍在支撑侧 | [31.88, 64.32000000000001] | [1594, 3216] |
| L06 | 卸掉原推盘拇指的载荷 | 先卸力，再撤离；桌面继续承载 | [64.32000000000001, 69.82000000000001] | [3216, 3491] |
| L07 | 撤开推盘拇指 | 从盘沿退出，避免带动圆盘 | [69.82000000000001, 75.82000000000001] | [3491, 3791] |
| L08 | 双手撤至盘上方和侧方 | 为改变手型预留几何空间 | [75.82000000000001, 91.82000000000001] | [3791, 4591] |
| L09 | 调整腕部姿态以双手接近 | 局部 IK 使用关节范围和腕部间隙约束 | [91.82000000000001, 107.82000000000001] | [4591, 5391] |
| L10 | 预张开并调整空载手指 | 空载预整形后再建立盘面接触 | [107.82000000000001, 130.88] | [5391, 6544] |
| L11 | 分别闭合两手的拇指与下侧手指 | 每只手建立两盘面的独立夹持；按接触力臂分配载荷 | [130.88, 161.42000000000002] | [6544, 8071] |
| L12 | 保持双手夹持共同抬盘 | 保持双手支撑；夹持丢失不得超过 0.1 s；建立旋转净空 | [161.42000000000002, 172.8] | [8071, 8640] |
| L13 | 同步旋转两手以翻转圆盘 | 双手夹持，腕部间隙、姿态和切向载荷反馈；保留全局限值 | [172.8, 222.82] | [8640, 11141] |
| L14 | 翻面后先稳定双手夹持 | 蓝面朝上，准备受控支撑交接 | [222.82, 232.84] | [11141, 11642] |
| L15 | 将载荷移交右手夹持并释放左手 | 此交接只发生在双手翻面完成后；保持圆盘受支撑 | [232.84, 241.16] | [11642, 12058] |
| L16 | 移开左手并准备再次推盘 | 右手承载，左手从盘体附近移开 | [241.16, 257.16] | [12058, 12858] |
| L17 | 右手将反面朝上的盘移至桌沿外侧 | 保持姿态与右手支撑，避免下侧手指被桌沿夹住 | [257.16, 277.16] | [12858, 13858] |
| L18 | 在桌沿外降低右手及圆盘 | 盘与承载手在桌沿外下降 | [277.16, 302.16] | [13858, 15108] |
| L19 | 对齐圆盘与桌面高度 | 按测量高度调整，继续由右手支撑 | [302.16, 305.36] | [15108, 15268] |
| L20 | 左手拇指从上方接近近侧盘沿 | 右手承载期间保持推盘手净空 | [305.36, 323.36] | [15268, 16168] |
| L21 | 在近侧盘沿外降低左手拇指 | 沿盘外侧下降至推盘高度 | [323.36, 335.36] | [16168, 16768] |
| L22 | 建立左手拇指与盘沿的轻柔接触 | 右手继续承载，左手低速寻找接触 | [335.36, 344.2] | [16768, 17210] |
| L23 | 将圆盘从承载手推向桌面 | 逐渐建立桌面支撑并打开右拇指；控制合力和姿态 | [344.2, 407.76] | [17210, 20388] |
| L24 | 核对桌面与下侧指垫共同承载 | 明确记录支撑交接控制步，不将它省略成瞬时跳转 | [407.76, 407.78000000000003] | [20388, 20389] |
| L25 | 盘心获得桌面支撑后撤出下侧指垫并继续推盘 | 撤指时暂停推进；左拇指维持桌面盘沿高度，避免撬起圆盘 | [407.78000000000003, 453.98] | [20389, 22699] |
| L26 | 卸去左拇指推力并松手稳定 | 完整位于桌内、蓝面朝上、目标内、无机器人接触并静止两秒 | [453.98, 457.305] | [22699, 22866] |

### 已记录检查

```json
{
  "command_count": 22866,
  "low_level_segment_count": 26,
  "continuous": true,
  "no_gaps_or_overlap": true,
  "no_checkpoint_splicing": true,
  "physical_peaks_400hz": {
    "linear_speed_m_s": 0.029912449286348806,
    "angular_speed_rad_s": 0.39503132416935877,
    "robot_force_n": 16.760442732601035,
    "table_force_n": 3.3998333307664694
  },
  "physical_limits": {
    "linear_speed_m_s": 0.12,
    "angular_speed_rad_s": 0.65,
    "robot_force_n": 18.0,
    "table_force_n": 8.0
  },
  "actuator_checks": {
    "effort_limits_passed": true,
    "target_speed_limit_passed": true,
    "target_speed_peak_rad_s": 0.4999999888241291,
    "applied_torque_peak_nm": [
      2.0690017060357175,
      0.05678033155675268,
      0.012653278890901032,
      0.7556413675004154,
      0.15013687503585563,
      5.648054795022428e-05,
      2.069001705479293,
      0.05678033155644406,
      0.012653605849184714,
      0.7556413876507682,
      0.1501368750358584,
      5.648054795451971e-05,
      2.519940232675951,
      16.69425661578549,
      32.124320372719225,
      10.661284028707081,
      6.477930995313297,
      3.894580530810447,
      4.463334259704499,
      1.2309704311262668,
      1.4853265043691377,
      1.1059646335052256,
      0.32000779138360974,
      0.48228224616014786,
      0.3345657837005819,
      0.46603872535275126,
      0.3126251207896198,
      0.3961596126861103,
      0.3126251425375253,
      10.661280823313312,
      4.554111263585337,
      3.8576161783672167,
      4.463319390788369,
      1.6003310090728604,
      1.4853200720695428,
      1.3177222404260212,
      0.3097880301779141,
      0.6298948942025573,
      0.3566523159277649,
      0.5437349634112956,
      0.31665576903718445,
      0.415866898333957,
      0.3166557887177386
    ],
    "effort_limit_nm": [
      88.0,
      139.0,
      88.0,
      139.0,
      50.0,
      50.0,
      88.0,
      139.0,
      88.0,
      139.0,
      50.0,
      50.0,
      88.0,
      50.0,
      50.0,
      25.0,
      25.0,
      25.0,
      25.0,
      25.0,
      5.0,
      5.0,
      2.450000047683716,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      25.0,
      25.0,
      25.0,
      25.0,
      25.0,
      5.0,
      5.0,
      2.450000047683716,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142
    ]
  },
  "robot_self_contact_observations_50hz": {
    "sampling_hz": 50,
    "threshold_n": 0.1,
    "scope": "control-boundary observations only; not substep collision certification",
    "pairs": {
      "left_hand_middle_1_link / right_hand_middle_1_link": {
        "peak_force_n": 1.0607570796658354,
        "observed_control_samples": 381
      },
      "left_hand_middle_1_link / right_hand_index_1_link": {
        "peak_force_n": 0.20192128959507438,
        "observed_control_samples": 110
      },
      "left_hand_index_1_link / right_hand_index_1_link": {
        "peak_force_n": 2.3110152892196245,
        "observed_control_samples": 1327
      },
      "left_wrist_yaw_link / torso_link": {
        "peak_force_n": 1.0620588673957603,
        "observed_control_samples": 32
      }
    }
  },
  "robot_environment_contact_observations_50hz": {
    "sampling_hz": 50,
    "threshold_n": 0.1,
    "scope": "control-boundary observations only; not substep collision certification",
    "pairs": {
      "right_wrist_yaw_link / table": {
        "peak_force_n": 3.656126278033907,
        "observed_control_samples": 67,
        "peak_time_s": 9.66,
        "peak_phase": "action_replay"
      },
      "left_hand_thumb_2_link / disk": {
        "peak_force_n": 6.067505095227168,
        "observed_control_samples": 10375,
        "peak_time_s": 370.64,
        "peak_phase": "action_replay"
      },
      "left_hand_thumb_2_link / table": {
        "peak_force_n": 3.6166379157093522,
        "observed_control_samples": 209,
        "peak_time_s": 65.72,
        "peak_phase": "action_replay"
      },
      "right_hand_middle_1_link / disk": {
        "peak_force_n": 4.92127877985766,
        "observed_control_samples": 6089,
        "peak_time_s": 221.78,
        "peak_phase": "action_replay"
      },
      "left_hand_middle_1_link / disk": {
        "peak_force_n": 3.2112850091976943,
        "observed_control_samples": 4696,
        "peak_time_s": 221.70000000000002,
        "peak_phase": "action_replay"
      },
      "right_hand_index_1_link / disk": {
        "peak_force_n": 3.090830817107952,
        "observed_control_samples": 12063,
        "peak_time_s": 404.40000000000003,
        "peak_phase": "action_replay"
      },
      "right_hand_thumb_2_link / table": {
        "peak_force_n": 5.802289551905277,
        "observed_control_samples": 1136,
        "peak_time_s": 156.46,
        "peak_phase": "action_replay"
      },
      "right_hand_thumb_1_link / disk": {
        "peak_force_n": 4.647140139012461,
        "observed_control_samples": 11441,
        "peak_time_s": 201.6,
        "peak_phase": "action_replay"
      },
      "left_hand_thumb_1_link / disk": {
        "peak_force_n": 3.906368886205962,
        "observed_control_samples": 2475,
        "peak_time_s": 194.86,
        "peak_phase": "action_replay"
      },
      "left_hand_index_1_link / disk": {
        "peak_force_n": 2.95199398578386,
        "observed_control_samples": 2862,
        "peak_time_s": 164.3,
        "peak_phase": "action_replay"
      },
      "right_wrist_yaw_link / disk": {
        "peak_force_n": 3.667678138720162,
        "observed_control_samples": 8198,
        "peak_time_s": 269.98,
        "peak_phase": "action_replay"
      },
      "torso_link / disk": {
        "peak_force_n": 1.9254153157776035,
        "observed_control_samples": 463,
        "peak_time_s": 282.62,
        "peak_phase": "action_replay"
      },
      "right_hand_thumb_2_link / disk": {
        "peak_force_n": 2.7632462640335302,
        "observed_control_samples": 3974,
        "peak_time_s": 370.64,
        "peak_phase": "action_replay"
      },
      "right_hand_middle_0_link / disk": {
        "peak_force_n": 0.2913073710629839,
        "observed_control_samples": 76,
        "peak_time_s": 399.78000000000003,
        "peak_phase": "action_replay"
      }
    }
  }
}
```

## 配置／见证 offset_y_003

[完整分层映射与生成来源](../../humanoid/g1_tabletop_disk_flip/validation/hierarchical/offset_y_003.json)。下面的轨迹段来自同一连续记录；准备与上下文段也保留。

| 高层目标 | 低层段 | 实测完成条件 |
| --- | --- | --- |
| slide · 轻推到桌边 | ["L01", "L02", "L03", "L04", "L05"] | ["at_edge"] |
| clamp · 建立双手独立夹持 | ["L06", "L07", "L08", "L09", "L10", "L11"] | ["bimanual_clamp"] |
| lift · 双手抬起并建立翻转净空 | ["L12"] | ["bimanual_clamp", "clear"] |
| turn · 双手翻面至蓝面朝上 | ["L13", "L14"] | ["bimanual_clamp", "clear", "inverted"] |
| place · 放回桌面并释放稳定 | ["L15", "L16", "L17", "L18", "L19", "L20", "L21", "L22", "L23", "L24", "L25", "L26", "L27"] | ["inverted", "placed", "released", "still", "in_goal"] |

| 低层段 | 动作 | 约束／支撑 | 时间 s | 命令切片 |
| --- | --- | --- | --- | --- |
| L01 | 稳定抬起且分开的双手 | 盘由桌面支撑；双手先稳定 | [0.0, 4.5] | [0, 225] |
| L02 | 拇指从上方接近远侧盘沿 | 接近阶段避免提前碰盘 | [4.5, 12.5] | [225, 625] |
| L03 | 在远侧盘沿外降低拇指 | 沿盘外侧下降，保留桌面支撑 | [12.5, 20.5] | [625, 1025] |
| L04 | 低速建立拇指推盘接触 | 以测得接触建立推力，限制速度与受力 | [20.5, 31.88] | [1025, 1594] |
| L05 | 沿桌面轻推至近侧桌沿 | 按实测悬伸量停止，盘心仍在支撑侧 | [31.88, 64.34] | [1594, 3217] |
| L06 | 卸掉原推盘拇指的载荷 | 先卸力，再撤离；桌面继续承载 | [64.34, 69.84] | [3217, 3492] |
| L07 | 撤开推盘拇指 | 从盘沿退出，避免带动圆盘 | [69.84, 75.84] | [3492, 3792] |
| L08 | 双手撤至盘上方和侧方 | 为改变手型预留几何空间 | [75.84, 91.84] | [3792, 4592] |
| L09 | 调整腕部姿态以双手接近 | 局部 IK 使用关节范围和腕部间隙约束 | [91.84, 107.84] | [4592, 5392] |
| L10 | 预张开并调整空载手指 | 空载预整形后再建立盘面接触 | [107.84, 130.9] | [5392, 6545] |
| L11 | 分别闭合两手的拇指与下侧手指 | 每只手建立两盘面的独立夹持；按接触力臂分配载荷 | [130.9, 161.88] | [6545, 8094] |
| L12 | 保持双手夹持共同抬盘 | 保持双手支撑；夹持丢失不得超过 0.1 s；建立旋转净空 | [161.88, 173.24] | [8094, 8662] |
| L13 | 同步旋转两手以翻转圆盘 | 双手夹持，腕部间隙、姿态和切向载荷反馈；保留全局限值 | [173.24, 222.84] | [8662, 11142] |
| L14 | 接近翻面完成时改用实测压力反馈 | 仅在已接近反面朝上且双手夹持有效时触发；原物理约束不变 | [222.84, 223.28] | [11142, 11164] |
| L15 | 翻面后先稳定双手夹持 | 蓝面朝上，准备受控支撑交接 | [223.28, 233.3] | [11164, 11665] |
| L16 | 将载荷移交右手夹持并释放左手 | 此交接只发生在双手翻面完成后；保持圆盘受支撑 | [233.3, 241.92000000000002] | [11665, 12096] |
| L17 | 移开左手并准备再次推盘 | 右手承载，左手从盘体附近移开 | [241.92000000000002, 257.92] | [12096, 12896] |
| L18 | 右手将反面朝上的盘移至桌沿外侧 | 保持姿态与右手支撑，避免下侧手指被桌沿夹住 | [257.92, 277.92] | [12896, 13896] |
| L19 | 在桌沿外降低右手及圆盘 | 盘与承载手在桌沿外下降 | [277.92, 302.92] | [13896, 15146] |
| L20 | 对齐圆盘与桌面高度 | 按测量高度调整，继续由右手支撑 | [302.92, 307.26] | [15146, 15363] |
| L21 | 左手拇指从上方接近近侧盘沿 | 右手承载期间保持推盘手净空 | [307.26, 325.26] | [15363, 16263] |
| L22 | 在近侧盘沿外降低左手拇指 | 沿盘外侧下降至推盘高度 | [325.26, 337.26] | [16263, 16863] |
| L23 | 建立左手拇指与盘沿的轻柔接触 | 右手继续承载，左手低速寻找接触 | [337.26, 347.26] | [16863, 17363] |
| L24 | 将圆盘从承载手推向桌面 | 逐渐建立桌面支撑并打开右拇指；控制合力和姿态 | [347.26, 420.44] | [17363, 21022] |
| L25 | 核对桌面与下侧指垫共同承载 | 明确记录支撑交接控制步，不将它省略成瞬时跳转 | [420.44, 420.46000000000004] | [21022, 21023] |
| L26 | 盘心获得桌面支撑后撤出下侧指垫并继续推盘 | 撤指时暂停推进；左拇指维持桌面盘沿高度，避免撬起圆盘 | [420.46000000000004, 475.66] | [21023, 23783] |
| L27 | 卸去左拇指推力并松手稳定 | 完整位于桌内、蓝面朝上、目标内、无机器人接触并静止两秒 | [475.66, 478.925] | [23783, 23947] |

### 已记录检查

```json
{
  "command_count": 23947,
  "low_level_segment_count": 27,
  "continuous": true,
  "no_gaps_or_overlap": true,
  "no_checkpoint_splicing": true,
  "physical_peaks_400hz": {
    "linear_speed_m_s": 0.05104231889686313,
    "angular_speed_rad_s": 0.6030108755178154,
    "robot_force_n": 16.766354319961327,
    "table_force_n": 3.343011442995499
  },
  "physical_limits": {
    "linear_speed_m_s": 0.12,
    "angular_speed_rad_s": 0.65,
    "robot_force_n": 18.0,
    "table_force_n": 8.0
  },
  "actuator_checks": {
    "effort_limits_passed": true,
    "target_speed_limit_passed": true,
    "target_speed_peak_rad_s": 0.4999999888241291,
    "applied_torque_peak_nm": [
      2.0690017060357175,
      0.056780331556625034,
      0.012653278890901032,
      0.7556413675004154,
      0.15013687503585563,
      5.6480547949385065e-05,
      2.069001705479293,
      0.05678033155494784,
      0.012653605849184714,
      0.7556413876507682,
      0.15013687503585837,
      5.648054779929215e-05,
      2.5115925219771325,
      17.162018211741266,
      32.079982175381346,
      10.661284028707081,
      6.4788633405347325,
      3.78234334327466,
      4.463334259704499,
      1.2739458145708755,
      1.4853265043691377,
      1.1183345063380437,
      0.32000816701699825,
      0.5036660005793727,
      0.3345294047516482,
      0.46959402588426763,
      0.312625166965821,
      0.39321617046913104,
      0.3126251884788722,
      10.661280823313312,
      4.669665288448126,
      3.8964241468237093,
      4.463319390788369,
      1.6406858691461186,
      1.4853200720695428,
      1.320064524216209,
      0.3097883160656648,
      0.6310963238171868,
      0.35643996394310684,
      0.51729455916932,
      0.3166606552409599,
      0.41019618604608243,
      0.31666067610172904
    ],
    "effort_limit_nm": [
      88.0,
      139.0,
      88.0,
      139.0,
      50.0,
      50.0,
      88.0,
      139.0,
      88.0,
      139.0,
      50.0,
      50.0,
      88.0,
      50.0,
      50.0,
      25.0,
      25.0,
      25.0,
      25.0,
      25.0,
      5.0,
      5.0,
      2.450000047683716,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      25.0,
      25.0,
      25.0,
      25.0,
      25.0,
      5.0,
      5.0,
      2.450000047683716,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142,
      1.399999976158142
    ]
  },
  "robot_self_contact_observations_50hz": {
    "sampling_hz": 50,
    "threshold_n": 0.1,
    "scope": "control-boundary observations only; not substep collision certification",
    "pairs": {
      "left_hand_middle_1_link / right_hand_middle_1_link": {
        "peak_force_n": 1.3952860804964393,
        "observed_control_samples": 525
      },
      "left_hand_middle_1_link / right_hand_index_1_link": {
        "peak_force_n": 0.231317523042236,
        "observed_control_samples": 113
      },
      "left_hand_index_1_link / right_hand_index_1_link": {
        "peak_force_n": 2.5348969199802713,
        "observed_control_samples": 1626
      },
      "left_wrist_yaw_link / torso_link": {
        "peak_force_n": 2.0206867698281306,
        "observed_control_samples": 45
      }
    }
  },
  "robot_environment_contact_observations_50hz": {
    "sampling_hz": 50,
    "threshold_n": 0.1,
    "scope": "control-boundary observations only; not substep collision certification",
    "pairs": {
      "right_wrist_yaw_link / table": {
        "peak_force_n": 4.392603925879463,
        "observed_control_samples": 67,
        "peak_time_s": 8.48,
        "peak_phase": "action_replay"
      },
      "left_hand_thumb_2_link / disk": {
        "peak_force_n": 5.375143885609008,
        "observed_control_samples": 11179,
        "peak_time_s": 375.8,
        "peak_phase": "action_replay"
      },
      "left_hand_thumb_2_link / table": {
        "peak_force_n": 2.752109799281713,
        "observed_control_samples": 209,
        "peak_time_s": 65.7,
        "peak_phase": "action_replay"
      },
      "right_hand_middle_1_link / disk": {
        "peak_force_n": 5.303524378577156,
        "observed_control_samples": 8919,
        "peak_time_s": 412.66,
        "peak_phase": "action_replay"
      },
      "left_hand_middle_1_link / disk": {
        "peak_force_n": 3.1119527160417766,
        "observed_control_samples": 4716,
        "peak_time_s": 222.76,
        "peak_phase": "action_replay"
      },
      "right_hand_index_1_link / disk": {
        "peak_force_n": 2.866347833244986,
        "observed_control_samples": 11209,
        "peak_time_s": 194.28,
        "peak_phase": "action_replay"
      },
      "right_hand_thumb_2_link / table": {
        "peak_force_n": 5.98975296239666,
        "observed_control_samples": 1170,
        "peak_time_s": 156.52,
        "peak_phase": "action_replay"
      },
      "right_hand_thumb_1_link / disk": {
        "peak_force_n": 4.638388751533241,
        "observed_control_samples": 10786,
        "peak_time_s": 164.48,
        "peak_phase": "action_replay"
      },
      "left_hand_thumb_1_link / disk": {
        "peak_force_n": 3.8844955793702827,
        "observed_control_samples": 2534,
        "peak_time_s": 195.28,
        "peak_phase": "action_replay"
      },
      "left_hand_index_1_link / disk": {
        "peak_force_n": 3.1322320361989684,
        "observed_control_samples": 2762,
        "peak_time_s": 164.76,
        "peak_phase": "action_replay"
      },
      "right_wrist_yaw_link / disk": {
        "peak_force_n": 4.007273696142687,
        "observed_control_samples": 8820,
        "peak_time_s": 272.62,
        "peak_phase": "action_replay"
      },
      "torso_link / disk": {
        "peak_force_n": 2.6467398548551264,
        "observed_control_samples": 618,
        "peak_time_s": 283.12,
        "peak_phase": "action_replay"
      },
      "right_hand_thumb_2_link / disk": {
        "peak_force_n": 2.363425025202438,
        "observed_control_samples": 3592,
        "peak_time_s": 378.40000000000003,
        "peak_phase": "action_replay"
      },
      "right_hand_middle_0_link / disk": {
        "peak_force_n": 0.7366777513505652,
        "observed_control_samples": 51,
        "peak_time_s": 413.04,
        "peak_phase": "action_replay"
      }
    }
  }
}
```

## 尚需核对

人工录像签审、第二人复现、更多配置与完整自碰撞/环境接触审阅；无通用随机域或移动全身能力声明。

## 复现与生成入口

- [humanoid/g1_tabletop_disk_flip/README.md](../../humanoid/g1_tabletop_disk_flip/README.md)
- [humanoid/g1_tabletop_disk_flip/solution/README.md](../../humanoid/g1_tabletop_disk_flip/solution/README.md)

[完整参考包](https://huggingface.co/datasets/IntelligenceLab/robo-si/resolve/39845e9f4f8bfd300059b49cffa1b8bddc667ddc/releases/g1-disk-flip/0.1.0-rc1-hierarchical/g1-disk-flip-0.1.0-rc1-hierarchical.tar.gz)。使用包内冻结配置、依赖说明与生成／回放入口；审阅包不替代完整包。

历史源码说明只提供设计上下文；若与冻结见证冲突，以见证的配置、控制器身份和发布清单为准。设计动作表不等同于已绑定的通用控制器。

## 验收与执行边界

本文件说明已有参考的设计与证据，不修改旧评分。任务级要求至少一个声明配置内的连续端到端生成见证；高层计划→低层动作、低层动作→轨迹、高层目标→实测终态分别核对。这里的“两两转换”是表示之间的对应，不是任意随机状态下技能可无条件拼接。

随机实例保留四种结果：有完整成功证据、通过可行性筛查、未确定、检查不通过；筛查通过不写成已证明可解。只在需要执行时生成当前局部轨迹；通用滚动规划和全随机域鲁棒性另列，不是本参考文档的完成前提。

若接触、支撑或守卫条件不满足，不推进下一动作；保留已有安全支撑并记录失败，仅在已知安全状态下重新观察与局部规划。不得凭事件名推断接触合格，不得将不同检查点的成功片段拼接成连续成功。

## 来源与版本

来源内容哈希见 [catalog.json](catalog.json)，对应生成器为 [build_reference_designs.py](../tools/build_reference_designs.py)。本次只整理设计与证据，不将待审事件关联计作验收通过。
