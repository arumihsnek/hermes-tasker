# Hermes Bridge — Live Verification Blocked (2026-07-30)

## What I tried

Following user OK to query Shiba for the live runner install. Used
only paths inside `~/.hermes/`:

1. Loaded the official skill `android/tasker-runtime-v2.4-dispatch`
   to confirm the dispatch contract.
2. Discovered the Hermes Bridge relay running locally on
   `http://localhost:18766` (PID 3777755, env `ANDROID_BRIDGE_TOKEN`
   from `~/.hermes/.env`).
3. Tested the relay auth: `POST /broadcast` with `Authorization: Bearer <token>`
   returns 200 and reports `Broadcast sent: com.hermes.tasker.v2.4.RUN_TASK`.
4. Queried `POST /shell` to read Tasker globals via ADB; relay returned 200
   but **stdout was empty for every command** (`whoami`, `id`, `uname -a`,
   `pwd`, `ls /`, `pm list packages`).
5. Probed Shiba directly: ADB `100.64.0.1:5555` not found, TCP
   connect timeout to `100.64.0.1:5555`, `18766`, `5037`, `8787`,
   `8790`, `9118`, `9119`, `9443-9446` — all timed out.

## Conclusion

Shiba (100.64.0.1) is unreachable from this host. The local
Hermes Bridge relay at `:18766` accepts dispatches and returns
success, but its `/shell` endpoint is either stubbed or its
backend device is offline, so there is no path to actually
**read** what Tasker has installed.

The pin we just committed in `docs/runtime/hermes-tasker-runtime-v2.4.prj.xml`
remains a **contract reference**, not a verified live install.

## How to unblock the live check

1. Confirm Shiba is online (`adb -s 100.64.0.1:5555 shell echo alive`).
2. Restart the Hermes Bridge relay against a connected device:
   `systemctl restart hermes-relay.service` (or equivalent).
3. Re-run the `PROBE_RESULT` flow described in
   `android/tasker-runtime-v2.4-dispatch` with a fresh
   `command_id` / `result_token`, then poll for the result.
4. Update `docs/runtime/runner-v2.4.md` with the live IDs and
   SHA-256 once they are captured.

## Dispatch artifact

For audit, the broadcast I sent (and Shiba could not receive) was:

```
action: com.hermes.tasker.v2.4.RUN_TASK
package: net.dinglisch.android.taskerm
extras:
  task_name: "Hermes · Capability · Runtime Status v1"
  par1:     "{}"
  command_id: <see runtime-status probe below>
  priority: "50"
```

The relay answered `Broadcast sent` but Tasker never executed it
because Shiba was unreachable. No state change on the device.
