#!/usr/bin/env python3
"""OnePal Minimum API Server - Task 06

Local HTTP API control plane. Binds to 127.0.0.1 only.
Provides read-only access to health, tasks, task-trees, task-runs, mas-trace,
and a POST /command endpoint that delegates to command_gateway.py.

Does NOT: execute actions, bypass governance, read secrets, expose files.

Usage:
    py scripts/api_server.py --host 127.0.0.1 --port 18790
"""

import argparse
import json
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Allowed read paths (whitelist — no arbitrary file access)
HEALTH_PATH = PROJECT_ROOT / "runtime" / "health_status.json"
TASKS_PATH = PROJECT_ROOT / "runtime" / "tasks" / "tasks.jsonl"
TREES_PATH = PROJECT_ROOT / "runtime" / "tasks" / "task_trees.jsonl"
TASK_RUNS_PATH = PROJECT_ROOT / "runtime" / "task_runs" / "task_runs.jsonl"
MAS_TRACE_PATH = PROJECT_ROOT / "logs" / "mas_trace.jsonl"
COMMAND_GATEWAY = PROJECT_ROOT / "scripts" / "command_gateway.py"

MAX_LIMIT = 100
MAX_COMMAND_LENGTH = 2000

ALLOWED_HOSTS = {"127.0.0.1", "localhost"}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path, limit=20):
    """Read latest N JSON lines from a JSONL file. Returns list, skipped_count."""
    results = []
    skipped = 0
    limit = min(int(limit), MAX_LIMIT)

    if not path.exists():
        return [], 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return [], 0

    # Take latest N lines
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            skipped += 1

    return results, skipped


def build_response(ok, data=None, error=None, meta_extra=None):
    """Unified JSON response format."""
    meta = {"timestamp": now_iso()}
    if meta_extra:
        meta.update(meta_extra)
    return {
        "ok": ok,
        "data": data if data is not None else {},
        "error": error,
        "meta": meta,
    }


def handle_health(health_path):
    """GET /health handler."""
    if health_path.exists():
        try:
            with open(health_path, "r", encoding="utf-8") as f:
                health_data = json.load(f)
            return build_response(True, data={
                "status": health_data.get("status", "unknown"),
                "source": "runtime/health_status.json",
                "exists": True,
                "last_updated": health_data.get("checked_at"),
            })
        except (json.JSONDecodeError, OSError):
            return build_response(True, data={
                "status": "limited",
                "source": "runtime/health_status.json",
                "exists": True,
                "note": "file exists but could not be parsed",
            })
    else:
        return build_response(True, data={
            "status": "limited",
            "source": "none",
            "exists": False,
            "note": "health_status.json not found",
        })


def handle_tasks(tasks_path, limit):
    """GET /tasks handler."""
    results, skipped = read_jsonl(tasks_path, limit)
    return build_response(True, data={"tasks": results}, meta_extra={
        "total": len(results),
        "skipped": skipped,
        "limit": limit,
        "source": "runtime/tasks/tasks.jsonl",
    })


def handle_task_trees(trees_path, limit):
    """GET /task-trees handler."""
    results, skipped = read_jsonl(trees_path, limit)
    return build_response(True, data={"task_trees": results}, meta_extra={
        "total": len(results),
        "skipped": skipped,
        "limit": limit,
        "source": "runtime/tasks/task_trees.jsonl",
    })


def _safe_source(path, default="file"):
    """Return a safe source string for a path, or default if outside project."""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return default


def handle_task_runs(path, limit):
    """GET /task-runs handler."""
    results, skipped = read_jsonl(path, limit)
    source = _safe_source(path, "none") if path.exists() else "none"
    return build_response(True, data={"task_runs": results}, meta_extra={
        "total": len(results),
        "skipped": skipped,
        "limit": limit,
        "source": source,
    })


def handle_mas_trace(path, limit):
    """GET /mas-trace handler."""
    results, skipped = read_jsonl(path, limit)
    return build_response(True, data={"mas_trace": results}, meta_extra={
        "total": len(results),
        "skipped": skipped,
        "limit": limit,
        "source": "logs/mas_trace.jsonl",
    })


