# Fleetbase v0.7.75 — isolated registration timing diagnostic

Branch: `diagnostics/v075-registration-timing`

## Scope
Only `api/app/Providers/AppServiceProvider.php` is instrumented. The diagnostic is disabled by default and restricted to requests whose path is `int/v1/onboard/create-account`.

## Activation (not performed)
1. Review and build a **new staging-only API image** containing this branch's source. The existing Render image is digest-pinned, so changing this branch alone cannot change the running application.
2. On the staging service only, set `REGISTRATION_TIMING_DIAGNOSTIC_ENABLED=true` and redeploy the newly built image.
3. Use a single controlled test registration after confirming the diagnostic logs `[registration:timing:start]`. Stop if it does not appear.
4. Collect `[registration:timing:query]`, `[registration:timing:finish]`, and the fatal error. Never post tokens, passwords, request bodies, or SQL bindings.
5. Turn the flag off and revert the staging image to the last verified digest after investigation.

## What the logs mean
- `start`: handler path was recognized and instrumentation armed.
- `query`: one **completed** SQL operation; shows ordinal, connection name, and timing, but not SQL or values.
- `finish`: Laravel emitted the request-handled event; may be absent on fatal timeout.
- The last completed query is **not proof** of the blocked query. A hanging SQL call does not emit a `QueryExecuted` event.
- If no query logs appear, investigate an operation before the first completed query or whether the diagnostic is installed and enabled.

## Safety
- No schema changes, SQL writes, user account creation, or Render changes are made by this branch.
- The diagnostic itself emits only timing and route metadata; other existing application logs remain subject to their own policies.
- The diagnostic does not isolate the exact PHP source statement. Further controller-level tracing may be required.
