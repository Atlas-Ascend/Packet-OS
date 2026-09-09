# BUILD TRUTH 08 — Verification and Evidence

## Required candidate evidence

- unit-test pass
- Python compile/import pass
- CLI demo reaches `COMPLETED`
- missing evidence blocks verification
- non-SECA verification is rejected
- illegal state transition is rejected
- Docker image builds
- schema and wiring files present

## Evidence classes

- **E1 source** — committed implementation/configuration
- **E2 test** — executable automated checks
- **E3 runtime** — demo/health output
- **E4 CI** — GitHub Actions result attached to candidate commit
- **E5 audit** — SECA checklist/result

## Finish rule

A green CI run is necessary but not synonymous with estate finish truth. The final promotion gate remains SECA.
