# SDLC Control

This repository follows the Ghost Atlas command-to-proof SDLC:

`canon -> requirements -> architecture -> contracts -> implementation -> test -> CI -> SECA gate -> merge -> deploy -> observe -> receipt`.

## Definition of done

- Build Truth 00-09 present and internally consistent.
- Core package imports under Python 3.11+.
- Automated unit tests pass.
- CLI demo proves the governed happy path.
- Docker image builds.
- Estate wiring references canonical existing repositories.
- CI result is attached to candidate commit.
- SECA checklist is satisfied before production promotion.

## Change discipline

No replacement build by default. Extend contracts additively, version breaking changes, preserve provenance, and never silently move authority boundaries.
