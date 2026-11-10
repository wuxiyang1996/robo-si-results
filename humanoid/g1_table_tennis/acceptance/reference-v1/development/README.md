# Retained development history

These attempts precede the frozen reference cohort and do not contribute to its success rate. Each directory retains its own source snapshot, configuration, outcome and artifact hashes.

- dev001–dev004: candidate kinematic/trajectory-limit rejections. Early G1 intercept geometry approached arm extension; the final design uses x=-1.20 m and a different elbow posture.
- dev005: diagnostic 1 ms physics run with enlarged command limits; ball landed in target but the inherited UR10e speed limit failed. Not a full success.
- dev006: 0.5 ms physics, G1-specific simulation motion limits; legal target return scored 85, but wrist recovery missed the declared ready tolerance.
- dev007: increased upper-body feedback gains overcame joint friction; full success at 100 points. The subsequent frozen campaign includes the final formatted source, independent audits, controls and torque replays.

The final declared G1 thresholds are 6 rad/s measured/commanded joint speed, 120 rad/s² commanded acceleration, original model motor effort bounds and 0.035 rad terminal ready tolerance. They are simulation task limits and do not certify hardware operation. Development runs are not silently relabeled under later thresholds.
