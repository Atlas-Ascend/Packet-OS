from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__


CAPABILITIES = {
    "owns": ["packet-schema", "task-state-contract", "handoff-envelope", "evidence-requirements", "packet-event-contract"],
    "does_not_own": ["executive-authorization", "worker-selection", "capability-routing", "finish-truth"],
    "verification_authority": "SECA",
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._json(200, {"status": "ok", "service": "packet-os", "version": __version__})
        elif self.path == "/capabilities":
            self._json(200, CAPABILITIES)
        else:
            self._json(404, {"error": "not_found"})

    def log_message(self, format: str, *args) -> None:
        return

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