def handle_command(body, gateway_path):
    """POST /command handler. Delegates to command_gateway.py via subprocess."""
    command_text = (body or "").strip()

    if not command_text:
        return build_response(False, error={
            "code": "EMPTY_COMMAND",
            "message": "command must not be empty",
        })

    if len(command_text) > MAX_COMMAND_LENGTH:
        return build_response(False, error={
            "code": "COMMAND_TOO_LONG",
            "message": f"command must be <= {MAX_COMMAND_LENGTH} characters",
        })

    # Subprocess delegation — no shell=True
    try:
        result = subprocess.run(
            ["py", str(gateway_path), "--command", command_text],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return build_response(False, error={
            "code": "GATEWAY_TIMEOUT",
            "message": "command_gateway.py timed out",
        })

    try:
        gateway_output = json.loads(result.stdout.strip()) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        gateway_output = {"raw_stdout": (result.stdout or "")[:500]}

    return build_response(True, data={
        "gateway_result": gateway_output,
        "gateway_exit_code": result.returncode,
    })


class OnePalHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OnePal API."""

    # Paths overrideable for testing
    health_path = HEALTH_PATH
    tasks_path = TASKS_PATH
    trees_path = TREES_PATH
    task_runs_path = TASK_RUNS_PATH
    mas_trace_path = MAS_TRACE_PATH
    gateway_path = COMMAND_GATEWAY

    def _send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_query_limit(self):
        """Extract ?limit=N from query string."""
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        try:
            limit = int(qs.get("limit", [20])[0])
            limit = min(max(limit, 1), MAX_LIMIT)
        except (ValueError, TypeError):
            limit = 20
        return limit, parsed.path

    def do_GET(self):
        path = urlparse(self.path).path
        limit, _ = self._parse_query_limit()

        try:
            if path == "/health":
                resp = handle_health(self.health_path)
                self._send_json(200, resp)

            elif path == "/tasks":
                resp = handle_tasks(self.tasks_path, limit)
                self._send_json(200, resp)

            elif path == "/task-trees":
                resp = handle_task_trees(self.trees_path, limit)
                self._send_json(200, resp)

            elif path == "/task-runs":
                resp = handle_task_runs(self.task_runs_path, limit)
                self._send_json(200, resp)

            elif path == "/mas-trace":
                resp = handle_mas_trace(self.mas_trace_path, limit)
                self._send_json(200, resp)

            else:
                self._send_json(404, build_response(False, error={
                    "code": "NOT_FOUND",
                    "message": f"route not found: {path}",
                }))
        except Exception:
            self._send_json(500, build_response(False, error={
                "code": "INTERNAL_ERROR",
                "message": traceback.format_exc()[:500],
            }))

    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/command":
            self._send_json(404, build_response(False, error={
                "code": "NOT_FOUND",
                "message": f"POST route not found: {path}",
            }))
            return

        # Read body
        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            body_json = json.loads(body_raw.decode("utf-8"))
            command_text = body_json.get("command", "")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, build_response(False, error={
                "code": "INVALID_JSON",
                "message": "request body must be valid JSON",
            }))
            return

        try:
            resp = handle_command(command_text, self.gateway_path)
            self._send_json(200, resp)
        except Exception:
            self._send_json(500, build_response(False, error={
                "code": "INTERNAL_ERROR",
                "message": traceback.format_exc()[:500],
            }))

    def log_message(self, format, *args):
        """Suppress default stderr logging in tests."""
        pass


def create_server(host, port, handler_class=OnePalHandler):
    """Create and return an HTTPServer instance."""
    server = HTTPServer((host, port), handler_class)
    return server


def main():
    parser = argparse.ArgumentParser(description="OnePal Minimum API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=18790, help="Port to bind")
    parser.add_argument("--health-path", default=None, help="Override health_status.json path")
    parser.add_argument("--tasks-path", default=None, help="Override tasks.jsonl path")
    parser.add_argument("--trees-path", default=None, help="Override task_trees.jsonl path")
    parser.add_argument("--task-runs-path", default=None, help="Override task_runs.jsonl path")
    parser.add_argument("--mas-trace-path", default=None, help="Override mas_trace.jsonl path")
    parser.add_argument("--gateway-path", default=None, help="Override command_gateway.py path")
    args = parser.parse_args()

    host = args.host.strip().lower()

    # Reject 0.0.0.0
    if host == "0.0.0.0":
        print(json.dumps({
            "error": "Binding to 0.0.0.0 is forbidden. Use 127.0.0.1 or localhost."
        }, ensure_ascii=False))
        sys.exit(1)

    if host not in ALLOWED_HOSTS:
        print(json.dumps({
            "error": f"Host '{host}' is not allowed. Use 127.0.0.1 or localhost."
        }, ensure_ascii=False))
        sys.exit(1)

    # Build handler class with path overrides
    class ConfiguredHandler(OnePalHandler):
        health_path = Path(args.health_path) if args.health_path else HEALTH_PATH
        tasks_path = Path(args.tasks_path) if args.tasks_path else TASKS_PATH
        trees_path = Path(args.trees_path) if args.trees_path else TREES_PATH
        task_runs_path = Path(args.task_runs_path) if args.task_runs_path else TASK_RUNS_PATH
        mas_trace_path = Path(args.mas_trace_path) if args.mas_trace_path else MAS_TRACE_PATH
        gateway_path = Path(args.gateway_path) if args.gateway_path else COMMAND_GATEWAY

    server = create_server(host, args.port, ConfiguredHandler)
    print(f"OnePal API Server listening on http://{host}:{args.port}")
    print("Endpoints: GET /health /tasks /task-trees /task-runs /mas-trace  POST /command")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
