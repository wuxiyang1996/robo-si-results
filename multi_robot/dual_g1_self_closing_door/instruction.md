# Dual G1 delivery through a self-closing door

You control two G1 robots, both starting in room A. Move the small parcel from its stand in A through the self-closing doorway into B. Place it on the target table and release it so it remains stable for at least 2 seconds. The parcel must be carried clear of fixed supports while crossing the doorway.

The episode has a shared 180-second simulation budget. Keep both robots within the room, posture, collision and hardware limits throughout. Both robots remain active in the same physical scene.

The `heavy_prop` variant includes a movable 12 kg crate in B in addition to the parcel. The `no_prop` variant contains only the parcel. Neither variant contains a wedge or light distractor. You may interact with the available objects. The final delivery goal is the same for both variants.

This goal description accompanies the native reference release. The isolated agent interface is not yet published.
