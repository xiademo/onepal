#!/usr/bin/env python3
"""Private configuration and OpenAI-compatible proposal requests for OnePal."""

from __future__ import annotations

import json
import os
import re
import socket
import tempfile
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "runtime-data-private" / "model_provider.json"
MAX_PROMPT_LENGTH = 4000
REQUEST_TIMEOUT_SECONDS = 45
MAX_TOKENS = 1200

SYSTEM_PROMPT = """你是 OnePal 的提案助手。只用中文回答，并严格使用以下四个标题：
摘要
建议步骤
风险与未知
需要人工确认

你不能声称已经执行命令、写入记忆、发送消息、提交申请或启用工具。你的职责是提供可供用户人工审核的建议。"""

SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{10,}",
    r"-----BEGIN",
    r"ghp_[a-zA-Z0-9]{20,}",
    r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}",
    r"(?:api[_-]?key|password|token|secret)\s*[:=]\s*\S{8,}",
]


class ProviderError(Exception):
    """A safe provider error that can be returned to the local dashboard."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def has_secret_like_content(value: str) -> bool:
    text = value or ""
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in SECRET_PATTERNS)


def _optional_nonnegative_number(value, field_name: str):
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ProviderError("INVALID_CONFIG", f"{field_name} 必须是非负数字")
    if number < 0:
        raise ProviderError("INVALID_CONFIG", f"{field_name} 必须是非负数字")
    return number


def validate_provider_config(payload: dict, require_api_key: bool = True) -> dict:
    payload = payload or {}
    base_url = str(payload.get("base_url") or "").strip().rstrip("/")
    model = str(payload.get("model") or "").strip()
    api_key = str(payload.get("api_key") or "").strip()

    try:
        parsed = urlparse(base_url)
    except ValueError:
        parsed = None
    if not parsed or parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
        raise ProviderError("INVALID_BASE_URL", "Base URL 必须是 HTTPS 的 OpenAI 兼容服务地址")
    if parsed.path.rstrip("/").endswith("/chat/completions"):
        raise ProviderError("INVALID_BASE_URL", "Base URL 不能包含 /chat/completions")
    if not model or len(model) > 128:
        raise ProviderError("INVALID_MODEL", "模型名称必须为 1 到 128 个字符")
    if require_api_key and (not api_key or len(api_key) > 2048):
        raise ProviderError("INVALID_API_KEY", "API Key 必填且不得超过 2048 个字符")

    return {
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
        "input_price_per_million": _optional_nonnegative_number(payload.get("input_price_per_million"), "input_price_per_million"),
        "output_price_per_million": _optional_nonnegative_number(payload.get("output_price_per_million"), "output_price_per_million"),
        "monthly_budget_usd": _optional_nonnegative_number(payload.get("monthly_budget_usd"), "monthly_budget_usd"),
    }


def load_provider_config(path: Path = DEFAULT_CONFIG_PATH) -> dict | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ProviderError("INVALID_CONFIG", "无法读取本机私有模型配置")
    return validate_provider_config(data)


def save_provider_config(payload: dict, path: Path = DEFAULT_CONFIG_PATH) -> dict:
    config = validate_provider_config(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="model_provider_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return config


def provider_status(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    try:
        config = load_provider_config(path)
    except ProviderError as exc:
        return {"configured": False, "error": {"code": exc.code, "message": exc.message}}
    if not config:
        return {"configured": False, "has_api_key": False}
    return {
        "configured": True,
        "has_api_key": bool(config.get("api_key")),
        "base_url": config["base_url"],
        "model": config["model"],
        "input_price_per_million": config["input_price_per_million"],
        "output_price_per_million": config["output_price_per_million"],
        "monthly_budget_usd": config["monthly_budget_usd"],
    }


def _request_json(url: str, method: str, api_key: str, body: dict | None = None, timeout: int = REQUEST_TIMEOUT_SECONDS) -> dict:
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = Request(
        url,
        data=encoded,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            **({"Content-Type": "application/json"} if encoded is not None else {}),
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raise ProviderError("PROVIDER_HTTP_ERROR", f"远程模型服务返回 HTTP {exc.code}")
    except URLError:
        raise ProviderError("PROVIDER_UNREACHABLE", "无法连接远程模型服务")
    except (TimeoutError, socket.timeout):
        raise ProviderError("PROVIDER_TIMEOUT", "远程模型服务请求超时")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ProviderError("INVALID_PROVIDER_RESPONSE", "远程模型服务未返回 JSON")


def test_provider_connection(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    config = load_provider_config(path)
    if not config:
        raise ProviderError("NOT_CONFIGURED", "尚未配置远程模型服务")
    data = _request_json(f"{config['base_url']}/models", "GET", config["api_key"])
    models = data.get("data") if isinstance(data, dict) else None
    return {"connected": True, "model_count": len(models) if isinstance(models, list) else None}


def estimate_cost(config: dict, usage: dict) -> float:
    input_price = config.get("input_price_per_million")
    output_price = config.get("output_price_per_million")
    if input_price is None or output_price is None:
        return 0.0
    prompt_tokens = int((usage or {}).get("prompt_tokens") or 0)
    completion_tokens = int((usage or {}).get("completion_tokens") or 0)
    return round((prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000, 8)


def create_proposal(prompt: str, current_month_cost: float, path: Path = DEFAULT_CONFIG_PATH) -> dict:
    prompt = (prompt or "").strip()
    if not prompt:
        raise ProviderError("EMPTY_PROMPT", "请输入需要生成建议的内容")
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise ProviderError("PROMPT_TOO_LONG", f"请求内容不得超过 {MAX_PROMPT_LENGTH} 个字符")
    if has_secret_like_content(prompt):
        raise ProviderError("SECRET_DETECTED", "检测到疑似密钥或密码，内容不会发送到远程模型")

    config = load_provider_config(path)
    if not config:
        raise ProviderError("NOT_CONFIGURED", "尚未配置远程模型服务")
    budget = config.get("monthly_budget_usd")
    if budget is not None and current_month_cost >= budget:
        raise ProviderError("BUDGET_EXCEEDED", "已达到本月模型预算，无法发起新的请求")

    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": MAX_TOKENS,
        "stream": False,
    }
    data = _request_json(f"{config['base_url']}/chat/completions", "POST", config["api_key"], payload)
    try:
        content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        raise ProviderError("INVALID_PROVIDER_RESPONSE", "远程模型响应中没有可用的建议内容")
    if not content:
        raise ProviderError("INVALID_PROVIDER_RESPONSE", "远程模型返回了空建议")

    usage = data.get("usage") if isinstance(data, dict) else {}
    return {
        "request_id": f"assist_{uuid.uuid4().hex[:16]}",
        "proposal_text": content,
        "model": config["model"],
        "usage": {
            "prompt_tokens": int((usage or {}).get("prompt_tokens") or 0),
            "completion_tokens": int((usage or {}).get("completion_tokens") or 0),
            "total_tokens": int((usage or {}).get("total_tokens") or 0),
        },
        "estimated_cost_usd": estimate_cost(config, usage or {}),
        "pricing_configured": config.get("input_price_per_million") is not None and config.get("output_price_per_million") is not None,
    }
