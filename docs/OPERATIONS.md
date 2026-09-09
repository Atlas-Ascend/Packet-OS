# Operations

## Local run

```bash
python -m pip install -e .
python -m packet_os.httpd
```

`PORT` defaults to `8080`.

## Health

`GET /healthz` returns service/version. `GET /capabilities` returns the authority boundary declaration.

## Deployment profile

The included Dockerfile is stateless and does not require secrets. A production deployment should sit behind the estate service mesh/event gateway and use an external durable event store.

## Failure routing

- state/implementation defect: DEVOS
- quality/acceptance/evidence defect: SECA
- worker/schedule issue: Workforce Spine
- capability route issue: CrownGrid
- connectivity/event delivery issue: Estate Event Gateway/service mesh

## Rollback

Revert/redeploy the last verified Git SHA. v0.1 performs no database migration and therefore has no destructive rollback step.
