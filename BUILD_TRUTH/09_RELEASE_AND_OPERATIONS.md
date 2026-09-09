# BUILD TRUTH 09 — Release and Operations

## Candidate release

Version: `0.1.0`  
Lifecycle: `active-candidate`

## CI gate

Pull requests and main pushes run compile, unit tests, CLI demo, and Docker build.

## Runtime

Default HTTP port is `$PORT` or `8080`. Endpoints:

- `GET /healthz` — liveness and version
- `GET /capabilities` — declared Packet OS ownership/non-ownership

The v0.1 service is stateless/ephemeral by design. Durable packet execution must wait for the estate event/persistence adapter.

## Promotion sequence

`candidate branch -> CI -> PR review -> SECA gate -> merge -> deployment adapter -> runtime observation -> release receipt`.

Rollback is a Git revert/redeploy to the prior verified commit; no destructive data migration exists in v0.1.
