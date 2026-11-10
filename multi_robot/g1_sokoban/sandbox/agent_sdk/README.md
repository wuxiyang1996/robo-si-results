# Per-robot Sokoban agent

Each container authenticates as one robot. No API selects another identity.
Use `g1sandbox.RobotClient` for info/status/observe/finish. Observation returns
only own RGB, own joints and body-frame inertial values, own goal color and inbox.

Submit `client.command({'q': targets}, steps=1)`. Both agents must submit one
target before the shared world steps. Poll `status()` until `steps` advances
before submitting another target; duplicate pending submissions are rejected.

Send explicit messages with
`client._call('send_message', recipient='g1_b', text='...')` (swap peer for B).
The trusted worker enforces 256 UTF-8 bytes and 16 pending messages. There is no
shared filesystem, shared map, scorer feedback, object state or world setter.

Full push-only task validity remains separate from interface validation; the
trusted report withholds a task score rather than treating arrival alone as success.
