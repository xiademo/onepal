#!/usr/bin/env python3
"""Local-only tests for OnePal's remote model provider boundary."""

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import model_provider as provider
from scripts.api_server import handle_model_provider_get, handle_model_provider_post


passed = 0
failed = 0


def test(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: {detail}")


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def config():
    return {
        "base_url": "https://provider.example/v1",
        "model": "proposal-model",
        "api_key": "sk-test-private-key-1234567890",
        "input_price_per_million": 2.0,
        "output_price_per_million": 8.0,
        "monthly_budget_usd": 5.0,
    }


def test_validation_and_redaction(tmpdir):
    print("\n--- P1: validation and redaction ---")
    for base_url in ("http://provider.example/v1", "https://provider.example/v1/chat/completions"):
        try:
            provider.validate_provider_config({**config(), "base_url": base_url})
            valid = False
        except provider.ProviderError:
            valid = True
        test("P1: invalid Base URL rejected", valid, base_url)

    path = tmpdir / "runtime-data-private" / "model_provider.json"
    provider.save_provider_config(config(), path)
    status = provider.provider_status(path)
    file_text = path.read_text(encoding="utf-8")
    test("P2: private config stores key only in ignored local file", "sk-test-private-key" in file_text)
    test("P3: provider status redacts API Key", "api_key" not in status and
         "sk-test-private-key" not in json.dumps(status) and status["has_api_key"])

    api_status = handle_model_provider_get(path)
    test("P4: provider API GET redacts API Key", "sk-test-private-key" not in json.dumps(api_status))

    invalid = handle_model_provider_post({**config(), "base_url": "http://bad.example/v1"}, path)
    test("P5: provider API enforces HTTPS", not invalid["ok"] and invalid["error"]["code"] == "INVALID_BASE_URL")


def test_mocked_models_and_chat(tmpdir):
    print("\n--- P6: mocked OpenAI-compatible requests ---")
    path = tmpdir / "model_provider.json"
    provider.save_provider_config(config(), path)
    seen = []
    original = provider.urlopen

    def fake_urlopen(request, timeout):
        seen.append((request, timeout))
        if request.full_url.endswith("/models"):
            return FakeResponse({"data": [{"id": "proposal-model"}]})
        return FakeResponse({
            "choices": [{"message": {"content": "摘要\n建议步骤\n风险与未知\n需要人工确认"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        })

    provider.urlopen = fake_urlopen
    try:
        connection = provider.test_provider_connection(path)
        proposal = provider.create_proposal("请整理本周计划", 0, path)
    finally:
        provider.urlopen = original

    models_request, models_timeout = seen[0]
    chat_request, chat_timeout = seen[1]
    chat_payload = json.loads(chat_request.data.decode("utf-8"))
    test("P6: GET /models uses Bearer authentication", models_request.full_url.endswith("/v1/models") and
         models_request.get_header("Authorization") == "Bearer sk-test-private-key-1234567890" and
         models_timeout == provider.REQUEST_TIMEOUT_SECONDS and connection["model_count"] == 1)
    test("P7: POST /chat/completions has fixed non-streaming limits", chat_request.full_url.endswith("/v1/chat/completions") and
         chat_payload["model"] == "proposal-model" and chat_payload["stream"] is False and
         chat_payload["max_tokens"] == provider.MAX_TOKENS and chat_timeout == provider.REQUEST_TIMEOUT_SECONDS)
    test("P8: proposal output parses usage and price", proposal["usage"]["total_tokens"] == 150 and
         proposal["estimated_cost_usd"] == 0.0006 and proposal["pricing_configured"])
    test("P9: proposal response never includes API Key", "sk-test-private-key" not in json.dumps(proposal))


def test_secret_and_budget_block_before_network(tmpdir):
    print("\n--- P10: security blocks before network ---")
    path = tmpdir / "model_provider.json"
    provider.save_provider_config(config(), path)
    original = provider.urlopen
    calls = []

    def blocked_urlopen(*args, **kwargs):
        calls.append(args)
        raise AssertionError("network must not be called")

    provider.urlopen = blocked_urlopen
    try:
        try:
            provider.create_proposal("token=abcdefghijklmnopqrstuvwxyz", 0, path)
            secret_blocked = False
        except provider.ProviderError as error:
            secret_blocked = error.code == "SECRET_DETECTED"
        try:
            provider.create_proposal("正常请求", 5.0, path)
            budget_blocked = False
        except provider.ProviderError as error:
            budget_blocked = error.code == "BUDGET_EXCEEDED"
    finally:
        provider.urlopen = original

    test("P10: secret-like prompt is rejected locally", secret_blocked and not calls)
    test("P11: reached monthly budget blocks request locally", budget_blocked and not calls)
    test("P12: proposal helper does not create memory or task files", not (tmpdir / "memory").exists() and not (tmpdir / "tasks").exists())


def main():
    with tempfile.TemporaryDirectory(prefix="onepal_model_provider_") as directory:
        tmpdir = Path(directory)
        test_validation_and_redaction(tmpdir)
        test_mocked_models_and_chat(tmpdir)
        test_secret_and_budget_block_before_network(tmpdir)
    total = passed + failed
    print(f"\nResults: {passed}/{total} PASS, {failed}/{total} FAIL")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
