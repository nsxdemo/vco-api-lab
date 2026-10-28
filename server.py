#!/usr/bin/env python3
"""
VeloCloud Modular Web Dashboard

Serves a web portal with independent modules for querying
VeloCloud Orchestrator APIs. Each module runs standalone.

Usage:
    python3 server.py [--port PORT]
"""
import http.server
import json
import os
import sys
import argparse
import requests

from modules.base import VCOClient
from modules import edges, topapps, routetable

MODULES = {
    "edges": edges,
    "topapps": topapps,
    "routetable": routetable,
}


class VCOHandler(http.server.SimpleHTTPRequestHandler):

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {fmt % args}\n")

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Expires", "0")
        super().end_headers()

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length))

    def _json_response(self, code, obj):
        body = json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _make_vco(self, params):
        return VCOClient(
            host=params.get("vco_url", ""),
            token=params.get("token", ""),
            verify_ssl=params.get("verify_ssl", True),
        )

    def do_POST(self):
        try:
            params = self._read_json()
        except (json.JSONDecodeError, ValueError) as exc:
            self._json_response(400, {"success": False, "errors": [str(exc)]})
            return

        if self.path == "/api/connect":
            self._handle_connect(params)
        elif self.path.startswith("/api/run/"):
            module_id = self.path[len("/api/run/"):]
            self._handle_module(module_id, params)
        else:
            self.send_error(404)

    def _handle_connect(self, params):
        vco = self._make_vco(params)
        try:
            data, _req = vco.rest_post("enterprise/getEnterprise", {})
            if isinstance(data, list):
                data = data[0] if data else {}
            eid = data.get("id")
            if not eid:
                self._json_response(200, {
                    "success": False,
                    "errors": ["Could not determine Enterprise ID from API response."],
                })
                return
            self._json_response(200, {
                "success": True,
                "errors": [],
                "enterprise": {
                    "id": eid,
                    "name": data.get("name", ""),
                    "accountNumber": data.get("accountNumber", ""),
                },
                "base_url": vco.rest_url,
            })
        except requests.exceptions.SSLError as exc:
            self._json_response(200, {"success": False, "errors": [
                f"SSL verification failed - try unchecking 'Verify SSL': {exc}"]})
        except requests.exceptions.ConnectionError as exc:
            self._json_response(200, {"success": False, "errors": [
                f"Connection failed - check the VCO hostname: {exc}"]})
        except requests.exceptions.HTTPError as exc:
            body = exc.response.text[:500] if exc.response is not None else ""
            self._json_response(200, {"success": False, "errors": [
                f"HTTP {exc.response.status_code}: {body}"]})
        except Exception as exc:
            self._json_response(200, {"success": False, "errors": [str(exc)]})

    def _handle_module(self, module_id, params):
        mod = MODULES.get(module_id)
        if not mod:
            self._json_response(404, {"success": False, "errors": [f"Unknown module: {module_id}"]})
            return

        eid = params.get("eid")
        if not eid:
            self._json_response(400, {"success": False, "errors": ["Enterprise ID required. Connect first."]})
            return

        vco = self._make_vco(params)
        result = mod.run(vco, int(eid), params)
        self._json_response(200, result)


def main():
    ap = argparse.ArgumentParser(description="VeloCloud Modular Web Dashboard")
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = http.server.ThreadingHTTPServer(("0.0.0.0", args.port), VCOHandler)
    print(f"VeloCloud Dashboard  ->  http://localhost:{args.port}")
    print(f"Modules: {', '.join(MODULES.keys())}")
    print("Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
